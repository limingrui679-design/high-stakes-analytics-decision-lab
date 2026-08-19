#!/usr/bin/env python3
"""Run a dependency-free readiness audit for the repository or installed Skill."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

SKILL_NAME = "high-stakes-analytics-decision-lab"
SCRIPT_DIR = Path(__file__).resolve().parent
LAYOUT_ROOT = SCRIPT_DIR.parent
REPOSITORY_SKILL = LAYOUT_ROOT / "skills" / SKILL_NAME
MAX_BUNDLE_BYTES = 2 * 1024 * 1024
MAX_BUNDLE_FILES = 64

RUNTIME_SCRIPTS = (
    "allocation_optimizer.py",
    "analytics_router.py",
    "data_quality.py",
    "decision_engine.py",
    "evidence_analysis.py",
    "hsadl.py",
    "init_case.py",
    "prediction_validation.py",
    "prepare_dataset.py",
    "profile_dataset.py",
    "quickstart_demo.py",
    "report_visuals.py",
    "route_question.py",
    "run_case.py",
    "validate_case.py",
    "visual_system.py",
)


def _layout() -> tuple[str, Path]:
    if (LAYOUT_ROOT / "SKILL.md").is_file():
        return "installed_skill", LAYOUT_ROOT
    if (REPOSITORY_SKILL / "SKILL.md").is_file():
        return "repository_checkout", REPOSITORY_SKILL
    return "unknown", LAYOUT_ROOT


def _directory_metrics(root: Path) -> tuple[int, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def audit() -> dict[str, Any]:
    layout, skill_root = _layout()
    checks: list[dict[str, Any]] = []

    def record(name: str, passed: bool, detail: str, *, required: bool = True) -> None:
        checks.append(
            {
                "name": name,
                "status": "pass" if passed else "fail" if required else "warn",
                "required": required,
                "detail": detail,
            }
        )

    version = ".".join(str(item) for item in sys.version_info[:3])
    record(
        "python",
        sys.version_info >= (3, 11),
        f"Python {version}; 3.11 or newer is required.",
    )
    record(
        "skill-layout",
        layout != "unknown",
        f"Detected {layout.replace('_', ' ')} at {skill_root}.",
    )
    missing_scripts = [name for name in RUNTIME_SCRIPTS if not (SCRIPT_DIR / name).is_file()]
    record(
        "runtime-files",
        not missing_scripts,
        "All required runtime scripts are present."
        if not missing_scripts
        else "Missing: " + ", ".join(missing_scripts),
    )
    required_skill_files = (
        skill_root / "SKILL.md",
        skill_root / "assets" / "case-template.json",
        skill_root / "assets" / "data-contract-template.json",
        skill_root / "references" / "reporting-standard.md",
        skill_root / "references" / "data-quality-gate.md",
    )
    missing_skill_files = [str(path) for path in required_skill_files if not path.is_file()]
    record(
        "skill-contract",
        not missing_skill_files,
        "Skill contract, templates, and core references are present."
        if not missing_skill_files
        else "Missing: " + ", ".join(missing_skill_files),
    )

    try:
        with tempfile.TemporaryDirectory(prefix="hsadl-doctor-") as temporary:
            probe = Path(temporary) / "probe.txt"
            probe.write_text("ok\n", encoding="utf-8")
            writable = probe.read_text(encoding="utf-8") == "ok\n"
    except OSError as error:
        writable = False
        write_detail = f"Temporary output failed: {error}"
    else:
        write_detail = "Temporary output can be created and read back."
    record("writable-output", writable, write_detail)

    file_count, byte_count = _directory_metrics(skill_root)
    record(
        "skill-footprint",
        file_count <= MAX_BUNDLE_FILES and byte_count <= MAX_BUNDLE_BYTES,
        f"{file_count} files, {byte_count / 1024:.1f} KiB; limits are "
        f"{MAX_BUNDLE_FILES} files and {MAX_BUNDLE_BYTES / 1024:.0f} KiB.",
    )
    git_path = shutil.which("git")
    record(
        "git",
        git_path is not None,
        f"Git available at {git_path}." if git_path else "Git not found; release checks are unavailable.",
        required=False,
    )
    required_failures = [
        item for item in checks if item["required"] and item["status"] != "pass"
    ]
    return {
        "schema_version": "1.0",
        "skill": SKILL_NAME,
        "layout": layout,
        "skill_root": str(skill_root),
        "platform": os.name,
        "ready": not required_failures,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()
    result = audit()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("High-Stakes Analytics & Decision Lab · doctor")
        for item in result["checks"]:
            marker = {"pass": "PASS", "fail": "FAIL", "warn": "WARN"}[item["status"]]
            print(f"[{marker}] {item['name']}: {item['detail']}")
        print("READY" if result["ready"] else "NOT READY")
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
