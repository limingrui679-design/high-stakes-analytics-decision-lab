#!/usr/bin/env python3
"""Build the GitHub-native editorial visuals used by the Skill README."""

from __future__ import annotations

from html import escape
from pathlib import Path

from visual_system import (
    BLUE,
    BLUE_TINT,
    CANVAS,
    CORAL,
    GOLD,
    GOLD_TINT,
    GRID,
    GRID_DARK,
    GREEN,
    INK,
    INK_SOFT,
    MAGENTA,
    MUTED,
    NAVY,
    NAVY_2,
    PAPER,
    QUIET,
    TEAL,
    TEAL_TINT,
    VIOLET,
    VIOLET_TINT,
    rounded_rect,
    svg_document,
    text,
    wrapped_text,
)


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets"
PROJECT_ROOT = ROOT / "examples" / "real-data-cases" / "projects"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif"


def _portfolio_metrics() -> dict[str, int]:
    project_count = sum(
        1
        for path in PROJECT_ROOT.iterdir()
        if path.is_dir() and not path.name.startswith("_")
    )
    evidence_reports = len(list(PROJECT_ROOT.glob("*/outputs/report.md")))
    decision_reports = len(
        list(PROJECT_ROOT.glob("*/outputs/decision/report/decision-report.md"))
    )
    evidence_figures = len(list(PROJECT_ROOT.glob("*/outputs/figures/*.svg")))
    decision_figures = len(
        list(PROJECT_ROOT.glob("*/outputs/decision/report/figures/*.svg"))
    )
    return {
        "real_data_projects": project_count,
        "primary_reports": evidence_reports,
        "conditional_briefs": decision_reports,
        "intelligence_products": evidence_reports + decision_reports,
        "evidence_figures": evidence_figures,
        "decision_figures": decision_figures,
        "accessible_figures": evidence_figures + decision_figures,
        "adaptive_routes": len(
            ("descriptive", "diagnostic", "predictive", "prescriptive")
        ),
    }


def _hero_text(
    x: float,
    y: float,
    value: str,
    *,
    size: int,
    weight: int = 400,
    fill: str = PAPER,
    anchor: str = "start",
    spacing: float = 0,
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
        f'letter-spacing="{spacing}" fill="{fill}">{escape(value)}</text>'
    )


def hero_svg() -> str:
    width, height = 1400, 760
    body = [
        f'<rect width="{width}" height="{height}" rx="28" fill="{NAVY}"/>',
        '<defs>',
        '<pattern id="heroGrid" width="24" height="24" patternUnits="userSpaceOnUse">',
        '<circle cx="1" cy="1" r=".9" fill="#FFFFFF" opacity=".11"/>',
        "</pattern>",
        "</defs>",
        f'<rect width="{width}" height="{height}" rx="28" fill="url(#heroGrid)"/>',
        f'<circle cx="1265" cy="88" r="198" fill="{NAVY_2}" opacity=".78"/>',
        f'<circle cx="1265" cy="88" r="102" fill="none" stroke="{TEAL}" stroke-width="2"/>',
        f'<circle cx="1265" cy="88" r="31" fill="{TEAL}"/>',
        f'<circle cx="1265" cy="88" r="14" fill="{NAVY}"/>',
        f'<line x1="1116" y1="88" x2="1398" y2="88" stroke="#36516F"/>',
        f'<line x1="1265" y1="-58" x2="1265" y2="232" stroke="#36516F"/>',
        _hero_text(
            64,
            55,
            "PLATFORM-NEUTRAL ANALYTICAL SKILL",
            size=12,
            weight=800,
            fill=TEAL,
            spacing=2,
        ),
        _hero_text(
            64,
            121,
            "High-Stakes Analytics & Decision Lab",
            size=48,
            weight=820,
        ),
        _hero_text(
            64,
            166,
            "Route the question. Prove the evidence. Match the report to the case.",
            size=22,
            weight=560,
            fill="#D4DFEC",
        ),
        _hero_text(
            64,
            201,
            "Evidence Intelligence is primary; a Decision Intelligence Brief is added only when justified.",
            size=15,
            weight=450,
            fill="#98ACC2",
        ),
    ]

    portfolio = _portfolio_metrics()
    metrics = [
        (str(portfolio["real_data_projects"]), "REAL-DATA PROJECTS", TEAL),
        (str(portfolio["intelligence_products"]), "INTELLIGENCE PRODUCTS", VIOLET),
        (str(portfolio["accessible_figures"]), "ACCESSIBLE FIGURES", GOLD),
        (f'{portfolio["adaptive_routes"]:02d}', "ADAPTIVE ROUTES", CORAL),
    ]
    for index, (value, label, color) in enumerate(metrics):
        x = 64 + index * 222
        body.extend(
            [
                f'<rect x="{x}" y="240" width="204" height="96" rx="16" '
                f'fill="#102B4B" stroke="#294866"/>',
                f'<rect x="{x}" y="240" width="6" height="96" rx="3" fill="{color}"/>',
                _hero_text(x + 22, 282, value, size=30, weight=840),
                _hero_text(
                    x + 22,
                    312,
                    label,
                    size=9,
                    weight=800,
                    fill="#93A9C0",
                    spacing=1.1,
                ),
            ]
        )

    sequence = [
        ("01", "QUESTION", "Decision context", "Owner · scope · horizon", BLUE),
        ("02", "ROUTE", "Evidence-matched method", "Describe · diagnose · predict", VIOLET),
        ("03", "EVIDENCE", "Intelligence report", "QA · methods · validation · all figures", TEAL),
        ("04", "DECISION", "Intelligence brief", "Gates · risk · status · reversal", GOLD),
    ]
    panel_y, panel_w, gap = 400, 294, 24
    for index, (number, label, headline, note, color) in enumerate(sequence):
        x = 64 + index * (panel_w + gap)
        body.extend(
            [
                f'<rect x="{x + 3}" y="{panel_y + 8}" width="{panel_w - 6}" height="216" '
                f'rx="20" fill="#020A14" opacity=".24"/>',
                f'<rect x="{x}" y="{panel_y}" width="{panel_w}" height="218" rx="20" '
                f'fill="{PAPER}" stroke="#33516E"/>',
                f'<rect x="{x}" y="{panel_y}" width="{panel_w}" height="8" rx="4" fill="{color}"/>',
                _hero_text(x + 25, panel_y + 42, number, size=11, weight=820, fill=color, spacing=1.3),
                _hero_text(x + 72, panel_y + 42, label, size=11, weight=820, fill=QUIET, spacing=1.1),
                _hero_text(x + 25, panel_y + 89, headline, size=19, weight=760, fill=INK),
                _hero_text(x + 25, panel_y + 122, note, size=12, weight=520, fill=MUTED),
                f'<line x1="{x + 25}" y1="{panel_y + 151}" x2="{x + panel_w - 25}" '
                f'y2="{panel_y + 151}" stroke="{GRID}"/>',
            ]
        )
        status = (
            "PRIMARY EVIDENCE"
            if index == 2
            else "ONLY WHEN JUSTIFIED"
            if index == 3
            else "EVIDENCE GATE"
        )
        status_color = TEAL if index == 2 else GOLD if index == 3 else QUIET
        body.append(
            _hero_text(
                x + 25,
                panel_y + 186,
                status,
                size=9,
                weight=820,
                fill=status_color,
                spacing=1.1,
            )
        )
        if index < len(sequence) - 1:
            start = x + panel_w + 5
            body.extend(
                [
                    f'<line x1="{start}" y1="{panel_y + 109}" x2="{start + gap - 10}" '
                    f'y2="{panel_y + 109}" stroke="{TEAL}" stroke-width="2"/>',
                    f'<path d="M {start + gap - 15} {panel_y + 103} '
                    f'L {start + gap - 8} {panel_y + 109} '
                    f'L {start + gap - 15} {panel_y + 115}" fill="none" '
                    f'stroke="{TEAL}" stroke-width="2"/>',
                ]
            )

    body.extend(
        [
            _hero_text(
                64,
                680,
                "DESCRIPTIVE",
                size=10,
                weight=820,
                fill=TEAL,
                spacing=1.2,
            ),
            _hero_text(
                245,
                680,
                "DIAGNOSTIC",
                size=10,
                weight=820,
                fill=GOLD,
                spacing=1.2,
            ),
            _hero_text(
                420,
                680,
                "PREDICTIVE",
                size=10,
                weight=820,
                fill=VIOLET,
                spacing=1.2,
            ),
            _hero_text(
                585,
                680,
                "PRESCRIPTIVE",
                size=10,
                weight=820,
                fill=CORAL,
                spacing=1.2,
            ),
            _hero_text(
                1336,
                680,
                "REAL DATA · REPRODUCIBLE · CLAIM-BOUNDED",
                size=10,
                weight=820,
                fill="#91A7BE",
                anchor="end",
                spacing=1.1,
            ),
            f'<line x1="64" y1="705" x2="1336" y2="705" stroke="#294866"/>',
            _hero_text(
                64,
                732,
                "Health · behavior · AI · operations · business · finance · policy · spatial planning",
                size=12,
                weight=560,
                fill="#AFC0D3",
            ),
        ]
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        '<title id="title">High-Stakes Analytics &amp; Decision Lab</title>'
        '<desc id="desc">An adaptive evidence workflow routes a question to an '
        "Evidence Intelligence Report first and adds a Decision Intelligence Brief "
        "only when the evidence supports it.</desc>"
        + "\n".join(body)
        + "</svg>\n"
    )


def report_layers_svg() -> str:
    body = [
        rounded_rect(38, 142, 714, 318, fill=PAPER, stroke=GRID_DARK, radius=20),
        f'<rect x="38" y="142" width="8" height="318" rx="4" fill="{TEAL}"/>',
        text(68, 177, "PRIMARY EVIDENCE LAYER", css="kicker", fill=TEAL),
        text(68, 216, "Evidence Intelligence Report", css="big", fill=INK),
        wrapped_text(
            68,
            247,
            "The primary evidence product readers use to inspect the question, source, data quality, method, validation, material figures, uncertainty, limitations, and reproducibility.",
            chars=80,
            line_height=19,
            css="label",
            fill=INK_SOFT,
        ),
    ]
    analysis_items = [
        ("01", "Source + data quality", "Manifest, hashes, grain, missingness"),
        ("02", "Method + validation", "Estimand, split, baseline, sensitivity"),
        ("03", "Material visual evidence", "Every analytical figure with interpretation"),
        ("04", "Claim boundary", "What the evidence can and cannot establish"),
    ]
    for index, (number, label, note) in enumerate(analysis_items):
        y = 318 + index * 34
        body.extend(
            [
                f'<circle cx="80" cy="{y - 4}" r="13" fill="{TEAL_TINT}"/>',
                text(80, y, number, css="micro", anchor="middle", fill=TEAL),
                text(106, y, label, css="section", fill=INK),
                text(332, y, note, css="small", fill=MUTED),
            ]
        )

    body.extend(
        [
            rounded_rect(784, 142, 378, 318, fill=PAPER, stroke=GRID_DARK, radius=20),
            f'<rect x="784" y="142" width="8" height="318" rx="4" fill="{GOLD}"/>',
            text(814, 177, "CONDITIONAL DECISION LAYER", css="kicker", fill=GOLD),
            text(814, 207, "Decision Intelligence", css="section", fill=INK),
            text(814, 234, "Brief", css="big", fill=INK),
            wrapped_text(
                814,
                265,
                "Added only when a real decision, feasible alternatives, and sufficient evidence exist.",
                chars=43,
                line_height=19,
                css="label",
                fill=INK_SOFT,
            ),
        ]
    )
    decision_items = [
        ("GATES", "What passes, blocks, or is missing"),
        ("RISK", "Constraints, tails, shared shocks"),
        ("STATUS", "Act, pilot, request evidence, or stop"),
        ("REVERSAL", "What new evidence would change the result"),
    ]
    for index, (label, note) in enumerate(decision_items):
        y = 328 + index * 38
        body.extend(
            [
                rounded_rect(
                    814,
                    y - 23,
                    316,
                    30,
                    fill=GOLD_TINT if index < 2 else VIOLET_TINT,
                    stroke="none",
                    radius=15,
                ),
                text(830, y - 3, label, css="micro", fill=GOLD if index < 2 else VIOLET),
                text(895, y - 3, note, css="small", fill=INK_SOFT),
            ]
        )

    body.extend(
        [
            f'<path d="M 752 299 C 770 299, 770 299, 784 299" fill="none" '
            f'stroke="{TEAL}" stroke-width="3"/>',
            f'<path d="M 776 293 L 784 299 L 776 305" fill="none" '
            f'stroke="{TEAL}" stroke-width="3"/>',
            rounded_rect(38, 486, 1124, 60, fill=NAVY, stroke=NAVY, radius=16),
            text(62, 511, "SHARED EVIDENCE SPINE", css="kicker", fill=TEAL),
            text(
                62,
                535,
                "Markdown narrative  ·  JSON results  ·  CSV evidence  ·  accessible SVG figures  ·  source lineage",
                css="label",
                fill="#D4DFEC",
            ),
        ]
    )
    return svg_document(
        "Two intelligence products, one evidence contract",
        "The Evidence Intelligence Report is primary; the Decision Intelligence Brief is conditional.",
        "\n".join(body),
        height=600,
        description=(
            "A large primary Evidence Intelligence Report panel feeds a smaller "
            "conditional Decision Intelligence Brief panel. Both share machine-readable "
            "evidence and source lineage."
        ),
        accent=TEAL,
        kicker="REPORT ARCHITECTURE",
        source="Source: reporting contract",
        note="Evidence first · decision second · no forced recommendation",
    )


def adaptive_system_svg() -> str:
    body = [
        rounded_rect(38, 144, 258, 318, fill=PAPER, stroke=GRID_DARK, radius=20),
        text(64, 177, "CASE INPUTS", css="kicker", fill=BLUE),
    ]
    inputs = [
        ("01", "Question", "What must be learned or decided?"),
        ("02", "Evidence", "Grain · time · source · quality"),
        ("03", "Maturity", "Explore · validate · pilot · stop"),
    ]
    for index, (number, label, note) in enumerate(inputs):
        y = 217 + index * 76
        body.extend(
            [
                f'<circle cx="78" cy="{y}" r="17" fill="{BLUE_TINT}"/>',
                text(78, y + 4, number, css="micro", anchor="middle", fill=BLUE),
                text(108, y - 3, label, css="section", fill=INK),
                text(108, y + 20, note, css="small", fill=MUTED),
            ]
        )

    body.extend(
        [
            rounded_rect(338, 172, 294, 262, fill=NAVY, stroke=NAVY, radius=22),
            text(365, 208, "ADAPTIVE ROUTER", css="kicker", fill=TEAL),
            _hero_text(
                365,
                245,
                "Route before format",
                size=26,
                weight=800,
                fill=PAPER,
                spacing=-0.25,
            ),
            wrapped_text(
                365,
                278,
                "Select only the descriptive, diagnostic, predictive, and prescriptive work the evidence supports.",
                chars=38,
                line_height=20,
                css="label",
                fill="#D4DFEC",
            ),
        ]
    )
    routes = [
        ("DESCRIBE", TEAL),
        ("DIAGNOSE", GOLD),
        ("PREDICT", VIOLET),
        ("DECIDE", CORAL),
    ]
    for index, (label, color) in enumerate(routes):
        x = 365 + (index % 2) * 122
        y = 344 + (index // 2) * 43
        body.extend(
            [
                rounded_rect(x, y, 108, 29, fill=NAVY_2, stroke="#36516F", radius=14),
                text(x + 54, y + 19, label, css="micro", anchor="middle", fill=color),
            ]
        )

    body.extend(
        [
            rounded_rect(674, 144, 488, 142, fill=PAPER, stroke=GRID_DARK, radius=20),
            f'<rect x="674" y="144" width="8" height="142" rx="4" fill="{TEAL}"/>',
            text(704, 177, "PRIMARY OUTPUT", css="kicker", fill=TEAL),
            text(704, 211, "Evidence Intelligence Report", css="big", fill=INK),
            text(
                704,
                241,
                "Case-specific methods · interleaved figures · claim boundary",
                css="label",
                fill=INK_SOFT,
            ),
            rounded_rect(674, 316, 488, 146, fill=PAPER, stroke=GRID_DARK, radius=20),
            f'<rect x="674" y="316" width="8" height="146" rx="4" fill="{GOLD}"/>',
            text(704, 349, "CONDITIONAL OUTPUT", css="kicker", fill=GOLD),
            text(704, 383, "Decision Intelligence Brief", css="big", fill=INK),
            text(
                704,
                413,
                "Evidence gates · dependent shocks · reversal conditions",
                css="label",
                fill=INK_SOFT,
            ),
        ]
    )
    for start_x, end_x, y in ((296, 338, 303), (632, 674, 215), (632, 674, 388)):
        body.extend(
            [
                f'<line x1="{start_x}" y1="{y}" x2="{end_x - 8}" y2="{y}" '
                f'stroke="{TEAL}" stroke-width="3"/>',
                f'<path d="M {end_x - 14} {y - 6} L {end_x - 6} {y} '
                f'L {end_x - 14} {y + 6}" fill="none" stroke="{TEAL}" stroke-width="3"/>',
            ]
        )

    body.extend(
        [
            rounded_rect(38, 492, 1124, 94, fill=TEAL_TINT, stroke="none", radius=18),
            text(64, 519, "VALID TERMINAL STATES", css="kicker", fill=TEAL),
        ]
    )
    terminals = [
        ("BASELINE", "What is happening"),
        ("VALIDATION", "What may happen"),
        ("BOUNDED ACTION", "What to test next"),
        ("STOP", "Evidence request · do not deploy"),
    ]
    for index, (label, note) in enumerate(terminals):
        x = 64 + index * 267
        body.extend(
            [
                text(x, 548, label, css="micro", fill=NAVY),
                text(x, 571, note, css="small", fill=INK_SOFT),
            ]
        )
    return svg_document(
        "Adaptive reporting is a routing system, not a fixed template",
        "Stable evidence discipline; case-specific fields, methods, figures, and terminal status",
        "\n".join(body),
        height=650,
        description=(
            "Question, evidence, and decision maturity enter an adaptive router. "
            "The router creates a primary evidence report and only when justified "
            "a conditional decision brief, with valid stopping outcomes."
        ),
        accent=VIOLET,
        kicker="ADAPTIVE ANALYTICS ARCHITECTURE",
        source="Source: High-Stakes Analytics & Decision Lab routing contract",
        note="Route first · adapt the schema · preserve the evidence boundary",
    )


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    assets = {
        "readme-hero.svg": hero_svg(),
        "report-layers.svg": report_layers_svg(),
        "adaptive-reporting-system.svg": adaptive_system_svg(),
    }
    for name, markup in assets.items():
        (ASSET_DIR / name).write_text(markup, encoding="utf-8")
    print(f"Wrote {len(assets)} README visuals to {ASSET_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
