#!/usr/bin/env python3
"""Migrate a decision case from schema 1.2 to explicit-uncertainty schema 1.3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def migrate(case: dict[str, Any]) -> tuple[dict[str, Any], int]:
    version = case.get("schema_version")
    if version not in {"1.2", "1.3"}:
        raise ValueError("Input schema_version must be 1.2 or 1.3.")
    migrated = json.loads(json.dumps(case))
    added = 0
    for alternative in migrated.get("alternatives", []):
        for specification in alternative.get("metrics", {}).values():
            if "uncertainty_type" in specification:
                continue
            specification["uncertainty_type"] = (
                "none"
                if specification.get("distribution") == "fixed"
                else "parameter"
            )
            added += 1
    migrated["schema_version"] = "1.3"
    notes = migrated.setdefault("decision_notes", [])
    note = (
        "Schema 1.3 migration classified non-fixed legacy distributions as "
        "parameter uncertainty. Review each classification before decision use."
    )
    if added and note not in notes:
        notes.append(note)
    return migrated, added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument("--output", type=Path)
    output.add_argument("--in-place", action="store_true")
    args = parser.parse_args()

    case = json.loads(args.input.read_text(encoding="utf-8"))
    migrated, added = migrate(case)
    target = args.input if args.in_place else args.output
    assert target is not None
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(migrated, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote schema 1.3 case to {target}; added {added} uncertainty labels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
