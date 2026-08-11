#!/usr/bin/env python3
"""Rebuild the public portfolio and verify cross-version semantic equivalence.

Raw sources, labels, categorical values, integer counts, and ordinary text must
match exactly. Floating-point outputs may differ only within the documented
cross-version tolerance. Hashes of regenerated analytical artifacts may change
when an interpreter serializes an equivalent float differently; source,
manifest, and configuration hashes are never exempted.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MINIMUM_PYTHON = (3, 11)

ABSOLUTE_TOLERANCE = 2e-8
RELATIVE_TOLERANCE = 1e-12
DERIVED_ARTIFACT_HASH_KEYS = {
    "analytical_results_sha256",
    "case_hash_sha256",
}
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REPORT_HASH_PATTERN = re.compile(
    r"(?im)(?P<prefix>(?:Result|Analytical result|Case) SHA-256:\s*`)[0-9a-f]{64}(?P<suffix>`)",
)
TOOL_CACHE_DIRECTORIES = {"__pycache__", ".pytest_cache"}
IGNORED_PARTS = {".git", *TOOL_CACHE_DIRECTORIES}
RELEASE_MANIFEST = Path("RELEASE-MANIFEST.json")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_ignorable_tool_cache_file(path: Path, relative: Path) -> bool:
    """Identify non-symlink cache files that are never copied into a rebuild."""
    if path.is_symlink():
        return False
    parent_parts = set(relative.parts[:-1])
    if ".pytest_cache" in parent_parts:
        return True
    if "__pycache__" in parent_parts:
        return relative.suffix == ".pyc"
    return False


def _manifest_files(root: Path) -> list[Path]:
    manifest_path = root / RELEASE_MANIFEST
    if not manifest_path.is_file():
        raise RuntimeError(
            "Repository metadata is unavailable and RELEASE-MANIFEST.json is missing."
        )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.1" or payload.get("algorithm") != "sha256":
        raise ValueError("Unsupported release-manifest schema or digest algorithm.")
    entries = payload.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Release manifest must contain a non-empty files list.")
    paths: list[Path] = []
    canonical_paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Release-manifest file entries must be objects.")
        raw_path = entry.get("path")
        expected_mode = entry.get("mode")
        expected_hash = entry.get("sha256")
        if (
            not isinstance(raw_path, str)
            or not isinstance(expected_mode, str)
            or not isinstance(expected_hash, str)
        ):
            raise ValueError("Release-manifest paths, modes, and hashes must be strings.")
        pure_path = PurePosixPath(raw_path)
        if (
            not raw_path
            or "\x00" in raw_path
            or "\\" in raw_path
            or pure_path.is_absolute()
            or ".." in pure_path.parts
            or pure_path.as_posix() != raw_path
            or pure_path == RELEASE_MANIFEST
        ):
            raise ValueError(f"Unsafe release-manifest path: {raw_path!r}")
        canonical = raw_path.casefold()
        if canonical in canonical_paths:
            raise ValueError(f"Duplicate release-manifest path: {raw_path!r}")
        canonical_paths.add(canonical)
        if HASH_PATTERN.fullmatch(expected_hash) is None:
            raise ValueError(f"Invalid release-manifest hash for {raw_path!r}.")
        if expected_mode not in {"100644", "100755"}:
            raise ValueError(f"Unsupported release-manifest mode for {raw_path!r}.")
        relative = Path(*pure_path.parts)
        source = root / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError(
                f"Release-manifest file is missing or unsupported: {raw_path}"
            )
        observed_hash = _sha256_file(source)
        if observed_hash != expected_hash:
            raise ValueError(
                f"Release-manifest hash mismatch for {raw_path}: "
                f"expected {expected_hash}, observed {observed_hash}"
            )
        if os.name == "posix":
            observed_mode = "100755" if source.stat().st_mode & 0o111 else "100644"
            if observed_mode != expected_mode:
                raise ValueError(
                    f"Release-manifest mode mismatch for {raw_path}: "
                    f"expected {expected_mode}, observed {observed_mode}"
                )
        paths.append(relative)
    expected_paths = {RELEASE_MANIFEST, *paths}
    observed_paths: set[Path] = set()
    for path in root.rglob("*"):
        if not path.is_file() and not path.is_symlink():
            continue
        relative = path.relative_to(root)
        if _is_ignorable_tool_cache_file(path, relative):
            continue
        observed_paths.add(relative)
    unlisted = sorted(observed_paths - expected_paths)
    if unlisted:
        preview = ", ".join(path.as_posix() for path in unlisted[:20])
        remainder = len(unlisted) - min(len(unlisted), 20)
        suffix = f" (+{remainder} more)" if remainder else ""
        raise ValueError(
            f"Release source tree contains unlisted files: {preview}{suffix}"
        )
    return [RELEASE_MANIFEST, *sorted(paths)]


def _tracked_files(root: Path) -> list[Path]:
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return [
                Path(item.decode("utf-8"))
                for item in result.stdout.split(b"\0")
                if item
            ]
    return _manifest_files(root)


def _copy_tracked_repository(source: Path, destination: Path, tracked: list[Path]) -> None:
    for relative in tracked:
        source_path = source / relative
        destination_path = destination / relative
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.is_symlink():
            destination_path.symlink_to(os.readlink(source_path))
        else:
            shutil.copy2(source_path, destination_path)


def _run(command: list[str], *, cwd: Path) -> None:
    environment = os.environ.copy()
    environment.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"})
    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode:
        rendered = " ".join(command)
        raise RuntimeError(f"Rebuild command failed ({rendered}):\n{result.stdout}")


def _rebuild(root: Path) -> int:
    python = sys.executable
    _run([python, "scripts/configure_tailored_portfolio.py"], cwd=root)
    project_root = root / "examples" / "real-data-cases" / "projects"
    projects = sorted(
        path
        for path in project_root.iterdir()
        if path.is_dir() and path.name != "_shared"
    )
    if len(projects) != 15:
        raise RuntimeError(f"Expected 15 public projects; found {len(projects)}.")
    for project in projects:
        print(f"Rebuilding {project.name}...", flush=True)
        for entrypoint in ("prepare_data.py", "analyze.py", "build_decision_case.py"):
            _run([python, str(project.relative_to(root) / entrypoint)], cwd=root)
    for script in (
        "scripts/build_readme_visuals.py",
        "scripts/build_terminal_decision_reports.py",
        "scripts/build_case_examples.py",
    ):
        _run([python, script], cwd=root)
    return len(projects)


def _semantic_json_differences(
    expected: Any,
    observed: Any,
    *,
    path: str = "$",
) -> tuple[list[str], int]:
    failures: list[str] = []
    normalized_hashes = 0
    if isinstance(expected, bool) or isinstance(observed, bool):
        if expected is not observed:
            failures.append(f"{path}: expected {expected!r}, observed {observed!r}")
        return failures, normalized_hashes
    if isinstance(expected, int) and isinstance(observed, int):
        if expected != observed:
            failures.append(f"{path}: expected integer {expected}, observed {observed}")
        return failures, normalized_hashes
    if isinstance(expected, int) or isinstance(observed, int):
        failures.append(
            f"{path}: integer type changed; expected {expected!r}, observed {observed!r}"
        )
        return failures, normalized_hashes
    if isinstance(expected, (int, float)) and isinstance(observed, (int, float)):
        left_number = float(expected)
        right_number = float(observed)
        if not (
            math.isfinite(left_number)
            and math.isfinite(right_number)
            and math.isclose(
                left_number,
                right_number,
                rel_tol=RELATIVE_TOLERANCE,
                abs_tol=ABSOLUTE_TOLERANCE,
            )
        ):
            failures.append(f"{path}: expected {expected!r}, observed {observed!r}")
        return failures, normalized_hashes
    if type(expected) is not type(observed):
        failures.append(
            f"{path}: expected type {type(expected).__name__}, "
            f"observed {type(observed).__name__}"
        )
        return failures, normalized_hashes
    if isinstance(expected, dict):
        expected_keys = set(expected)
        observed_keys = set(observed)
        if expected_keys != observed_keys:
            failures.append(
                f"{path}: key mismatch; missing={sorted(expected_keys - observed_keys)}, "
                f"added={sorted(observed_keys - expected_keys)}"
            )
            return failures, normalized_hashes
        for key in expected:
            left = expected[key]
            right = observed[key]
            if (
                key in DERIVED_ARTIFACT_HASH_KEYS
                and isinstance(left, str)
                and isinstance(right, str)
                and HASH_PATTERN.fullmatch(left)
                and HASH_PATTERN.fullmatch(right)
            ):
                normalized_hashes += int(left != right)
                continue
            child_failures, child_hashes = _semantic_json_differences(
                left,
                right,
                path=f"{path}.{key}",
            )
            failures.extend(child_failures)
            normalized_hashes += child_hashes
        return failures, normalized_hashes
    if isinstance(expected, list):
        if len(expected) != len(observed):
            failures.append(
                f"{path}: expected list length {len(expected)}, observed {len(observed)}"
            )
            return failures, normalized_hashes
        for index, (left, right) in enumerate(zip(expected, observed, strict=True)):
            child_failures, child_hashes = _semantic_json_differences(
                left,
                right,
                path=f"{path}[{index}]",
            )
            failures.extend(child_failures)
            normalized_hashes += child_hashes
        return failures, normalized_hashes
    if expected != observed:
        failures.append(f"{path}: expected {expected!r}, observed {observed!r}")
    return failures, normalized_hashes


def _semantic_csv_differences(expected: Path, observed: Path) -> list[str]:
    with expected.open("r", encoding="utf-8-sig", newline="") as handle:
        expected_rows = list(csv.reader(handle))
    with observed.open("r", encoding="utf-8-sig", newline="") as handle:
        observed_rows = list(csv.reader(handle))
    if len(expected_rows) != len(observed_rows):
        return [
            f"row count: expected {len(expected_rows)}, observed {len(observed_rows)}"
        ]
    failures: list[str] = []
    for row_index, (left_row, right_row) in enumerate(
        zip(expected_rows, observed_rows, strict=True),
        start=1,
    ):
        if len(left_row) != len(right_row):
            failures.append(
                f"row {row_index}: expected {len(left_row)} columns, "
                f"observed {len(right_row)}"
            )
            continue
        for column_index, (left, right) in enumerate(
            zip(left_row, right_row, strict=True),
            start=1,
        ):
            if left == right:
                continue
            try:
                left_number = float(left)
                right_number = float(right)
            except ValueError:
                failures.append(
                    f"row {row_index}, column {column_index}: "
                    f"expected {left!r}, observed {right!r}"
                )
                continue
            if not (
                math.isfinite(left_number)
                and math.isfinite(right_number)
                and math.isclose(
                    left_number,
                    right_number,
                    rel_tol=RELATIVE_TOLERANCE,
                    abs_tol=ABSOLUTE_TOLERANCE,
                )
            ):
                failures.append(
                    f"row {row_index}, column {column_index}: "
                    f"expected {left!r}, observed {right!r}"
                )
    return failures


def _normalize_report_hashes(value: str) -> str:
    return REPORT_HASH_PATTERN.sub(
        lambda match: match.group("prefix") + "<regenerated-artifact>" + match.group("suffix"),
        value,
    )


def _compare_file(expected: Path, observed: Path) -> tuple[list[str], int]:
    if expected.read_bytes() == observed.read_bytes():
        return [], 0
    if expected.suffix == ".json":
        return _semantic_json_differences(
            json.loads(expected.read_text(encoding="utf-8")),
            json.loads(observed.read_text(encoding="utf-8")),
        )
    if expected.suffix == ".csv":
        return _semantic_csv_differences(expected, observed), 0
    if expected.suffix == ".md":
        left = _normalize_report_hashes(expected.read_text(encoding="utf-8"))
        right = _normalize_report_hashes(observed.read_text(encoding="utf-8"))
        return ([] if left == right else ["text changed beyond generated hash receipts"]), 0
    return ["byte content changed"], 0


def verify(root: Path = ROOT) -> dict[str, int | float]:
    tracked = _tracked_files(root)
    exact_files = 0
    semantic_files = 0
    normalized_hashes = 0
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="hsdl-reproducibility-") as directory:
        scratch = Path(directory) / "repository"
        _copy_tracked_repository(root, scratch, tracked)
        project_count = _rebuild(scratch)
        print("Comparing regenerated artifacts...", flush=True)
        for relative in tracked:
            expected = root / relative
            observed = scratch / relative
            if not observed.exists():
                failures.append(f"{relative}: tracked file disappeared")
                continue
            if expected.read_bytes() == observed.read_bytes():
                exact_files += 1
                continue
            file_failures, file_hashes = _compare_file(expected, observed)
            if file_failures:
                failures.extend(f"{relative}: {failure}" for failure in file_failures[:20])
            else:
                semantic_files += 1
                normalized_hashes += file_hashes
        tracked_set = set(tracked)
        for path in scratch.rglob("*"):
            if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
                continue
            if path.suffix in {".pyc", ".pyo"}:
                continue
            relative = path.relative_to(scratch)
            if relative not in tracked_set:
                failures.append(f"{relative}: unexpected generated file")
    if failures:
        preview = "\n".join(f"- {failure}" for failure in failures[:100])
        remainder = len(failures) - min(len(failures), 100)
        suffix = f"\n- ... {remainder} additional failures" if remainder else ""
        raise AssertionError(f"Portfolio reproducibility check failed:\n{preview}{suffix}")
    return {
        "projects": project_count,
        "tracked_files": len(tracked),
        "byte_identical_files": exact_files,
        "semantically_equivalent_files": semantic_files,
        "normalized_derived_hashes": normalized_hashes,
        "absolute_tolerance": ABSOLUTE_TOLERANCE,
        "relative_tolerance": RELATIVE_TOLERANCE,
    }


def main() -> int:
    if sys.version_info < MINIMUM_PYTHON:
        required = ".".join(str(value) for value in MINIMUM_PYTHON)
        observed = ".".join(str(value) for value in sys.version_info[:3])
        raise SystemExit(
            f"Python {required} or newer is required; current interpreter is {observed}."
        )
    summary = verify()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
