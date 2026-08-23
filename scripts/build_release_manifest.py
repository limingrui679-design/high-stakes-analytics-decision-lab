#!/usr/bin/env python3
"""Build the hash allowlist used to verify source archives without Git metadata."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "RELEASE-MANIFEST.json"
RELEASE_VERSION = "1.1.2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_manifest(root: Path = ROOT) -> dict[str, object]:
    content_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    result = subprocess.run(
        ["git", "ls-files", "-s", "-z"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )
    entries = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode = metadata.split(b" ", 1)[0].decode("ascii")
        relative_text = encoded_path.decode("utf-8")
        if relative_text == OUTPUT.name:
            continue
        relative = Path(relative_text)
        source = root / relative
        if source.is_symlink():
            raise ValueError(f"Release manifests do not support symlinks: {relative}")
        entries.append(
            {
                "path": relative.as_posix(),
                "mode": mode,
                "sha256": _sha256(source),
            }
        )
    entries.sort(key=lambda item: str(item["path"]))
    return {
        "schema_version": "1.1",
        "release": RELEASE_VERSION,
        "release_tag": f"v{RELEASE_VERSION}",
        "content_commit": content_commit,
        "algorithm": "sha256",
        "scope": "Every tracked release file except RELEASE-MANIFEST.json itself.",
        "archive_build_method": (
            "git archive --format=zip "
            f"--prefix=high-stakes-analytics-decision-lab/ v{RELEASE_VERSION}"
        ),
        "release_commit_binding": (
            f"The annotated v{RELEASE_VERSION} tag binds this self-excluding manifest and its "
            "content commit to the final release commit."
        ),
        "files": entries,
    }


def main() -> int:
    payload = build_manifest()
    OUTPUT.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    files = payload["files"]
    if not isinstance(files, list):
        raise TypeError("Release manifest files must be a list.")
    print(json.dumps({"path": str(OUTPUT), "files": len(files)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
