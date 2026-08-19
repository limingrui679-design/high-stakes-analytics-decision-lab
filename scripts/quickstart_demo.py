#!/usr/bin/env python3
"""Build a small, clearly synthetic data-readiness demo without fitting a model."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

from init_case import initialize_workspace

GENERATOR_ID = "high-stakes-analytics-decision-lab/quickstart-demo-v1"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owned_demo(path: Path) -> bool:
    marker = path / "demo-metadata.json"
    if not marker.is_file():
        return False
    try:
        return json.loads(marker.read_text(encoding="utf-8")).get("generated_by") == GENERATOR_ID
    except (json.JSONDecodeError, OSError):
        return False


def _write_inputs(root: Path) -> tuple[Path, Path]:
    source = root / "support-demand-demo.csv"
    rows = [
        {"row_id": "01", "month": "2026-01-01", "region": "North", "requests": 112},
        {"row_id": "02", "month": "2026-01-01", "region": "South", "requests": 94},
        {"row_id": "03", "month": "2026-02-01", "region": "North", "requests": 118},
        {"row_id": "04", "month": "2026-02-01", "region": "South", "requests": 97},
        {"row_id": "05", "month": "2026-03-01", "region": "North", "requests": 121},
        {"row_id": "06", "month": "2026-03-01", "region": "South", "requests": 103},
        {"row_id": "07", "month": "2026-04-01", "region": "North", "requests": 125},
        {"row_id": "08", "month": "2026-04-01", "region": "South", "requests": 107},
    ]
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    contract = root / "data-contract.json"
    _write_json(
        contract,
        {
            "schema_version": "1.0",
            "contract_source": "user_supplied",
            "dataset_name": "support-demand-demo",
            "intended_use": "descriptive",
            "grain": "one row per region-month",
            "required_columns": ["row_id", "month", "region", "requests"],
            "primary_key": ["row_id"],
            "date_columns": ["month"],
            "numeric_columns": ["requests"],
            "numeric_ranges": {"requests": {"minimum": 0, "maximum": 1000}},
            "categorical_columns": {"region": ["North", "South"]},
            "target_column": None,
            "feature_columns": [],
            "forbidden_columns": [],
            "direct_identifier_columns": [],
            "sensitive_columns": [],
            "missing_tokens": [""],
        },
    )
    return source, contract


def build_demo(output_dir: Path) -> dict[str, Any]:
    destination = output_dir.expanduser().resolve()
    if destination.exists():
        if not _owned_demo(destination):
            raise FileExistsError(
                "Demo output exists and is not owned by this generator; choose another directory: "
                f"{destination}"
            )
        shutil.rmtree(destination)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="hsadl-demo-input-") as temporary:
        source, contract = _write_inputs(Path(temporary))
        manifest = initialize_workspace(
            source,
            "What is happening to monthly support demand across regions?",
            destination,
            contract_path=contract,
            scope="auto",
        )
    elapsed = time.perf_counter() - started
    metadata = {
        "schema_version": "1.0",
        "generated_by": GENERATOR_ID,
        "synthetic_engineering_fixture": True,
        "empirical_claims_permitted": False,
        "model_fitted": False,
        "recommendation_generated": False,
        "quality_gate": manifest["data_quality"]["status"],
        "primary_route": manifest["routing"]["primary_mode"],
        "elapsed_seconds": round(elapsed, 3),
    }
    _write_json(destination / "demo-metadata.json", metadata)
    (destination / "DEMO.md").write_text(
        "# 60-second readiness demo\n\n"
        "> This is a synthetic engineering fixture. It proves the setup and gate "
        "workflow, not an empirical result.\n\n"
        f"- Quality gate: `{metadata['quality_gate']}`\n"
        f"- Suggested route: `{metadata['primary_route']}`\n"
        "- Cleaning applied: `false`\n"
        "- Model fitted: `false`\n"
        "- Recommendation generated: `false`\n\n"
        "Open [README.md](README.md), then inspect the data-quality report, "
        "analysis blueprint, machine-readable setup contract, and accessible SVGs.\n",
        encoding="utf-8",
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("build/demo"))
    args = parser.parse_args()
    try:
        result = build_demo(args.output_dir)
    except (FileExistsError, OSError, ValueError) as error:
        raise SystemExit(f"quickstart_demo.py: error: {error}") from error
    print(f"Demo: {args.output_dir.expanduser().resolve()}")
    print(f"Quality gate: {result['quality_gate']}")
    print(f"Elapsed: {result['elapsed_seconds']:.3f}s")
    print("Boundary: synthetic engineering fixture; no empirical result or recommendation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
