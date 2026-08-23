#!/usr/bin/env python3
"""Reject high-confidence credential artifacts without echoing suspected values."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
RELEASE_MANIFEST = "RELEASE-MANIFEST.json"

SECRET_FILENAME_PATTERNS = (
    re.compile(r"(?:^|/)\.env(?:\.[^/]+)?$", re.IGNORECASE),
    re.compile(r"(?:^|/)id_(?:rsa|dsa|ecdsa|ed25519)$", re.IGNORECASE),
    re.compile(r"(?:^|/)[^/]+\.(?:key|pem|p12|pfx)$", re.IGNORECASE),
    re.compile(r"(?:^|/)(?:credentials?|secrets?)(?:\.[^/]*)?$", re.IGNORECASE),
)

CONTENT_RULES: tuple[tuple[str, tuple[bytes, ...], re.Pattern[bytes]], ...] = (
    (
        "private-key-header",
        (b"PRIVATE KEY",),
        re.compile(br"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ),
    (
        "aws-access-key",
        (b"AKIA", b"ASIA"),
        re.compile(br"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])"),
    ),
    (
        "github-token",
        (b"ghp_", b"gho_", b"ghu_", b"ghs_", b"ghr_"),
        re.compile(br"(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9_]{20,255}(?![A-Za-z0-9_])"),
    ),
    (
        "openai-api-key",
        (b"sk-",),
        re.compile(br"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,255}(?![A-Za-z0-9_-])"),
    ),
    (
        "slack-token",
        (b"xoxb-", b"xoxa-", b"xoxp-", b"xoxr-", b"xoxs-"),
        re.compile(br"(?<![A-Za-z0-9-])xox[baprs]-[A-Za-z0-9-]{20,255}(?![A-Za-z0-9-])"),
    ),
    (
        "google-api-key",
        (b"AIza",),
        re.compile(br"(?<![A-Za-z0-9_-])AIza[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])"),
    ),
    (
        "stripe-live-key",
        (b"sk_live_", b"rk_live_"),
        re.compile(br"(?<![A-Za-z0-9_])(?:sk|rk)_live_[A-Za-z0-9]{16,255}(?![A-Za-z0-9])"),
    ),
)


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    line: int | None = None


def tracked_paths(root: Path = ROOT) -> list[Path]:
    """Return Git-tracked files, falling back to a verified release manifest."""

    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        result = None
    if result is not None and result.returncode == 0:
        return [root / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]

    manifest_path = root / RELEASE_MANIFEST
    if not manifest_path.is_file():
        raise FileNotFoundError("Git metadata and RELEASE-MANIFEST.json are both unavailable.")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = payload.get("files")
    if not isinstance(entries, list):
        raise ValueError("Release manifest must contain a files list.")
    paths: list[Path] = [manifest_path]
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("Release manifest contains an invalid file entry.")
        path = root / entry["path"]
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(f"Release-manifest file is unavailable: {entry['path']}")
        paths.append(path)
    return paths


def scan_paths(root: Path, paths: Sequence[Path]) -> list[Finding]:
    """Scan path names and non-binary contents using narrow high-confidence rules."""

    findings: list[Finding] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if any(pattern.search(relative) for pattern in SECRET_FILENAME_PATTERNS):
            findings.append(Finding(path=relative, rule="secret-shaped-filename"))
        try:
            content = path.read_bytes()
        except OSError as error:
            raise OSError(f"Could not scan tracked path {relative}: {error}") from error
        if b"\0" in content[:8192]:
            continue
        for rule, markers, pattern in CONTENT_RULES:
            if not any(marker in content for marker in markers):
                continue
            match = pattern.search(content)
            if match is not None:
                line_number = content.count(b"\n", 0, match.start()) + 1
                findings.append(Finding(path=relative, rule=rule, line=line_number))
    return findings


def format_findings(findings: Sequence[Finding]) -> str:
    """Render metadata only; never return the matching source text or value."""

    lines = [
        "Tracked-secret scan failed. Suspected values are intentionally not printed."
    ]
    for finding in findings:
        location = f":{finding.line}" if finding.line is not None else ""
        lines.append(f"- {finding.path}{location} [{finding.rule}]")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan Git-tracked or release-manifest files for high-confidence credentials."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()
    paths = tracked_paths(root)
    findings = scan_paths(root, paths)
    if findings:
        print(format_findings(findings), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "scope": "tracked-or-release-manifest-files",
                "files_scanned": len(paths),
                "findings": 0,
                "values_printed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
