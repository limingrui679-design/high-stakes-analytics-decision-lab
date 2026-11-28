"""Replay a published-data extraction or freeze its evidence for a new study."""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

from source_cache import obtain, sha256

PROJECTS = Path(__file__).resolve().parents[1] / "projects"


def module(path):
    spec = importlib.util.spec_from_file_location("publisher_extraction", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


class Sources:
    """Record only publisher objects actually opened for a particular snapshot."""

    def __init__(self, cache):
        self.cache = cache
        self.used = {}

    def get(self, name):
        receipt = json.loads((self.cache / (name + ".origin.json")).read_text())
        if name not in self.used:
            if sha256(self.cache / name) != receipt["sha256"]:
                raise ValueError(f"Source digest changed: {name}")
            self.used[name] = receipt
        return self.cache / name

    def names(self, pattern):
        return sorted(
            p.name
            for p in self.cache.glob(pattern)
            if (self.cache / (p.name + ".origin.json")).is_file()
        )


def process(project, cache, freeze, fetch):
    config = json.loads((project / "study-design.json").read_text())
    target = project / "data/raw/observations.csv.gz"
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = project / "source-manifest.json"
    if freeze and fetch:
        raise ValueError(
            "Fetch uses a committed manifest; freezing adopts explicitly supplied source receipts"
        )
    if not freeze:
        if not manifest_path.is_file():
            raise FileNotFoundError(f"No input lock for {project.name}")
        manifest = json.loads(manifest_path.read_text())
        if fetch:
            for record in manifest["sources"]:
                for item in record["artifacts"]:
                    obtain(cache, item["name"], item["url"], item["sha256"])
    data = Sources(cache)
    extractor = module(project / "extract.py")
    fields = list(config["fields"])
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp)
        plain = scratch / "observations.csv"
        with plain.open("w", newline="", encoding="utf-8") as out:
            writer = csv.writer(out, lineterminator="\n")
            writer.writerow(fields)
            count = 0
            for row in extractor.rows(data):
                if len(row) != len(fields):
                    raise ValueError(
                        f"Publisher extraction has {len(row)} columns, expected {len(fields)}"
                    )
                writer.writerow(row)
                count += 1
        if not count or not data.used:
            raise ValueError("Empty extraction or missing upstream identities")
        if not freeze:
            expected = {
                a["name"]: (a["sha256"], a["url"])
                for s in manifest["sources"]
                for a in s["artifacts"]
            }
            actual = {name: (a["sha256"], a["url"]) for name, a in data.used.items()}
            if actual != expected:
                raise ValueError("The publisher input set changed")
            with gzip.open(target, "rb") as bundled, plain.open("rb") as actual:
                while True:
                    chunk = actual.read(1048576)
                    if chunk != bundled.read(1048576):
                        raise ValueError(f"Upstream reproduction differs: {project.name}")
                    if not chunk:
                        break
            print(
                f"{project.name}: verified {count:,} rows against {len(data.used)} publisher objects"
            )
            return
        packed = scratch / "snapshot.gz"
        with (
            packed.open("wb") as raw,
            gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream,
            plain.open("rb") as input_file,
        ):
            shutil.copyfileobj(input_file, stream)
        sources = []
        assigned = set()
        for group in config["sources"]:
            artifacts = [
                data.used[n]
                for n in sorted(data.used)
                if any(n.startswith(prefix) for prefix in group["prefixes"])
            ]
            if not artifacts:
                raise ValueError(f"Missing upstream objects for {group['source_id']}")
            if assigned.intersection(a["name"] for a in artifacts):
                raise ValueError("Upstream groups overlap")
            assigned.update(a["name"] for a in artifacts)
            sources.append(
                {k: v for k, v in group.items() if k != "prefixes"} | {"artifacts": artifacts}
            )
        if assigned != set(data.used):
            raise ValueError(f"Unmapped source files: {set(data.used) - assigned}")
        shutil.copy2(packed, target)
        first = sources[0]
        write_json(
            manifest_path,
            dict(
                schema_version="1.1",
                project_id=project.name,
                source_id=first["source_id"],
                title=config["dataset"],
                publisher=config["publisher"],
                landing_page=config["landing_page"],
                version=config["version"],
                accessed_at=config["accessed_at"],
                license=first["license"],
                redistribution=config["redistribution"],
                grain=config["grain"],
                expected_rows=count,
                sources=sources,
                raw_files=[
                    dict(
                        path="data/raw/observations.csv.gz",
                        sha256=sha256(packed),
                        bytes=packed.stat().st_size,
                        uncompressed_sha256=sha256(plain),
                    )
                ],
            ),
        )
        print(f"{project.name}: {count:,} rows from {len(assigned)} locked objects", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument(
        "--project",
        required=True,
        choices=sorted(p.parent.name for p in PROJECTS.glob("*/extract.py")),
    )
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="Maintainers: adopt a new reviewed snapshot and input hashes",
    )
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    process(PROJECTS / args.project, args.cache, args.freeze, args.fetch)
