#!/usr/bin/env python3
"""Build the school-neutral data payload used by the interactive case explorer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "examples" / "real-data-cases"
OUTPUT = ROOT / "demo" / "data.js"
REPOSITORY_URL = (
    "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab"
)
ROUTE_ALIASES = {
    "decision": "prescriptive",
    "inferential": "diagnostic",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def build_payload() -> dict[str, Any]:
    case_payload = _load(CASE_ROOT / "cases.json")
    capability_payload = _load(CASE_ROOT / "capability-map.json")
    cases = case_payload.get("cases", [])
    capabilities = capability_payload.get("capabilities", [])
    mappings = capability_payload.get("cases", {})
    if not isinstance(cases, list) or len(cases) != 15:
        raise ValueError("The explorer requires exactly fifteen cases.")
    if not isinstance(capabilities, list) or not isinstance(mappings, dict):
        raise ValueError("The capability map is incomplete.")
    labels = {item["id"]: item["label"] for item in capabilities}
    demo_cases = []
    for case in cases:
        mapping = mappings.get(case["id"])
        if not isinstance(mapping, dict):
            raise ValueError(f"Missing capability path for {case['id']}.")
        capability_ids = [mapping["primary"], *mapping.get("supporting", [])]
        if any(item not in labels for item in capability_ids):
            raise ValueError(f"Unknown capability path for {case['id']}.")
        routes = list(
            dict.fromkeys(ROUTE_ALIASES.get(item, item) for item in case["route"])
        )
        demo_cases.append(
            {
                "number": case["number"],
                "id": case["id"],
                "title": case["gallery_title"],
                "domain": case["domain"],
                "routes": routes,
                "question": case["question"],
                "result": case["result"],
                "endpoint": case["terminal_output"],
                "boundary": case["boundary"],
                "capabilities": capability_ids,
                "capability_labels": [labels[item] for item in capability_ids],
                "signals": mapping["signals"],
                "figure": f"../examples/real-data-cases/{case['figure']}",
                "figure_alt": case["figure_alt"],
                "case_card": (
                    f"{REPOSITORY_URL}/blob/main/examples/real-data-cases/cases/"
                    f"{case['number']}-{case['id']}.md"
                ),
                "project": (
                    f"{REPOSITORY_URL}/blob/main/examples/real-data-cases/projects/"
                    f"{case['project_id']}/PROJECT.md"
                ),
            }
        )
    return {
        "schema_version": "1.0",
        "school_neutral": True,
        "boundary": (
            "Public-data research portfolio; no production deployment, institutional "
            "adoption, external review, or achieved real-world impact is implied."
        ),
        "metrics": {
            "cases": 15,
            "routes": 4,
            "capabilities": len(capabilities),
            "accessible_figures": 119,
        },
        "capabilities": capabilities,
        "cases": demo_cases,
    }


def render_data(payload: dict[str, Any] | None = None) -> str:
    current = payload or build_payload()
    return "window.HSADL_DEMO = " + json.dumps(
        current,
        ensure_ascii=False,
        indent=2,
    ) + ";\n"


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_data(), encoding="utf-8")
    print(json.dumps({"path": str(OUTPUT), "cases": 15, "school_neutral": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
