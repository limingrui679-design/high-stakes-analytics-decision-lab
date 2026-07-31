#!/usr/bin/env python3
"""Route one question into descriptive, predictive, and prescriptive analysis."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

ROUTER_VERSION = "1.1.0"

MODE_LABELS = {
    "descriptive": "Descriptive analytics",
    "diagnostic": "Diagnostic bridge",
    "predictive": "Predictive analytics",
    "prescriptive": "Prescriptive analytics",
}

KEYWORDS = {
    "descriptive": (
        "what happened",
        "what is happening",
        "current",
        "historical",
        "trend",
        "summary",
        "summarize",
        "compare",
        "distribution",
        "how many",
        "发生了什么",
        "目前",
        "现状",
        "历史",
        "趋势",
        "描述",
        "总结",
        "比较",
        "对比",
        "分布",
        "多少",
    ),
    "diagnostic": (
        "why",
        "driver",
        "cause",
        "reason",
        "root cause",
        "explain",
        "explanation",
        "explain the change",
        "为什么",
        "原因",
        "驱动因素",
        "归因",
        "诊断",
    ),
    "predictive": (
        "predict",
        "forecast",
        "likely",
        "likelihood",
        "probability",
        "risk of",
        "will",
        "next",
        "future",
        "scenario",
        "预测",
        "预估",
        "未来",
        "接下来",
        "概率",
        "风险",
        "情景",
    ),
    "prescriptive": (
        "should",
        "recommend",
        "choose",
        "select",
        "allocate",
        "optimize",
        "strategy",
        "decision",
        "trade-off",
        "constraint",
        "how should",
        "what action",
        "which option",
        "which policy",
        "which strategy",
        "best action",
        "minimize",
        "maximize",
        "compare alternatives",
        "怎么办",
        "应该",
        "应该如何",
        "如何选择",
        "如何分配",
        "如何优化",
        "如何提高",
        "如何降低",
        "如何改进",
        "采取什么",
        "哪种方案",
        "哪项政策",
        "哪种策略",
        "最优方案",
        "最小化",
        "最大化",
        "推荐",
        "选择",
        "分配",
        "优化",
        "策略",
        "决策",
        "权衡",
        "约束",
    ),
}

LENSES: dict[str, dict[str, Any]] = {
    "descriptive": {
        "question": "What is happening, to whom, where, and over time?",
        "purpose": "Establish a trustworthy baseline before modeling the future or recommending action.",
        "methods": [
            "Metric and denominator definition",
            "Trend, cohort, segment, and distribution analysis",
            "Missingness, representativeness, and outlier review",
            "Observed group-gap and process-funnel description",
        ],
        "minimum_data": [
            "Unit of analysis and population",
            "Timestamp or period",
            "Outcome, exposure, and denominator fields",
            "Relevant segment or affected-group fields",
        ],
        "visuals": [
            "KPI scorecard",
            "Time trend",
            "Distribution or funnel",
            "Segment heatmap",
        ],
        "validity_checks": [
            "Stable metric definitions and comparable periods",
            "Complete denominators and explicit exclusions",
            "No causal language from descriptive differences",
        ],
        "handoff": "Produces the baseline, segments, and evidence-quality constraints needed downstream.",
    },
    "predictive": {
        "question": "What is likely to happen next, and how uncertain is it?",
        "purpose": "Estimate future outcomes or scenario consequences without converting prediction into causation.",
        "methods": [
            "Naive and domain-relevant baseline comparison",
            "Time-aware train, validation, and test design",
            "Forecasting, risk modeling, or scenario simulation",
            "Calibration and uncertainty-interval assessment",
        ],
        "minimum_data": [
            "Defined target outcome and forecast horizon",
            "Historical outcomes at the intended prediction grain",
            "Predictors available at decision time",
            "Intervention, policy, or external-scenario assumptions",
        ],
        "visuals": [
            "Forecast with uncertainty band",
            "Calibration or residual diagnostic",
            "Error by segment",
            "Scenario fan or risk distribution",
        ],
        "validity_checks": [
            "Out-of-sample evaluation against a simple baseline",
            "Leakage, drift, and temporal-order checks",
            "Calibration and subgroup error review",
        ],
        "handoff": "Supplies outcome distributions and uncertainty for each feasible alternative or scenario.",
    },
    "prescriptive": {
        "question": "What should be done—and how—under the stated objectives and constraints?",
        "purpose": "Compare actions by combining evidence with explicit values, feasibility, risk, and distributional effects.",
        "methods": [
            "Alternative and status-quo definition",
            "Multi-criteria value and hard-constraint modeling",
            "Monte Carlo, scenario, tail-risk, and Pareto analysis",
            "Weight sensitivity and affected-group review",
        ],
        "minimum_data": [
            "Decision owner, alternatives, and time horizon",
            "Objectives, weights, and fixed value scales",
            "Budget, safety, legal, or operational constraints",
            "Predicted or causal outcome distributions by alternative",
        ],
        "visuals": [
            "Decision scorecard and ranking",
            "Risk and uncertainty intervals",
            "Scenario and sensitivity views",
            "Group-impact diagnostics",
        ],
        "validity_checks": [
            "Feasibility before ranking",
            "Expected value shown beside tail risk",
            "Prediction, causal evidence, and value judgments kept separate",
        ],
        "handoff": "Produces a recommendation, conditions for reversal, monitoring triggers, and next evidence.",
    },
}

DIAGNOSTIC_BRIDGE = {
    "question": "Why did the observed pattern occur?",
    "role": "An optional bridge between description and prediction.",
    "methods": [
        "Segment decomposition and contribution analysis",
        "Process or funnel diagnostics",
        "Hypothesis-driven root-cause checks",
        "Causal design only when intervention effects are claimed",
    ],
    "guardrail": (
        "A correlated driver is not automatically a cause. State the identification "
        "strategy before using causal language."
    ),
}


def _matched_signals(text: str) -> dict[str, list[str]]:
    lowered = text.casefold()
    return {
        mode: [keyword for keyword in keywords if keyword.casefold() in lowered]
        for mode, keywords in KEYWORDS.items()
    }


def build_blueprint(
    question: str,
    *,
    context: str = "",
    scope: str = "full",
) -> dict[str, Any]:
    """Build a machine-readable analysis blueprint from a natural-language question."""

    normalized = " ".join(question.split())
    if not normalized:
        raise ValueError("question must be non-empty")
    if scope not in {"auto", "full"}:
        raise ValueError("scope must be 'auto' or 'full'")

    signals = _matched_signals(f"{normalized} {context}")
    scores = {mode: len(items) for mode, items in signals.items()}
    # Explicit action questions take precedence, then explicit "why/explain"
    # questions. This prevents domain nouns such as "risk" from turning a
    # diagnostic question ("Why did a high-risk group decline?") into a
    # forecast request when both modes receive one lexical match.
    priority = ("prescriptive", "diagnostic", "predictive", "descriptive")
    primary = max(priority, key=lambda mode: (scores[mode], -priority.index(mode)))
    top_score = scores[primary]
    tied_modes = [mode for mode in priority if scores[mode] == top_score and top_score > 0]
    if top_score == 0:
        primary = "descriptive"
        routing_confidence = "low"
        ambiguous = True
    elif len(tied_modes) > 1:
        routing_confidence = "medium"
        ambiguous = True
    else:
        routing_confidence = "high" if top_score >= 2 else "medium"
        ambiguous = False

    if scope == "full":
        execution_order = ["descriptive", "predictive", "prescriptive"]
    else:
        execution_order = {
            "descriptive": ["descriptive"],
            "diagnostic": ["descriptive", "diagnostic"],
            "predictive": ["descriptive", "predictive"],
            "prescriptive": ["descriptive", "predictive", "prescriptive"],
        }[primary]

    primary_signals = signals[primary]
    reason = (
        f"Detected {MODE_LABELS[primary].lower()} cues: "
        + ", ".join(f"“{item}”" for item in primary_signals[:5])
        + "."
        if primary_signals
        else "No explicit analytical cue was detected, so the router starts with a descriptive baseline."
    )
    if len(tied_modes) > 1:
        reason += (
            " Multiple modes received equal cue scores; the higher-action mode is "
            "shown as primary while the full cue set remains visible."
        )

    analysis_lenses = []
    for mode in ("descriptive", "predictive", "prescriptive"):
        lens = dict(LENSES[mode])
        lens.update(
            {
                "id": mode,
                "label": MODE_LABELS[mode],
                "status": "required" if mode in execution_order else "optional",
            }
        )
        analysis_lenses.append(lens)

    return {
        "schema_version": "1.0",
        "router_version": ROUTER_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "question": normalized,
        "context": context.strip(),
        "data_status": "not_supplied",
        "routing": {
            "primary_mode": primary,
            "primary_label": MODE_LABELS[primary],
            "scope": scope,
            "execution_order": execution_order,
            "confidence": routing_confidence,
            "ambiguous": ambiguous,
            "alternate_modes": [
                mode for mode in priority if mode != primary and scores[mode] > 0
            ],
            "diagnostic_bridge_recommended": bool(signals["diagnostic"]),
            "signals": signals,
            "reason": reason,
        },
        "analysis_lenses": analysis_lenses,
        "diagnostic_bridge": DIAGNOSTIC_BRIDGE,
        "minimum_inputs": [
            "Decision owner or intended reader",
            "Population, unit of analysis, geography, and time window",
            "Outcome definitions, denominators, and source provenance",
            "Prediction target and horizon, if forecasting is required",
            "Alternatives, constraints, and objectives, if a recommendation is required",
            "Affected groups and harms that averages may hide",
        ],
        "handoff_to_decision_model": {
            "alternatives": "At least a status quo and one actionable alternative",
            "criteria": "Benefits, costs, risks, implementation, evidence quality, and material distributional outcomes",
            "constraints": "Hard budget, safety, legal, capacity, or service thresholds",
            "scenarios": "Plausible external states with transparent probabilities or non-probabilistic stress cases",
            "uncertainty": "Outcome distributions or intervals, with dependence assumptions disclosed",
            "values": "Stakeholder weights and fixed worst-to-best reference scales",
        },
        "guardrails": [
            "With no data, deliver a blueprint—not fabricated findings.",
            "Treat keyword routing as a reviewable planning aid, not proof of user intent; revise the route when context contradicts it.",
            "A prediction estimates likely outcomes; it does not identify the effect of an intervention.",
            "Use causal language only with a defensible identification strategy.",
            "A prescriptive recommendation combines empirical evidence with explicit values and constraints.",
            "If required inputs are missing or every alternative is infeasible, state that no decision-ready recommendation exists.",
        ],
    }


def _wrap(text: str, width: int) -> list[str]:
    words: list[str] = []
    for token in text.split():
        if len(token) <= width:
            words.append(token)
        else:
            words.extend(token[index : index + width] for index in range(0, len(token), width))
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _svg_text(
    x: float,
    y: float,
    value: str,
    *,
    size: int = 16,
    weight: int = 400,
    fill: str = "#172033",
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="-apple-system,BlinkMacSystemFont,'
        f'&quot;Segoe UI&quot;,Arial,sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
        f"{escape(value)}</text>"
    )


def render_blueprint_svg(blueprint: dict[str, Any]) -> str:
    """Render an accessible executive blueprint for the three analysis lenses."""

    width, height = 1400, 720
    ink, muted, grid = "#0B1324", "#617084", "#D9E2EC"
    navy, navy_2, canvas, white = "#0B1F3A", "#13345B", "#F3F6FA", "#FFFFFF"
    colors = ["#00A69A", "#8168E8", "#E0AA2B"]
    light_colors = ["#DDF5F2", "#EEEAFE", "#FFF2C7"]
    question_lines = _wrap(blueprint["question"], 92)[:2]
    primary_label = blueprint["routing"]["primary_label"]
    execution_order = blueprint["routing"]["execution_order"]
    if blueprint.get("data_status") == "profiled":
        readiness = blueprint.get("data_readiness", {})
        footer_status = (
            "Data profiled"
            + (
                f" · quality gate {readiness['status']}"
                if readiness.get("status")
                else ""
            )
            + " · routing aid only · no empirical finding or recommendation"
        )
    else:
        footer_status = (
            "No data supplied → blueprint only · no empirical finding · "
            "no forecast · no recommendation"
        )
    body: list[str] = [
        f'<rect width="{width}" height="{height}" rx="22" fill="{canvas}"/>',
        f'<rect width="{width}" height="180" rx="22" fill="{navy}"/>',
        f'<rect y="158" width="{width}" height="22" fill="{navy}"/>',
        f'<rect width="10" height="180" fill="{colors[0]}"/>',
        _svg_text(48, 42, "ANALYTICS ROUTER · EXECUTIVE BLUEPRINT", size=11, weight=800, fill=colors[0]),
        _svg_text(48, 86, "One question. Three evidence lenses. One decision path.", size=34, weight=780, fill=white),
    ]
    for index, line in enumerate(question_lines):
        prefix = "“" if index == 0 else ""
        suffix = "”" if index == len(question_lines) - 1 else ""
        body.append(_svg_text(48, 123 + index * 23, f"{prefix}{line}{suffix}", size=16, fill="#C7D4E4"))
    body.extend(
        [
            f'<rect x="1120" y="42" width="228" height="78" rx="14" fill="{navy_2}" stroke="#31516F"/>',
            _svg_text(1140, 68, "PRIMARY MODE", size=10, weight=800, fill="#8EA5BD"),
            _svg_text(1140, 99, primary_label, size=19, weight=760, fill=white),
            f'<circle cx="1313" cy="81" r="16" fill="{colors[0]}"/>',
            f'<path d="M 1306 81 L 1311 86 L 1321 75" fill="none" stroke="{navy}" stroke-width="2.5"/>',
        ]
    )

    card_y, card_width, gap = 216, 402, 38
    card_xs = [48, 48 + card_width + gap, 48 + (card_width + gap) * 2]
    summaries = [
        ("descriptive", "01", "DESCRIPTIVE", "What is happening?", "Baseline · trend · segments", "Observed evidence"),
        ("predictive", "02", "PREDICTIVE", "What may happen next?", "Forecast · calibration · risk", "Modeled evidence"),
        ("prescriptive", "03", "PRESCRIPTIVE", "What should be done?", "Options · constraints · values", "Decision layer"),
    ]
    for index, (mode, number, label, question, methods, evidence) in enumerate(summaries):
        x = card_xs[index]
        required = mode in execution_order
        body.extend(
            [
                f'<rect x="{x}" y="{card_y}" width="{card_width}" height="284" rx="18" '
                f'fill="{white}" stroke="{colors[index] if required else grid}" stroke-width="{2.5 if required else 1}"/>',
                f'<rect x="{x}" y="{card_y}" width="8" height="284" rx="4" fill="{colors[index]}"/>',
                f'<circle cx="{x + 48}" cy="{card_y + 48}" r="24" fill="{colors[index]}"/>',
                _svg_text(x + 48, card_y + 54, number, size=12, weight=800, fill=white, anchor="middle"),
                _svg_text(x + 86, card_y + 42, label, size=12, weight=800, fill=colors[index]),
                _svg_text(x + 86, card_y + 66, evidence, size=12, fill=muted),
                _svg_text(x + 25, card_y + 124, question, size=22, weight=760, fill=ink),
                f'<rect x="{x + 25}" y="{card_y + 151}" width="{card_width - 50}" height="48" rx="9" fill="{light_colors[index]}"/>',
                _svg_text(x + 42, card_y + 181, methods, size=13, weight=680, fill=ink),
                _svg_text(x + 25, card_y + 230, "COMPLETION GATE", size=9, weight=800, fill=muted),
                _svg_text(
                    x + 25,
                    card_y + 258,
                    "Required in this path" if required else "Available when needed",
                    size=13,
                    weight=720,
                    fill=colors[index] if required else muted,
                ),
                f'<circle cx="{x + card_width - 30}" cy="{card_y + 251}" r="9" fill="{colors[index] if required else white}" stroke="{colors[index]}"/>',
            ]
        )
        if required:
            body.append(f'<path d="M {x + card_width - 34} {card_y + 251} L {x + card_width - 31} {card_y + 255} L {x + card_width - 25} {card_y + 247}" fill="none" stroke="{white}" stroke-width="1.6"/>')
        if index < 2:
            arrow_x = x + card_width + 8
            body.extend(
                [
                    f'<line x1="{arrow_x}" y1="{card_y + 140}" x2="{arrow_x + 20}" y2="{card_y + 140}" stroke="#9CB0C5" stroke-width="2"/>',
                    f'<path d="M {arrow_x + 15} {card_y + 134} L {arrow_x + 24} {card_y + 140} L {arrow_x + 15} {card_y + 146}" fill="none" stroke="#9CB0C5" stroke-width="2"/>',
                ]
            )

    body.extend(
        [
            f'<rect x="48" y="536" width="1304" height="110" rx="15" fill="{white}" stroke="{grid}"/>',
            f'<rect x="48" y="536" width="8" height="110" rx="4" fill="#E06950"/>',
            _svg_text(76, 567, "OPTIONAL DIAGNOSTIC BRIDGE", size=10, weight=800, fill="#B34E39"),
            _svg_text(76, 601, "Why did the pattern occur?", size=19, weight=740, fill=ink),
            _svg_text(395, 590, "Decomposition and root-cause hypotheses may guide investigation.", size=14, fill=muted),
            _svg_text(395, 614, "A causal claim still requires an identification strategy.", size=14, weight=650, fill="#B34E39"),
            f'<rect x="1068" y="558" width="252" height="52" rx="12" fill="#FCE7E2"/>',
            _svg_text(1194, 580, "DO NOT SKIP", size=9, weight=800, fill="#A63C2A", anchor="middle"),
            _svg_text(1194, 600, "causal-evidence guardrail", size=12, weight=700, fill="#A63C2A", anchor="middle"),
            f'<line x1="48" y1="678" x2="1352" y2="678" stroke="{grid}"/>',
            _svg_text(48, 703, footer_status, size=11, fill=muted),
            _svg_text(1352, 703, "Source: routing blueprint JSON", size=11, fill="#8B98A9", anchor="end"),
        ]
    )
    description = (
        "A three-stage analytics workflow moves from descriptive evidence to predictive "
        "estimates and prescriptive decisions, with an optional diagnostic bridge."
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Question-to-analysis routing blueprint</title>
<desc id="desc">{escape(description)}</desc>
{''.join(body)}
</svg>
"""


def render_blueprint_report(blueprint: dict[str, Any]) -> str:
    routing = blueprint["routing"]
    if blueprint.get("data_status") == "profiled":
        readiness = blueprint.get("data_readiness", {})
        rows = readiness.get("rows")
        columns = readiness.get("columns")
        shape = (
            f" ({rows:,} rows × {columns:,} columns)"
            if isinstance(rows, int) and isinstance(columns, int)
            else ""
        )
        status = readiness.get("status", "not recorded")
        data_note = (
            f"> A dataset was profiled{shape}; its quality gate is `{status}`. "
            "This document remains a planning blueprint, not an empirical finding, "
            "forecast, or recommendation."
        )
    else:
        data_note = (
            "> No dataset was supplied. This document is an analysis blueprint, not an "
            "empirical finding, forecast, or recommendation."
        )
    lines = [
        "# Question-to-Analysis Blueprint",
        "",
        f"> **Question:** {blueprint['question']}",
        "",
        "![Three analytics lenses](figures/analytics-lifecycle.svg)",
        "",
        "## Routing decision",
        "",
        f"- **Primary mode:** {routing['primary_label']}",
        f"- **Routing confidence:** {routing['confidence']} "
        f"({'ambiguous or mixed' if routing['ambiguous'] else 'clear cue lead'})",
        f"- **Execution scope:** {routing['scope']}",
        "- **Execution order:** "
        + " → ".join(MODE_LABELS[mode] for mode in routing["execution_order"]),
        f"- **Why:** {routing['reason']}",
        "",
        data_note,
        "",
    ]
    for index, lens in enumerate(blueprint["analysis_lenses"], start=1):
        lines.extend(
            [
                f"## {index}. {lens['label']}: {lens['question']}",
                "",
                f"**Role:** {lens['purpose']}",
                "",
                "| Component | Blueprint |",
                "|---|---|",
                "| Methods | " + "; ".join(lens["methods"]) + " |",
                "| Minimum data | " + "; ".join(lens["minimum_data"]) + " |",
                "| Recommended visuals | " + "; ".join(lens["visuals"]) + " |",
                "| Validity checks | " + "; ".join(lens["validity_checks"]) + " |",
                "",
                f"**Handoff:** {lens['handoff']}",
                "",
            ]
        )
    diagnostic = blueprint["diagnostic_bridge"]
    lines.extend(
        [
            "## Optional diagnostic bridge: why did the pattern occur?",
            "",
            diagnostic["role"],
            "",
        ]
    )
    lines.extend(f"- {method}" for method in diagnostic["methods"])
    lines.extend(
        [
            "",
            f"**Guardrail:** {diagnostic['guardrail']}",
            "",
            "## Minimum input checklist",
            "",
        ]
    )
    lines.extend(f"- [ ] {item}" for item in blueprint["minimum_inputs"])
    lines.extend(
        [
            "",
            "## Evidence-to-decision contract",
            "",
            "| Decision-model input | Required definition |",
            "|---|---|",
        ]
    )
    lines.extend(
        f"| {key.replace('_', ' ').title()} | {value} |"
        for key, value in blueprint["handoff_to_decision_model"].items()
    )
    lines.extend(["", "## Guardrails", ""])
    lines.extend(f"- {item}" for item in blueprint["guardrails"])
    lines.extend(
        [
            "",
            f"*Generated by question router {blueprint['router_version']}.*",
            "",
        ]
    )
    return "\n".join(lines)


def write_blueprint(
    blueprint: dict[str, Any],
    output_dir: str | Path,
) -> tuple[Path, Path, Path]:
    output_path = Path(output_dir)
    figures_dir = output_path / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "analysis-blueprint.json"
    report_path = output_path / "analysis-blueprint.md"
    figure_path = figures_dir / "analytics-lifecycle.svg"
    json_path.write_text(
        json.dumps(blueprint, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_blueprint_report(blueprint), encoding="utf-8")
    figure_path.write_text(render_blueprint_svg(blueprint), encoding="utf-8")
    return json_path, report_path, figure_path
