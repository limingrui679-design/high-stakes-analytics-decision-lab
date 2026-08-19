#!/usr/bin/env python3
"""Profile uploaded case data and write a data-readiness bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from data_quality import load_contract, write_quality_bundle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Profile CSV, TSV, JSON, or JSONL data before analysis."
    )
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    contract = load_contract(args.contract, dataset_name=args.dataset.stem)
    profile, plan = write_quality_bundle(
        args.dataset,
        args.output_dir,
        contract=contract,
    )
    print(f"Quality gate: {profile['quality_gate']['status']}")
    print(f"Findings: {len(profile['findings'])}")
    print(f"Safe automatic actions: {sum(a['mode'] == 'safe_auto' for a in plan['actions'])}")
    print(
        "Actions requiring confirmation: "
        f"{sum(a['mode'] == 'requires_confirmation' for a in plan['actions'])}"
    )
    print(f"Report: {args.output_dir / 'data-quality-report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
