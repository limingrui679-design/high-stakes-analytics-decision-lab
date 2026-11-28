"""Fetch public publisher inputs atomically and retain their content identities."""

from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from pathlib import Path
from urllib.parse import urlsplit

CONTACT = "HighStakesAnalyticsResearch/1.0 (https://github.com/limingrui679-design/high-stakes-analytics-decision-lab)"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def obtain(cache: Path, name: str, url: str, expected: str | None = None) -> Path:
    if not url.startswith("https://") or Path(name).name != name:
        raise ValueError("Expected an HTTPS publisher URL and a flat cache filename")
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / name
    receipt = cache / (name + ".origin.json")
    if path.is_file() and receipt.is_file():
        previous = json.loads(receipt.read_text())
        if previous["url"] != url and not expected:
            raise ValueError(f"Cache collision for {name}")
        if sha256(path) != (expected or previous["sha256"]):
            raise ValueError(f"Cached bytes changed for {name}")
        return path
    partial = cache / (name + "." + uuid.uuid4().hex + ".part")
    try:
        subprocess.run(
            [
                "curl",
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--retry",
                "2",
                "--connect-timeout",
                "15",
                "--speed-time",
                "55",
                "--speed-limit",
                "64",
                "--user-agent",
                CONTACT,
                "--output",
                str(partial),
                url,
            ],
            check=True,
        )
        with partial.open("rb") as source:
            head = source.read(256)
        if not head or (name.lower().endswith(".zip") and not head.startswith(b"PK")):
            raise ValueError(f"Unexpected payload for {name} from {urlsplit(url).netloc}")
        if name.endswith(".XPT") and not head.startswith(b"HEADER"):
            raise ValueError(f"Not a SAS transport file: {name}")
        if name.endswith(".pdf") and not head.startswith(b"%PDF"):
            raise ValueError(f"Not a PDF: {name}")
        if name.endswith(".csv") and head.lstrip().startswith(b"<"):
            raise ValueError(f"Unexpected HTML response for {name}")
        digest = sha256(partial)
        if expected and digest != expected:
            raise ValueError(f"Publisher bytes differ from the pinned release for {name}")
        partial.replace(path)
        temp_receipt = receipt.with_suffix("." + uuid.uuid4().hex + ".tmp")
        temp_receipt.write_text(
            json.dumps(
                {
                    "name": name,
                    "url": url,
                    "bytes": path.stat().st_size,
                    "hash_algorithm": "sha256",
                    "sha256": digest,
                },
                indent=2,
            )
            + "\n"
        )
        temp_receipt.replace(receipt)
        return path
    finally:
        partial.unlink(missing_ok=True)
