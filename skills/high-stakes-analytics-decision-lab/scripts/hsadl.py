#!/usr/bin/env python3
"""Single entry point for High-Stakes Analytics & Decision Lab commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
COMMANDS = {
    "doctor": ("doctor.py", "Check Python, files, write access, and Skill footprint."),
    "demo": ("quickstart_demo.py", "Build a safe 60-second readiness demo."),
    "start": ("init_case.py", "Create a guarded workspace from one dataset and question."),
    "route": ("route_question.py", "Route a question without inventing empirical results."),
    "profile": ("profile_dataset.py", "Run the data-readiness gate."),
    "prepare": ("prepare_dataset.py", "Apply only reviewed cleaning actions."),
    "evidence": ("evidence_analysis.py", "Run a supported evidence module."),
    "predict": ("prediction_validation.py", "Validate supplied held-out predictions."),
    "allocate": ("allocation_optimizer.py", "Solve a bounded discrete allocation case."),
    "validate": ("validate_case.py", "Validate a decision-case contract."),
    "run": ("run_case.py", "Run a validated decision case."),
}


def _help() -> str:
    rows = [
        "High-Stakes Analytics & Decision Lab",
        "",
        "Usage: python3 scripts/hsadl.py <command> [arguments]",
        "",
        "Commands:",
    ]
    width = max(len(name) for name in COMMANDS)
    rows.extend(
        f"  {name.ljust(width)}  {description}"
        for name, (_, description) in COMMANDS.items()
    )
    rows.extend(
        [
            "",
            "Start here:",
            "  python3 scripts/hsadl.py doctor",
            "  python3 scripts/hsadl.py demo --output-dir build/demo",
            "  python3 scripts/hsadl.py start data.csv --question \"What changed?\" --output-dir case",
            "",
            "Run '<command> --help' for command-specific options.",
        ]
    )
    return "\n".join(rows)


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help", "help"}:
        print(_help())
        return 0
    command = sys.argv[1]
    if command not in COMMANDS:
        print(f"hsadl: unknown command: {command}\n", file=sys.stderr)
        print(_help(), file=sys.stderr)
        return 2
    script_name = COMMANDS[command][0]
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name), *sys.argv[2:]],
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
