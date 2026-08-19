#!/usr/bin/env python3
"""Build the compact, self-contained agent Skill from canonical repository files."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "high-stakes-analytics-decision-lab"
BUNDLE_ROOT = ROOT / "skills" / SKILL_NAME
CASE_ROOT = ROOT / "examples" / "real-data-cases"
REPOSITORY_URL = (
    "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab"
)

SCRIPT_NAMES = (
    "allocation_optimizer.py",
    "analytics_router.py",
    "data_quality.py",
    "decision_engine.py",
    "doctor.py",
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
REFERENCE_NAMES = (
    "advanced-method-boundaries.md",
    "analytics-triad.md",
    "case-schema.md",
    "data-quality-gate.md",
    "domain-playbooks.md",
    "editorial-visual-system.md",
    "method-domain-map.json",
    "method-modules.md",
    "method-routing.md",
    "methodology.md",
    "provenance-contract.md",
    "real-evidence-workflow.md",
    "reporting-standard.md",
    "reproducibility-contract.md",
    "visual-report-system.md",
)
ASSET_NAMES = (
    "case-template.json",
    "data-contract-template.json",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def _case_precedents() -> str:
    case_payload = _read_json(CASE_ROOT / "cases.json")
    capability_payload = _read_json(CASE_ROOT / "capability-map.json")
    cases = case_payload.get("cases", [])
    capabilities = capability_payload.get("capabilities", [])
    mappings = capability_payload.get("cases", {})
    if not isinstance(cases, list) or len(cases) != 15:
        raise ValueError("The compact Skill requires exactly fifteen case precedents.")
    if not isinstance(capabilities, list) or not isinstance(mappings, dict):
        raise ValueError("The capability map is incomplete.")
    labels = {item["id"]: item["label"] for item in capabilities}
    lines = [
        "# Fifteen case precedents",
        "",
        (
            "These school-neutral precedents are navigation aids. Reuse a method contract, "
            "not a saved empirical result, threshold, subgroup, weight, causal claim, or "
            "recommendation. Follow the linked report for full sources and limitations."
        ),
        "",
        "| # | Case | Route | Capability path | Valid endpoint |",
        "|---:|---|---|---|---|",
    ]
    for case in cases:
        mapping = mappings.get(case["id"], {})
        primary = labels.get(mapping.get("primary"), "Unmapped")
        supporting = [labels.get(item, item) for item in mapping.get("supporting", [])]
        capability_path = " → ".join([primary, *supporting])
        card = (
            f"{REPOSITORY_URL}/blob/main/examples/real-data-cases/cases/"
            f"{case['number']}-{case['id']}.md"
        )
        routes = " / ".join(case["route"])
        lines.append(
            f"| {case['number']} | [{case['gallery_title']}]({card}) | {routes} | "
            f"{capability_path} | {case['terminal_output']} |"
        )
    lines.extend(["", "## Selection notes", ""])
    for case in cases:
        mapping = mappings[case["id"]]
        signals = "; ".join(mapping["signals"])
        project = (
            f"{REPOSITORY_URL}/tree/main/examples/real-data-cases/projects/"
            f"{case['project_id']}"
        )
        lines.extend(
            [
                f"### {case['number']} · {case['gallery_title']}",
                "",
                f"- Question: {case['question']}",
                f"- Reviewer signals: {signals}.",
                f"- Boundary: {case['boundary']}",
                f"- Full reproducible project: [{case['project_id']}]({project})",
                "",
            ]
        )
    return "\n".join(lines)


def _reset_generated_paths() -> None:
    for directory in ("scripts", "references", "assets"):
        target = BUNDLE_ROOT / directory
        if target.exists():
            shutil.rmtree(target)
    for filename in ("LICENSE.txt", "bundle-manifest.json"):
        target = BUNDLE_ROOT / filename
        if target.exists():
            target.unlink()


def _copy(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build_bundle() -> dict[str, Any]:
    if not (BUNDLE_ROOT / "SKILL.md").is_file():
        raise FileNotFoundError(BUNDLE_ROOT / "SKILL.md")
    if not (BUNDLE_ROOT / "agents" / "openai.yaml").is_file():
        raise FileNotFoundError(BUNDLE_ROOT / "agents" / "openai.yaml")
    _reset_generated_paths()

    for name in SCRIPT_NAMES:
        _copy(ROOT / "scripts" / name, BUNDLE_ROOT / "scripts" / name)
    for name in REFERENCE_NAMES:
        _copy(ROOT / "references" / name, BUNDLE_ROOT / "references" / name)
    for name in ASSET_NAMES:
        _copy(ROOT / "assets" / name, BUNDLE_ROOT / "assets" / name)
    _copy(ROOT / "LICENSE.txt", BUNDLE_ROOT / "LICENSE.txt")
    precedent_path = BUNDLE_ROOT / "references" / "case-precedents.md"
    precedent_path.write_text(_case_precedents(), encoding="utf-8")

    entries = []
    for path in sorted(item for item in BUNDLE_ROOT.rglob("*") if item.is_file()):
        if path.name == "bundle-manifest.json":
            continue
        relative = path.relative_to(BUNDLE_ROOT).as_posix()
        entries.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "skill": SKILL_NAME,
        "generator": "scripts/build_skill_bundle.py",
        "school_neutral": True,
        "file_count_excluding_manifest": len(entries),
        "bytes_excluding_manifest": sum(entry["bytes"] for entry in entries),
        "files": entries,
    }
    manifest_path = BUNDLE_ROOT / "bundle-manifest.json"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    payload = build_bundle()
    print(
        json.dumps(
            {
                "skill": payload["skill"],
                "files": payload["file_count_excluding_manifest"] + 1,
                "kilobytes": round((payload["bytes_excluding_manifest"] + (BUNDLE_ROOT / "bundle-manifest.json").stat().st_size) / 1024, 1),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
