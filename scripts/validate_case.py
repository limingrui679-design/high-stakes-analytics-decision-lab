#!/usr/bin/env python3
"""Validate a High-Stakes Analytics & Decision Lab case file."""

from __future__ import annotations

import argparse
from pathlib import Path

from decision_engine import load_case, validate_case


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a decision case JSON file.")
    parser.add_argument("case", type=Path, help="Path to the case JSON file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        case = load_case(args.case)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2
    result = validate_case(case)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")
    if result.valid:
        print("VALID")
        return 0
    print(f"INVALID: {len(result.errors)} error(s)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
