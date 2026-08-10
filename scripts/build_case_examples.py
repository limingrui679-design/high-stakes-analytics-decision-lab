#!/usr/bin/env python3
"""Validate and build the bundled real-data case gallery."""

from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

from build_terminal_decision_reports import build_all as build_terminal_reports
from visual_system import (
    CATEGORY_PALETTE,
    GRID_DARK,
    INK,
    MUTED,
    PAPER,
    rounded_rect,
    svg_document,
    text,
    wrapped_text,
)


SKILL_ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = SKILL_ROOT / "examples" / "real-data-cases"
CASE_INDEX = CASE_ROOT / "cases.json"
CASE_DIR = CASE_ROOT / "cases"
FIGURE_DIR = CASE_ROOT / "figures"
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PROJECT_FIGURES = {
    "population-health-survival": "temporal-calibration.svg",
    "behavioral-reading-experiment": "paired-effect.svg",
    "census-income-ai": "temporal-performance.svg",
    "bike-demand-operations": "forecast-mae.svg",
    "cross-city-311-shift": "within-city-shift.svg",
    "bank-marketing-response": "capacity-capture.svg",
    "treasury-risk-engineering": "expected-shortfall.svg",
    "sec-nport-filing-review": "risk-indicator-p90.svg",
    "cfpb-fintech-complaint-operations": "cumulative-gain.svg",
    "commercial-real-estate-risk": "borough-price-per-sqft.svg",
    "wildfire-mitigation-under-uncertainty": "scenario-regret.svg",
    "social-norm-field-experiment": "cluster-robust-itt.svg",
    "opportunity-zone-policy-evaluation": "matched-change-effects.svg",
    "nhanes-population-transportability": "transport-calibration.svg",
    "spatial-equity-planning": "need-map.svg",
}


def sync_representative_figures() -> None:
    payload = json.loads(CASE_INDEX.read_text(encoding="utf-8"))
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    expected = {Path(case["figure"]).name for case in payload.get("cases", [])}
    for path in FIGURE_DIR.glob("*.svg"):
        if path.name != "case-landscape.svg" and path.name not in expected:
            path.unlink()
    for case in payload.get("cases", []):
        source = (
            CASE_ROOT
            / "projects"
            / case["project_id"]
            / "outputs"
            / "figures"
            / PROJECT_FIGURES[case["project_id"]]
        )
        target = CASE_ROOT / case["figure"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def validate_local_links(markdown_path: Path) -> None:
    """Require every relative Markdown target in a report to resolve."""
    body = markdown_path.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", body):
        clean = target.strip().split(maxsplit=1)[0].strip("<>")
        if (
            not clean
            or clean.startswith(("#", "https://", "http://", "mailto:"))
        ):
            continue
        resolved = (markdown_path.parent / clean.split("#", 1)[0]).resolve()
        if not resolved.exists():
            raise ValueError(
                f"Broken local link in {markdown_path}: {target}"
            )


def load_cases() -> list[dict]:
    payload = json.loads(CASE_INDEX.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if payload.get("case_count") != 15 or len(cases) != 15:
        raise ValueError("The bundled real-data gallery must contain exactly fifteen cases.")
    ids = [case.get("id") for case in cases]
    numbers = [case.get("number") for case in cases]
    if len(set(ids)) != 15 or len(set(numbers)) != 15:
        raise ValueError("Case identifiers and display numbers must be unique.")
    for case in cases:
        required = {
            "number",
            "id",
            "project_id",
            "title",
            "gallery_title",
            "gallery_endpoint",
            "domain",
            "route",
            "question",
            "source",
            "methods",
            "headline_metrics",
            "result",
            "terminal_output",
            "boundary",
            "figure",
            "figure_alt",
        }
        missing = sorted(required - set(case))
        if missing:
            raise ValueError(f"{case.get('id', 'unknown')} missing fields: {missing}")
        source = case["source"]
        for field in (
            "dataset",
            "publisher",
            "url",
            "version",
            "accessed_at",
            "license",
            "grain",
            "prepared_rows",
            "snapshot_files",
        ):
            if field not in source:
                raise ValueError(f"{case['id']} source missing {field}.")
        if not str(source["url"]).startswith("https://"):
            raise ValueError(f"{case['id']} source URL must use HTTPS.")
        if int(source["prepared_rows"]) < 1:
            raise ValueError(f"{case['id']} must have at least one prepared row.")
        project_root = CASE_ROOT / "projects" / case["project_id"]
        report_path = project_root / "outputs" / "report.md"
        manifest_path = project_root / "source-manifest.json"
        results_path = project_root / "outputs" / "results.json"
        required_project_paths = (
            project_root / "PROJECT.md",
            manifest_path,
            project_root / "config.json",
            project_root / "download_data.py",
            project_root / "prepare_data.py",
            project_root / "analyze.py",
            project_root / "build_decision_case.py",
            project_root / "data" / "processed" / "analysis.csv",
            project_root / "data" / "data-dictionary.json",
            project_root / "data" / "quality-report.json",
            project_root / "outputs" / "chart-map.json",
            report_path,
            results_path,
        )
        for required_path in required_project_paths:
            if not required_path.exists():
                raise ValueError(f"{case['id']} is missing {required_path}.")
        figures = sorted((project_root / "outputs" / "figures").glob("*.svg"))
        if len(figures) < 3:
            raise ValueError(f"{case['id']} must bundle at least three figures.")
        validate_local_links(report_path)
        validate_local_links(project_root / "PROJECT.md")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("project_id") != case["project_id"]:
            raise ValueError(f"{case['id']} project and manifest identifiers differ.")
        if int(manifest.get("expected_rows", -1)) != int(source["prepared_rows"]):
            raise ValueError(f"{case['id']} prepared-row count differs from its manifest.")
        manifest_hashes = {
            Path(item["path"]).name: item["sha256"]
            for item in manifest.get("raw_files", [])
        }
        for snapshot in source["snapshot_files"]:
            if not HASH_PATTERN.fullmatch(str(snapshot.get("sha256", ""))):
                raise ValueError(f"{case['id']} has an invalid SHA-256 value.")
            if manifest_hashes.get(snapshot["name"]) != snapshot["sha256"]:
                raise ValueError(f"{case['id']} case and manifest hashes differ.")
            raw_path = project_root / "data" / "raw" / snapshot["name"]
            if not raw_path.exists():
                raise ValueError(f"{case['id']} bundled raw file is missing.")
            digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            if digest != snapshot["sha256"]:
                raise ValueError(f"{case['id']} bundled raw-file hash differs.")
        figure_path = CASE_ROOT / case["figure"]
        if not figure_path.exists():
            raise ValueError(f"{case['id']} figure is missing: {figure_path}")
        source_figure = (
            project_root
            / "outputs"
            / "figures"
            / PROJECT_FIGURES[case["project_id"]]
        )
        if not source_figure.exists():
            raise ValueError(f"{case['id']} source figure is missing.")
        if hashlib.sha256(figure_path.read_bytes()).digest() != hashlib.sha256(
            source_figure.read_bytes()
        ).digest():
            raise ValueError(
                f"{case['id']} representative figure differs from project output."
            )
        decision_report = (
            project_root
            / "outputs"
            / "decision"
            / "report"
            / "decision-report.md"
        )
        decision_result = decision_report.parent / "decision-results.json"
        decision_chart_map = decision_report.parent / "figures" / "chart-map.json"
        if decision_report.exists():
            for required_decision_path in (
                decision_result,
                decision_chart_map,
            ):
                if not required_decision_path.exists():
                    raise ValueError(
                        f"{case['id']} is missing complete decision output: "
                        f"{required_decision_path}"
                    )
            decision_figures = sorted(
                (decision_report.parent / "figures").glob("*.svg")
            )
            if len(decision_figures) < 2:
                raise ValueError(
                    f"{case['id']} must bundle at least two decision-report figures."
                )
            validate_local_links(decision_report)
    return cases


def card_filename(case: dict) -> str:
    return f"{case['number']}-{case['id']}.md"


def case_card(case: dict) -> str:
    source = case["source"]
    routes = " → ".join(case["route"])
    metrics = "\n".join(
        f"- **{metric['label']}:** {metric['value']}"
        for metric in case["headline_metrics"]
    )
    methods = "\n".join(f"- {method}" for method in case["methods"])
    snapshots = "\n".join(
        f"- `{snapshot['name']}` — `{snapshot['sha256']}`"
        for snapshot in source["snapshot_files"]
    )
    analyzed_note = ""
    if source.get("analyzed_rows") is not None:
        analyzed_note = f"\n| Analyzed rows | {source['analyzed_rows']:,} |"
    figure_relative = "../" + case["figure"]
    project_relative = f"../projects/{case['project_id']}"
    decision_report = (
        CASE_ROOT
        / "projects"
        / case["project_id"]
        / "outputs"
        / "decision"
        / "report"
        / "decision-report.md"
    )
    decision_link = ""
    if decision_report.exists():
        decision_link = (
            f"\n- [Open the Decision Intelligence Brief]"
            f"({project_relative}/outputs/decision/report/decision-report.md)"
        )
    return f"""# {case['number']} · {case['title']}

**Technical summary.** {case['result']}

## Evidence products

- [Open the Evidence Intelligence Report]({project_relative}/outputs/report.md)
- [Review the project design]({project_relative}/PROJECT.md)
- [Inspect the source manifest]({project_relative}/source-manifest.json)
- [Inspect the machine-readable results]({project_relative}/outputs/results.json){decision_link}

![{case['figure_alt']}]({figure_relative})

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | {case['domain']} |
| Adaptive route | {routes} |
| Analytical question | {case['question']} |
| Prepared rows | {source['prepared_rows']:,} |{analyzed_note}
| Valid terminal output | {case['terminal_output']} |

## Evidence-backed findings

{metrics}

## Methods selected for this case

{methods}

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

{case['boundary']}

## Source identity

- **Dataset:** [{source['dataset']}]({source['url']})
- **Publisher:** {source['publisher']}
- **Version:** {source['version']}
- **Accessed:** {source['accessed_at']}
- **License:** {source['license']}
- **Analytical grain:** {source['grain']}

### Reviewed source-snapshot hashes

{snapshots}

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
"""


def gallery_svg(cases: list[dict]) -> str:
    body: list[str] = []
    x_positions = [42, 618]
    card_width = 540
    card_height = 128
    top = 138
    row_gap = 16
    for index, case in enumerate(cases):
        row = index // 2
        column = index % 2
        x = x_positions[column]
        y = top + row * (card_height + row_gap)
        color = CATEGORY_PALETTE[index % len(CATEGORY_PALETTE)]
        body.append(
            rounded_rect(
                x,
                y,
                card_width,
                card_height,
                fill=PAPER,
                stroke=GRID_DARK,
                radius=14,
            )
        )
        body.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="8" height="{card_height}" '
            f'rx="4" fill="{color}"/>'
        )
        body.append(text(x + 24, y + 24, case["number"], css="eyebrow", fill=color))
        body.append(
            text(
                x + 68,
                y + 24,
                " → ".join(case["route"]).upper(),
                css="eyebrow",
                fill=MUTED,
            )
        )
        title_lines = wrapped_text(
            x + 24,
            y + 52,
            case["gallery_title"],
            chars=45,
            line_height=18,
            css="section",
            fill=INK,
        )
        body.append(title_lines)
        first_metric = case["headline_metrics"][0]
        body.append(
            text(
                x + 24,
                y + 101,
                f"{first_metric['label']}: {first_metric['value']}",
                css="small",
                fill=MUTED,
            )
        )
        body.append(
            text(
                x + 24,
                y + 120,
                case["gallery_endpoint"],
                css="small",
                fill=color,
            )
        )
    return svg_document(
        "Fifteen complete real-data projects, fifteen evidence-matched paths",
        "Complete projects span health, behavior, AI, operations, business, finance, policy, and spatial planning.",
        "\n".join(body),
        height=1380,
        description=(
            "Fifteen numbered cards show each case domain, adaptive analytical route, "
            "one headline metric, and the evidence-matched terminal output."
        ),
        accent=CATEGORY_PALETTE[0],
        kicker="REAL-DATA CASE GALLERY",
        source="Sources: official or academic datasets; identities and hashes in cases.json",
        note="Complete reports · code · figures · reviewed source snapshots",
    )


def gallery_readme(cases: list[dict]) -> str:
    rows = []
    for case in cases:
        link = f"cases/{card_filename(case)}"
        report = f"projects/{case['project_id']}/outputs/report.md"
        decision_report = (
            f"projects/{case['project_id']}/outputs/decision/report/"
            "decision-report.md"
        )
        decision_path = CASE_ROOT / decision_report
        terminal_link = (
            f"[Decision]({decision_report})"
            if decision_path.exists()
            else f"[Terminal result](projects/{case['project_id']}/outputs/results.json)"
        )
        evidence = case["headline_metrics"][0]
        rows.append(
            f"| {case['number']} · {case['title']} | "
            f"{case['domain']}<br>{evidence['label']}: {evidence['value']} | "
            f"{' → '.join(case['route'])} | "
            f"[Evidence]({report}) · [Card]({link}) · {terminal_link} |"
        )
    gallery_cells = []
    for index in range(0, len(cases), 2):
        cells = []
        for case in cases[index : index + 2]:
            link = f"cases/{card_filename(case)}"
            report = f"projects/{case['project_id']}/outputs/report.md"
            decision_report = (
                f"projects/{case['project_id']}/outputs/decision/report/"
                "decision-report.md"
            )
            decision_path = CASE_ROOT / decision_report
            terminal_link = (
                f'<a href="{decision_report}">Decision Intelligence Brief</a>'
                if decision_path.exists()
                else f'<a href="projects/{case["project_id"]}/outputs/results.json">Terminal result</a>'
            )
            cells.append(
                f"""<td width="50%">
  <a href="{report}">
    <img src="{case['figure']}" alt="{case['figure_alt']}">
  </a>
  <br><strong>{case['number']} · {case['title']}</strong>
  <br>{case['result']}
  <br><em>Boundary:</em> {case['boundary']}
  <br><a href="{link}">Case card</a> · <a href="{report}">Evidence Intelligence Report</a>
  · {terminal_link}
</td>"""
            )
        gallery_cells.append("<tr>\n" + "\n".join(cells) + "\n</tr>")
    return f"""# Fifteen Complete Real-Data Projects

## Technical summary

The fifteen projects share one evidence spine but do not share one report template.
Each route changes the methods, validation, figures, and valid endpoint.

| Fixed across projects | Adapted to the case | Valid endpoints |
|---|---|---|
| Source lineage, data quality, uncertainty, limitations, and reproducibility | Descriptive, inferential, diagnostic, predictive, or prescriptive modules | Bounded action, non-deployment, diligence request, evidence request, or no decision |

The **Evidence Intelligence Report** remains the primary product. A separate
Decision Intelligence Brief appears only when a decision layer is justified.

<p align="center">
  <img src="figures/case-landscape.svg" alt="Fifteen real-data cases and their evidence-matched analytical paths" width="92%">
</p>

The overview should be read as a routing map. It shows why some cases end in a
bounded recommendation while others end in negative validation, a diligence
request, or an evidence request.

<details>
<summary><strong>What every complete project bundles</strong></summary>

```text
projects/
├── _shared/                 # shared standard-library analytical runtime
├── project-catalog.json     # fifteen-project machine-readable index
└── <project-id>/
    ├── PROJECT.md
    ├── source-manifest.json
    ├── config.json
    ├── download_data.py
    ├── prepare_data.py
    ├── analyze.py
    ├── build_decision_case.py
    ├── data/                # reviewed raw snapshot, prepared data, dictionary, quality
    └── outputs/             # evidence report, decision brief, figures, results
```

</details>

## Evidence Intelligence index

| Project | Domain and headline evidence | Adaptive route | Open artifacts |
|---|---|---|---|
{chr(10).join(rows)}

## Optional visual gallery

The index above is the default reading path. Open the gallery only when a
visual comparison across all fifteen projects is useful.

<details>
<summary><strong>Open fifteen representative visuals and claim boundaries</strong></summary>

<table>
{chr(10).join(gallery_cells)}
</table>

</details>

## Machine-readable evidence

[`cases.json`](cases.json) is the canonical case index. It records the sources,
reviewed snapshot hashes, data grain, methods, metrics, result, terminal
output, interpretation boundary, and representative figure for every case.
The generator checks the bundled raw files against those hashes and each
project's source manifest before rebuilding the navigation layer.

<details>
<summary><strong>Regenerate the cards, landscape, and index</strong></summary>

Regenerate the individual cards and overview:

```bash
python3 ../../scripts/build_case_examples.py
```

</details>

## Reuse rule

Reuse the method contract, not a saved result. A different source, population,
time window, objective, constraint, or decision owner requires new evidence
and a new validation path.
"""


def main() -> int:
    build_terminal_reports(CASE_ROOT / "projects")
    sync_representative_figures()
    cases = load_cases()
    CASE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    expected_cards = {card_filename(case) for case in cases}
    for path in CASE_DIR.glob("*.md"):
        if path.name not in expected_cards:
            path.unlink()
    for case in cases:
        (CASE_DIR / card_filename(case)).write_text(
            case_card(case),
            encoding="utf-8",
        )
    (FIGURE_DIR / "case-landscape.svg").write_text(
        gallery_svg(cases),
        encoding="utf-8",
    )
    (CASE_ROOT / "README.md").write_text(
        gallery_readme(cases),
        encoding="utf-8",
    )
    print(f"Validated and indexed {len(cases)} complete real-data projects in {CASE_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
