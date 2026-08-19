#!/usr/bin/env python3
"""Create an analysis blueprint from one natural-language question."""

from __future__ import annotations

import argparse
from pathlib import Path

from analytics_router import build_blueprint, write_blueprint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Route one question into descriptive, predictive, and prescriptive "
            "analysis, then write a visual blueprint."
        )
    )
    parser.add_argument("question", help="Natural-language analytical question.")
    parser.add_argument(
        "--context",
        default="",
        help="Optional domain, decision, audience, or data context.",
    )
    parser.add_argument(
        "--scope",
        choices=("full", "auto"),
        default="full",
        help=(
            "full plans all three lenses; auto uses only the primary lens and its "
            "prerequisites (default: full)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for the Markdown, JSON, and SVG blueprint.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    blueprint = build_blueprint(
        args.question,
        context=args.context,
        scope=args.scope,
    )
    json_path, report_path, figure_path = write_blueprint(
        blueprint,
        args.output_dir,
    )
    print(f"Primary mode: {blueprint['routing']['primary_label']}")
    print(
        "Execution order: "
        + " -> ".join(blueprint["routing"]["execution_order"])
    )
    print(f"Blueprint JSON: {json_path}")
    print(f"Blueprint report: {report_path}")
    print(f"Blueprint visual: {figure_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
