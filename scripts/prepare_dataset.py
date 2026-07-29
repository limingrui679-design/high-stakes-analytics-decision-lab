#!/usr/bin/env python3
"""Apply a reviewed cleaning plan to a copy of uploaded case data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_quality import apply_cleaning_plan


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Apply safe preprocessing and explicitly approved cleaning actions. "
            "The source file is never overwritten."
        )
    )
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--quality-report", type=Path, required=True)
    parser.add_argument("--cleaning-plan", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--approve",
        action="append",
        default=[],
        metavar="ACTION_ID",
        help="Approve one executable requires_confirmation action; repeat as needed.",
    )
    args = parser.parse_args()
    report = json.loads(args.quality_report.read_text(encoding="utf-8"))
    plan = json.loads(args.cleaning_plan.read_text(encoding="utf-8"))
    log = apply_cleaning_plan(
        args.dataset,
        report,
        plan,
        args.output_dir,
        approvals=args.approve,
    )
    print(f"Processed data: {args.output_dir / 'processed/analysis.csv'}")
    print(f"Quality gate before: {log['quality_gate_before']}")
    print(f"Quality gate after: {log['quality_gate_after']}")
    print(f"Transformation log: {args.output_dir / 'transformation-log.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
