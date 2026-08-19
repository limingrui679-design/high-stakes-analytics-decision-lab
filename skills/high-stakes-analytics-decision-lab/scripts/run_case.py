#!/usr/bin/env python3
"""Run a High-Stakes Analytics & Decision Lab case and write report artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from decision_engine import analyze_case, case_hash, load_case, write_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze alternatives under uncertainty and produce a traceable brief."
    )
    parser.add_argument("case", type=Path, help="Path to a decision case JSON file.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for decision-results.json and decision-report.md.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=10_000,
        help="Monte Carlo sample count (default: 10000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260726,
        help="Random seed (default: 20260726).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    case = load_case(args.case)
    result = analyze_case(
        case,
        samples=args.samples,
        seed=args.seed,
        source_hash=case_hash(args.case),
    )
    result_path, report_path = write_outputs(case, result, args.output_dir)
    recommendation_id = result["decision"]["recommendation"]
    if recommendation_id:
        recommendation = result["alternatives"][recommendation_id]["label"]
        print(f"Recommendation: {recommendation}")
    else:
        print("Recommendation: no decision-ready alternative")
    print(f"Results: {result_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
