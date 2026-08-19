#!/usr/bin/env python3
"""Generate accessible, production-grade SVG figures for decision reports."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from visual_system import (
    CANVAS,
    CORAL,
    DANGER,
    DANGER_TINT,
    GOLD,
    GRID,
    GRID_DARK,
    INK,
    INK_SOFT,
    MUTED,
    NAVY,
    PAPER,
    SUCCESS,
    SUCCESS_TINT,
    WARNING,
    WARNING_TINT,
    WIDTH,
    categorical_colors,
    path_donut,
    pill,
    progress_bar,
    rounded_rect,
    score_tint,
    svg_document,
    text,
    theme_for,
    wrapped_text,
)


def _criterion_score(value: float, criterion: dict[str, Any]) -> float:
    worst = float(criterion["scale"]["worst"])
    best = float(criterion["scale"]["best"])
    if criterion["direction"] == "maximize":
        score = (value - worst) / (best - worst)
    else:
        score = (worst - value) / (worst - best)
    return min(1.0, max(0.0, score))


def _theme(result: dict[str, Any]) -> tuple[str, str, str]:
    return theme_for(result["decision"]["domain"])


def _breach_display(summary: dict[str, Any]) -> tuple[str, str]:
    count = int(summary["constraint_violation_count"])
    samples = int(summary["constraint_sample_count"])
    observed = float(summary["constraint_violation_rate"])
    upper = float(summary["constraint_violation_rate_upper_95"])
    status = {
        "declared_support_excludes_breach": "bounded support",
        "modeled_tail_crosses_threshold": "tail crosses",
        "unbounded_tail": "unbounded tail",
    }[summary["constraint_support_status"]]
    value = "0 observed" if count == 0 else f"{observed:.1%}"
    return value, f"{count:,}/{samples:,} · U95 {upper:.2%} · {status}"


def _alternative_colors(result: dict[str, Any]) -> dict[str, str]:
    return categorical_colors(
        result["decision"]["ranking"],
        preferred=result["decision"]["recommendation"],
        accent=_theme(result)[0],
    )


def _status_colors(status: str) -> tuple[str, str]:
    if status == "decision_ready":
        return SUCCESS_TINT, SUCCESS
    if status == "illustrative_preference":
        return WARNING_TINT, WARNING
    return DANGER_TINT, DANGER


def _axis(
    body: list[str],
    *,
    left: float,
    right: float,
    top: float,
    bottom: float,
    labels: list[tuple[float, str]],
) -> None:
    for value, label in labels:
        x = left + (right - left) * value
        body.append(
            f'<line x1="{x:.1f}" y1="{top:.1f}" x2="{x:.1f}" y2="{bottom:.1f}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        body.append(text(x, bottom + 22, label, css="small", anchor="middle"))


def _decision_scorecard(result: dict[str, Any]) -> str:
    decision = result["decision"]
    alternatives = result["alternatives"]
    recommendation_id = decision["recommendation"]
    recommendation = alternatives[recommendation_id] if recommendation_id else None
    accent, accent_dark, accent_tint = _theme(result)
    status_fill, status_ink = _status_colors(decision["decision_status"])
    body: list[str] = []

    # Dominant answer panel
    body.append(rounded_rect(36, 134, 540, 214, fill=NAVY, stroke=NAVY, radius=18))
    body.append(text(62, 165, "MODELED DECISION", css="kicker", fill=accent))
    if recommendation:
        body.append(
            wrapped_text(
                62,
                210,
                recommendation["label"],
                chars=31,
                line_height=31,
                css="display",
                fill=PAPER,
            )
        )
        badge, _ = pill(
            62,
            292,
            decision["decision_status_label"],
            fill=status_fill,
            foreground=status_ink,
        )
        body.append(badge)
        body.append(text(62, 331, "Highest-ranked option that passes the modeled risk rule", css="small", fill="#C7D4E4"))
    else:
        body.append(text(62, 222, "No feasible option", css="display", fill=PAPER))
        body.append(text(62, 262, "Revise the alternatives or constraints before commitment", css="label", fill="#C7D4E4"))

    cards = [
        (
            "DECISION VALUE",
            f"{recommendation['value_score']:.1f}" if recommendation else "—",
            "of 100 · downside adjusted",
        ),
        (
            "MODELED P(BEST)",
            f"{recommendation['probability_best']:.0%}" if recommendation else "—",
            f"feasible set · {result['metadata']['samples']:,} draws",
        ),
        (
            "ROBUSTNESS",
            f"{decision['robustness_score']:.0f}" if recommendation else "—",
            "diagnostic · not confidence",
        ),
    ]
    card_width = 180
    for index, (label, value, note) in enumerate(cards):
        x = 596 + index * 190
        body.append(rounded_rect(x, 134, card_width, 214, fill=PAPER, stroke=GRID, radius=16))
        body.append(text(x + 18, 166, label, css="eyebrow"))
        body.append(text(x + 18, 222, value, css="display", fill=accent_dark if index == 0 else INK))
        body.append(
            wrapped_text(x + 18, 272, note, chars=20, line_height=17, css="small")
        )
        body.append(progress_bar(x + 18, 315, card_width - 36, (
            recommendation["value_score"] / 100 if index == 0 and recommendation
            else recommendation["probability_best"] if index == 1 and recommendation
            else decision["robustness_score"] / 100 if recommendation else 0
        ), color=accent))

    # Constraint U95 versus tolerance
    body.append(rounded_rect(36, 366, 1128, 102, fill=PAPER, stroke=GRID, radius=16))
    body.append(text(58, 396, "CONSTRAINT RISK BOUNDARY", css="eyebrow"))
    tolerance = float(decision["max_constraint_violation_rate"])
    if recommendation:
        observed = float(recommendation["constraint_violation_rate"])
        upper = float(recommendation["constraint_violation_rate_upper_95"])
        scale = max(0.01, tolerance * 1.35, upper * 1.2, observed * 1.2)
        chart_left, chart_width = 322, 616
        tolerance_x = chart_left + chart_width * tolerance / scale
        observed_x = chart_left + chart_width * observed / scale
        upper_x = chart_left + chart_width * upper / scale
        body.append(text(58, 432, _breach_display(recommendation)[0], css="section"))
        body.append(text(58, 454, _breach_display(recommendation)[1], css="small"))
        body.append(
            f'<line x1="{chart_left}" y1="423" x2="{chart_left + chart_width}" y2="423" '
            f'stroke="{GRID_DARK}" stroke-width="9" stroke-linecap="round"/>'
        )
        body.append(
            f'<line x1="{chart_left}" y1="423" x2="{upper_x:.1f}" y2="423" '
            f'stroke="{accent}" stroke-width="9" stroke-linecap="round"/>'
        )
        body.append(f'<circle cx="{observed_x:.1f}" cy="423" r="7" fill="{NAVY}" stroke="{PAPER}" stroke-width="2"/>')
        body.append(
            f'<path d="M {upper_x:.1f} 414 L {upper_x + 9:.1f} 423 L {upper_x:.1f} 432 '
            f'L {upper_x - 9:.1f} 423 Z" fill="{accent}" stroke="{NAVY}"/>'
        )
        body.append(
            f'<line x1="{tolerance_x:.1f}" y1="397" x2="{tolerance_x:.1f}" y2="450" '
            f'stroke="{DANGER}" stroke-width="2" stroke-dasharray="5 4"/>'
        )
        body.append(text(tolerance_x, 389, f"tolerance {tolerance:.1%}", css="small", anchor="middle", fill=DANGER))
        body.append(text(963, 417, "PASS" if recommendation["feasible"] else "FAIL", css="section", fill=SUCCESS if recommendation["feasible"] else DANGER))
        body.append(text(963, 441, "U95 is inside tolerance" if recommendation["feasible"] else "U95 exceeds tolerance", css="small"))
    else:
        body.append(text(58, 435, "Every option exceeds the configured risk boundary.", css="section", fill=DANGER))

    return svg_document(
        "Decision summary",
        "One answer, four diagnostics, and the risk boundary that governs feasibility",
        "\n".join(body),
        height=510,
        accent=accent,
        description=(
            "Executive scorecard showing the preferred modeled alternative, decision value, "
            "probability of being best, robustness, and constraint-breach upper bound versus tolerance."
        ),
    )


def _robustness_profile(result: dict[str, Any]) -> str:
    decision = result["decision"]
    components = decision["robustness_components"]
    accent, _, accent_tint = _theme(result)
    status_fill, status_ink = _status_colors(decision["decision_status"])
    labels = {
        "probability_best": ("P(best among feasible)", "How often this option leads"),
        "weight_stability": ("Weight stability", "Survives local value changes"),
        "scenario_stability": ("Scenario stability", "Leads across modeled worlds"),
        "constraint_headroom": ("Constraint headroom", "Distance from risk boundary"),
    }
    body: list[str] = [
        rounded_rect(36, 134, 322, 270, fill=PAPER, stroke=GRID, radius=18),
        path_donut(197, 242, 72, decision["robustness_score"] / 100, color=accent, stroke_width=16),
        text(197, 239, f"{decision['robustness_score']:.0f}", css="display", anchor="middle"),
        text(197, 261, "OF 100", css="eyebrow", anchor="middle"),
    ]
    badge, _ = pill(77, 334, decision["decision_status_label"], fill=status_fill, foreground=status_ink, width=240)
    body.append(badge)
    body.append(text(197, 384, "Model behavior · not real-world confidence", css="small", anchor="middle"))

    row_y = 138
    for key in ("probability_best", "weight_stability", "scenario_stability", "constraint_headroom"):
        component = components[key]
        value = float(component["value"])
        weight = float(component["weight"])
        body.append(rounded_rect(382, row_y, 782, 58, fill=PAPER, stroke=GRID, radius=12))
        body.append(text(402, row_y + 23, labels[key][0], css="section"))
        body.append(text(402, row_y + 43, labels[key][1], css="small"))
        body.append(progress_bar(690, row_y + 24, 320, value, color=accent, marker=0.75))
        body.append(text(1030, row_y + 29, f"{value:.0%}", css="value"))
        chip, _ = pill(1083, row_y + 15, f"w {weight:.0%}", fill=accent_tint, foreground=accent, width=62)
        body.append(chip)
        row_y += 68
    body.append(text(382, 430, "Reference marker = 75% diagnostic threshold · component weights sum to 100%", css="small"))

    return svg_document(
        "Decision robustness profile",
        "Transparent components explain the modeled score and readiness status",
        "\n".join(body),
        height=478,
        accent=accent,
        description=(
            "Donut and bullet bars show probability-best, weight stability, scenario stability, "
            "constraint headroom, their weights, and the overall robustness diagnostic."
        ),
    )


def _alternative_ranking(result: dict[str, Any]) -> str:
    alternatives = result["alternatives"]
    ranking = result["decision"]["ranking"]
    recommendation = result["decision"]["recommendation"]
    accent, accent_dark, accent_tint = _theme(result)
    chart_left, chart_right = 366, 1122
    chart_top, row_height = 160, 88
    height = chart_top + row_height * len(ranking) + 54
    body: list[str] = []
    _axis(
        body,
        left=chart_left,
        right=chart_right,
        top=132,
        bottom=height - 76,
        labels=[(x / 100, f"{x}") for x in range(0, 101, 20)],
    )
    for index, alternative_id in enumerate(ranking):
        summary = alternatives[alternative_id]
        y = chart_top + index * row_height
        is_recommended = alternative_id == recommendation
        if index % 2 == 0:
            body.append(rounded_rect(30, y - 28, 1134, 72, fill=PAPER, stroke="none", radius=9))
        body.append(f'<circle cx="58" cy="{y}" r="17" fill="{accent if is_recommended else NAVY}"/>')
        body.append(text(58, y + 5, str(index + 1), css="pill", anchor="middle", fill=PAPER))
        body.append(
            wrapped_text(
                86,
                y - 4,
                summary["label"],
                chars=31,
                line_height=16,
                css="section" if is_recommended else "label",
            )
        )
        value = float(summary["risk_adjusted_utility"])
        bar_width = max(4, value * (chart_right - chart_left))
        fill = accent if is_recommended else (accent_tint if summary["feasible"] else DANGER_TINT)
        stroke = accent_dark if is_recommended else (accent if summary["feasible"] else DANGER)
        body.append(
            f'<rect x="{chart_left}" y="{y - 15}" width="{bar_width:.1f}" height="30" '
            f'rx="7" fill="{fill}" stroke="{stroke}" stroke-width="{2 if is_recommended else 1}"/>'
        )
        label_x = chart_left + bar_width - 10 if bar_width > 74 else chart_left + bar_width + 8
        label_anchor = "end" if bar_width > 74 else "start"
        label_fill = PAPER if is_recommended and bar_width > 74 else INK
        body.append(text(label_x, y + 5, f"{value * 100:.1f}", css="value", anchor=label_anchor, fill=label_fill))
        status_label = "FEASIBLE" if summary["feasible"] else "RISK FAIL"
        status_fill = SUCCESS_TINT if summary["feasible"] else DANGER_TINT
        status_ink = SUCCESS if summary["feasible"] else DANGER
        status, _ = pill(86, y + 20, status_label, fill=status_fill, foreground=status_ink, width=76)
        body.append(status)
        pbest = f"P(best) {summary['probability_best']:.0%}" if summary["feasible"] else "P(best) n/a"
        body.append(text(174, y + 39, f"{pbest} · U95 {summary['constraint_violation_rate_upper_95']:.2%}", css="small"))

    return svg_document(
        "Alternative ranking",
        "Risk-adjusted decision value · direct ranks, feasibility, P(best), and breach U95",
        "\n".join(body),
        height=height,
        accent=accent,
        description=(
            "Horizontal ranked bars compare risk-adjusted decision value on a zero-to-100 scale. "
            "Labels show feasibility, probability-best, and the breach-frequency upper bound."
        ),
    )


def _constraint_risk(result: dict[str, Any]) -> str:
    alternatives = result["alternatives"]
    ranking = result["decision"]["ranking"]
    recommendation = result["decision"]["recommendation"]
    tolerance = float(result["decision"]["max_constraint_violation_rate"])
    accent, _, accent_tint = _theme(result)
    values = [
        max(
            float(alternatives[item]["constraint_violation_rate"]),
            float(alternatives[item]["constraint_violation_rate_upper_95"]),
        )
        for item in ranking
    ]
    scale = max(0.01, tolerance * 1.35, max(values, default=0) * 1.18)
    chart_left, chart_right = 354, 1080
    chart_top, row_height = 174, 72
    height = chart_top + len(ranking) * row_height + 60
    tolerance_x = chart_left + (chart_right - chart_left) * tolerance / scale
    body: list[str] = []
    ticks = 5
    _axis(
        body,
        left=chart_left,
        right=chart_right,
        top=138,
        bottom=height - 90,
        labels=[(i / ticks, f"{scale * i / ticks:.1%}") for i in range(ticks + 1)],
    )
    body.append(
        f'<line x1="{tolerance_x:.1f}" y1="132" x2="{tolerance_x:.1f}" y2="{height - 90}" '
        f'stroke="{DANGER}" stroke-width="2.5" stroke-dasharray="6 5"/>'
    )
    body.append(text(tolerance_x, 126, f"risk tolerance {tolerance:.1%}", css="small", anchor="middle", fill=DANGER))
    for index, alternative_id in enumerate(ranking):
        summary = alternatives[alternative_id]
        y = chart_top + index * row_height
        observed = float(summary["constraint_violation_rate"])
        upper = float(summary["constraint_violation_rate_upper_95"])
        observed_x = chart_left + (chart_right - chart_left) * observed / scale
        upper_x = chart_left + (chart_right - chart_left) * upper / scale
        is_recommended = alternative_id == recommendation
        if index % 2 == 0:
            body.append(rounded_rect(30, y - 25, 1134, 56, fill=PAPER, stroke="none", radius=8))
        body.append(
            wrapped_text(
                48,
                y + 4,
                summary["label"],
                chars=31,
                line_height=16,
                css="section" if is_recommended else "label",
            )
        )
        color = accent if summary["feasible"] else DANGER
        body.append(
            f'<line x1="{observed_x:.1f}" y1="{y}" x2="{upper_x:.1f}" y2="{y}" '
            f'stroke="{color}" stroke-width="5" stroke-linecap="round"/>'
        )
        body.append(f'<circle cx="{observed_x:.1f}" cy="{y}" r="7" fill="{NAVY}" stroke="{PAPER}" stroke-width="2"/>')
        body.append(
            f'<path d="M {upper_x:.1f} {y - 9:.1f} L {upper_x + 9:.1f} {y:.1f} '
            f'L {upper_x:.1f} {y + 9:.1f} L {upper_x - 9:.1f} {y:.1f} Z" '
            f'fill="{color}" stroke="{NAVY}" stroke-width="1"/>'
        )
        label = f"observed {observed:.1%} · U95 {upper:.2%}"
        body.append(text(min(chart_right - 4, max(chart_left + 12, upper_x + 14)), y - 12, label, css="mono", anchor="end" if upper_x > chart_right - 190 else "start"))
        status, _ = pill(
            1088,
            y - 14,
            "PASS" if summary["feasible"] else "FAIL",
            fill=SUCCESS_TINT if summary["feasible"] else DANGER_TINT,
            foreground=SUCCESS if summary["feasible"] else DANGER,
            width=62,
        )
        body.append(status)
    body.append(text(354, height - 34, "● observed breach rate   ◆ one-sided 95% upper bound", css="small"))
    return svg_document(
        "Constraint risk boundary",
        "Feasibility is determined by the conservative upper bound—not the observed rate alone",
        "\n".join(body),
        height=height,
        accent=accent,
        description=(
            "Interval markers compare each alternative's observed constraint-breach rate and "
            "one-sided 95 percent upper bound with the configured risk tolerance."
        ),
    )


def _uncertainty_plot(result: dict[str, Any]) -> str:
    alternatives = result["alternatives"]
    ranking = result["decision"]["ranking"]
    recommendation = result["decision"]["recommendation"]
    accent, _, accent_tint = _theme(result)
    chart_left, chart_right = 342, 1034
    chart_top, row_height = 176, 72
    height = chart_top + len(ranking) * row_height + 62
    body: list[str] = []
    _axis(
        body,
        left=chart_left,
        right=chart_right,
        top=136,
        bottom=height - 84,
        labels=[(x / 10, f"{x / 10:.1f}") for x in range(0, 11, 2)],
    )
    body.append(text(342, 126, "P05", css="small"))
    body.append(text(1034, 126, "P95", css="small", anchor="end"))
    for index, alternative_id in enumerate(ranking):
        summary = alternatives[alternative_id]
        y = chart_top + index * row_height
        is_recommended = alternative_id == recommendation
        if index % 2 == 0:
            body.append(rounded_rect(30, y - 26, 1134, 58, fill=PAPER, stroke="none", radius=8))
        body.append(
            wrapped_text(48, y + 4, summary["label"], chars=30, line_height=16, css="section" if is_recommended else "label")
        )
        x_low = chart_left + float(summary["utility_p05"]) * (chart_right - chart_left)
        x_high = chart_left + float(summary["utility_p95"]) * (chart_right - chart_left)
        x_mean = chart_left + float(summary["expected_utility"]) * (chart_right - chart_left)
        x_cvar = chart_left + float(summary["cvar10"]) * (chart_right - chart_left)
        color = accent if is_recommended else INK_SOFT
        body.append(
            f'<rect x="{x_low:.1f}" y="{y - 7:.1f}" width="{max(2, x_high - x_low):.1f}" '
            f'height="14" rx="7" fill="{accent_tint if is_recommended else "#E1E7EE"}"/>'
        )
        body.append(
            f'<line x1="{x_low:.1f}" y1="{y}" x2="{x_high:.1f}" y2="{y}" '
            f'stroke="{color}" stroke-width="2"/>'
        )
        body.append(f'<circle cx="{x_mean:.1f}" cy="{y}" r="8" fill="{color}" stroke="{PAPER}" stroke-width="2"/>')
        body.append(
            f'<path d="M {x_cvar:.1f} {y - 8:.1f} L {x_cvar + 8:.1f} {y:.1f} '
            f'L {x_cvar:.1f} {y + 8:.1f} L {x_cvar - 8:.1f} {y:.1f} Z" fill="{GOLD}" stroke="{NAVY}"/>'
        )
        body.append(text(1052, y - 5, f"mean {summary['expected_utility']:.3f}", css="mono"))
        body.append(text(1052, y + 15, f"CVaR10 {summary['cvar10']:.3f}", css="small"))
    body.append(text(342, height - 34, "● expected utility   ◆ worst-decile average   band = P05–P95", css="small"))
    return svg_document(
        "Utility uncertainty and downside",
        "Expected value is shown beside overlap and the average of the worst 10% of outcomes",
        "\n".join(body),
        height=height,
        accent=accent,
        description=(
            "Dot and interval plot comparing P05 to P95 utility, expected utility, and "
            "the average of the worst ten percent of simulated outcomes."
        ),
    )


def _correlation_stress(result: dict[str, Any]) -> str:
    diagnostic = result["correlation_sensitivity"]
    recommendation_id = result["decision"]["recommendation"]
    alternatives = result["alternatives"]
    accent, _, accent_tint = _theme(result)
    modes = [
        (
            "INDEPENDENT",
            "No shared residual shocks",
            diagnostic["independent_baseline"],
        ),
        (
            "DECLARED",
            "Declared factor loadings",
            diagnostic["declared_correlation"],
        ),
        (
            "CORRELATION STRESS",
            f"Loadings × {diagnostic['stress_multiplier']:.2f}",
            diagnostic["correlation_stress"],
        ),
    ]
    body: list[str] = []
    card_width = 354
    for index, (label, note, mode) in enumerate(modes):
        x = 36 + index * 382
        preferred_id = mode["recommendation"]
        preferred_label = (
            alternatives[preferred_id]["label"] if preferred_id else "No feasible option"
        )
        metric_id = recommendation_id or preferred_id
        metrics = mode["alternatives"].get(metric_id, {}) if metric_id else {}
        card_fill = accent_tint if index == 1 else PAPER
        card_stroke = accent if index == 1 else GRID
        body.append(
            rounded_rect(
                x,
                136,
                card_width,
                318,
                fill=card_fill,
                stroke=card_stroke,
                radius=17,
                stroke_width=2 if index == 1 else 1,
            )
        )
        body.append(text(x + 22, 169, label, css="eyebrow", fill=accent if index == 1 else None))
        body.append(text(x + 22, 194, note, css="small"))
        body.append(
            wrapped_text(
                x + 22,
                228,
                preferred_label,
                chars=31,
                line_height=20,
                css="section",
            )
        )
        if metrics:
            p_best = float(metrics["probability_best"])
            cvar = float(metrics["cvar10"])
            upper = float(metrics["constraint_violation_rate_upper_95"])
            body.append(text(x + 22, 294, "P(BEST)", css="eyebrow"))
            body.append(text(x + 326, 298, f"{p_best:.0%}", css="value", anchor="end"))
            body.append(progress_bar(x + 22, 310, 304, p_best, color=accent))
            body.append(text(x + 22, 356, "CVaR10", css="eyebrow"))
            body.append(text(x + 326, 358, f"{cvar:.3f}", css="value", anchor="end"))
            body.append(text(x + 22, 397, "BREACH U95", css="eyebrow"))
            body.append(text(x + 326, 399, f"{upper:.1%}", css="value", anchor="end"))
            status, _ = pill(
                x + 22,
                414,
                "FEASIBLE" if metrics["feasible"] else "OUTSIDE RULE",
                fill=SUCCESS_TINT if metrics["feasible"] else DANGER_TINT,
                foreground=SUCCESS if metrics["feasible"] else DANGER,
                width=116,
            )
            body.append(status)
    declared_label = (
        "ranking changes versus independence"
        if diagnostic["recommendation_changed_vs_independent"]
        else "same winner versus independence"
    )
    stress_label = (
        "stress changes the winner"
        if diagnostic["recommendation_changed_under_stress"]
        else "winner survives correlation stress"
    )
    body.extend(
        [
            text(36, 486, f"● {declared_label}", css="section", fill=accent),
            text(606, 486, f"◆ {stress_label}", css="section"),
            text(
                36,
                514,
                "P(best), tail utility, and risk are recomputed—not extrapolated—from matched simulations.",
                css="small",
            ),
        ]
    )
    return svg_document(
        "Correlation and tail-risk stress",
        "Independent residuals are compared with declared shared shocks and stronger dependence",
        "\n".join(body),
        height=580,
        accent=accent,
        description=(
            "Three directly labeled panels compare the preferred option, probability of being best, "
            "worst-decile utility, and constraint upper bound under independent, declared correlated, "
            "and correlation-stress simulations."
        ),
    )


def _criterion_scorecard(result: dict[str, Any]) -> str:
    alternatives = result["alternatives"]
    ranking = result["decision"]["ranking"]
    criteria = result["criteria"]
    recommendation = result["decision"]["recommendation"]
    accent, _, accent_tint = _theme(result)
    left, top = 276, 180
    cell_width = (WIDTH - left - 34) / len(criteria)
    row_height = 76
    height = top + row_height * len(ranking) + 58
    body: list[str] = []
    for column, criterion in enumerate(criteria):
        x = left + column * cell_width
        body.append(rounded_rect(x + 3, 128, cell_width - 8, 42, fill=NAVY, stroke=NAVY, radius=8))
        body.append(
            wrapped_text(
                x + cell_width / 2,
                145,
                criterion["label"],
                chars=max(9, int(cell_width / 8)),
                line_height=14,
                css="pill",
                anchor="middle",
                fill=PAPER,
            )
        )
        body.append(text(x + cell_width / 2, 174, f"weight {criterion['normalized_weight']:.0%}", css="small", anchor="middle"))
    for row, alternative_id in enumerate(ranking):
        y = top + row * row_height
        is_recommended = alternative_id == recommendation
        body.append(rounded_rect(30, y, 1134, row_height - 8, fill=PAPER if not is_recommended else accent_tint, stroke=accent if is_recommended else GRID, radius=10, stroke_width=2 if is_recommended else 1))
        body.append(
            wrapped_text(48, y + 29, alternatives[alternative_id]["label"], chars=27, line_height=16, css="section" if is_recommended else "label")
        )
        if is_recommended:
            badge, _ = pill(48, y + 38, "PREFERRED", fill=accent, foreground=PAPER, width=82)
            body.append(badge)
        for column, criterion in enumerate(criteria):
            metric = alternatives[alternative_id]["criteria"][criterion["id"]]
            score = metric.get("normalized_score")
            if score is None:
                score = _criterion_score(metric["mean"], criterion)
            x = left + column * cell_width + 14
            body.append(text(x, y + 26, f"{float(score) * 100:.0f}", css="value"))
            body.append(progress_bar(x, y + 39, cell_width - 32, float(score), color=accent if is_recommended else INK_SOFT, height=8))
            body.append(text(x, y + 61, "higher value" if float(score) >= 0.67 else "trade-off" if float(score) < 0.45 else "mid-range", css="small"))
    return svg_document(
        "Criterion trade-off profile",
        "Every score uses its declared worst-to-best reference scale; weights remain visible",
        "\n".join(body),
        height=height,
        accent=accent,
        description=(
            "A directly labeled scorecard compares normalized criterion values and weights "
            "for each alternative, with the preferred option outlined."
        ),
    )


def _scenario_plot(result: dict[str, Any]) -> str:
    alternatives = result["alternatives"]
    ranking = result["decision"]["ranking"]
    scenarios = result["scenarios"]
    recommendation = result["decision"]["recommendation"]
    accent, _, _ = _theme(result)
    colors = _alternative_colors(result)
    columns = min(3, len(scenarios))
    rows = math.ceil(len(scenarios) / columns)
    panel_gap = 18
    panel_width = (1128 - panel_gap * (columns - 1)) / columns
    panel_height = 112 + len(ranking) * 44
    top = 136
    height = top + rows * (panel_height + panel_gap) + 46
    body: list[str] = []
    for index, scenario in enumerate(scenarios):
        column = index % columns
        row = index // columns
        x = 36 + column * (panel_width + panel_gap)
        y = top + row * (panel_height + panel_gap)
        body.append(rounded_rect(x, y, panel_width, panel_height, fill=PAPER, stroke=GRID, radius=16))
        body.append(text(x + 18, y + 28, scenario["label"], css="section"))
        probability, probability_width = pill(x + panel_width - 102, y + 13, f"P {scenario['probability']:.0%}", fill=NAVY, foreground=PAPER, width=84)
        body.append(probability)
        body.append(text(x + 18, y + 55, "Risk-adjusted value · common 0–1 scale", css="small"))
        values = {
            alternative_id: alternatives[alternative_id]["scenario_utility"][scenario["id"]]["risk_adjusted_utility"]
            for alternative_id in ranking
        }
        winner = max(values, key=values.__getitem__)
        for alt_index, alternative_id in enumerate(ranking):
            row_y = y + 83 + alt_index * 44
            label = alternatives[alternative_id]["label"]
            color = colors[alternative_id]
            body.append(text(x + 18, row_y, label[:26] + ("…" if len(label) > 26 else ""), css="small", fill=INK if alternative_id == winner else MUTED))
            body.append(progress_bar(x + 18, row_y + 10, panel_width - 82, values[alternative_id], color=color, height=8))
            body.append(text(x + panel_width - 18, row_y + 18, f"{values[alternative_id]:.3f}", css="mono", anchor="end"))
            if alternative_id == winner:
                body.append(text(x + panel_width - 18, row_y, "WINNER", css="eyebrow", anchor="end", fill=color))
        if winner != recommendation:
            body.append(text(x + 18, y + panel_height - 12, "Scenario overturns the baseline preference", css="small", fill=WARNING))
    return svg_document(
        "Scenario resilience",
        "Small multiples reveal which external conditions preserve—or overturn—the preferred option",
        "\n".join(body),
        height=height,
        accent=accent,
        description=(
            "Small-multiple panels compare all alternatives on a common zero-to-one scale "
            "within each scenario and directly label the winner and scenario probability."
        ),
    )


def _sensitivity_heatmap(result: dict[str, Any]) -> str:
    alternatives = result["alternatives"]
    ranking = result["decision"]["ranking"]
    sensitivity = result["weight_sensitivity"]
    recommendation = result["decision"]["recommendation"]
    accent, _, accent_tint = _theme(result)
    left, top = 306, 188
    cell_width = (WIDTH - left - 34) / len(ranking)
    row_height = 62
    height = top + row_height * len(sensitivity) + 56
    body: list[str] = []
    for column, alternative_id in enumerate(ranking):
        x = left + column * cell_width
        body.append(
            wrapped_text(
                x + cell_width / 2,
                140,
                alternatives[alternative_id]["label"],
                chars=max(9, int(cell_width / 8)),
                line_height=14,
                css="small",
                anchor="middle",
            )
        )
        if alternative_id == recommendation:
            body.append(text(x + cell_width / 2, 174, "BASELINE PREFERENCE", css="eyebrow", anchor="middle", fill=accent))
    for row, item in enumerate(sensitivity):
        y = top + row * row_height
        if row % 2 == 0:
            body.append(rounded_rect(30, y - 3, 1134, row_height - 2, fill=PAPER, stroke="none", radius=8))
        arrow = "↓" if item["label"].lstrip().startswith("↓") else "↑"
        body.append(text(48, y + 24, arrow, css="section", fill=CORAL if arrow == "↓" else accent))
        body.append(wrapped_text(76, y + 22, item["label"], chars=29, line_height=15, css="label"))
        for column, alternative_id in enumerate(ranking):
            score = item["scores"].get(alternative_id)
            x = left + column * cell_width + 5
            is_winner = alternative_id == item["winner"]
            if score is None:
                body.append(rounded_rect(x, y + 6, cell_width - 10, 42, fill=CANVAS, stroke=GRID, radius=7))
                body.append(text(x + (cell_width - 10) / 2, y + 31, "infeasible", css="small", anchor="middle"))
                continue
            fill, foreground = score_tint(float(score), accent, accent_tint)
            body.append(rounded_rect(x, y + 6, cell_width - 10, 42, fill=fill, stroke=GOLD if is_winner else GRID, radius=7, stroke_width=3 if is_winner else 1))
            body.append(text(x + (cell_width - 10) / 2, y + 32, f"{score:.3f}", css="mono", anchor="middle", fill=foreground))
            if is_winner:
                body.append(text(x + cell_width - 14, y + 18, "◆", css="small", anchor="end", fill=GOLD))
    body.append(text(48, height - 32, "◆ gold outline = winner after one two-sided value-weight stress; numbers remain directly readable", css="small"))
    return svg_document(
        "Weight sensitivity",
        "Which stakeholder priorities can change the winner?",
        "\n".join(body),
        height=height,
        accent=accent,
        description=(
            "A directly labeled sensitivity matrix shows risk-adjusted scores and the winner "
            "after increasing or decreasing one criterion weight at a time."
        ),
    )


def _group_impact_heatmap(result: dict[str, Any]) -> str | None:
    alternatives = result["alternatives"]
    ranking = result["decision"]["ranking"]
    recommendation = result["decision"]["recommendation"]
    accent, _, accent_tint = _theme(result)
    metric_ids = sorted(
        {
            metric_id
            for alternative_id in ranking
            for metric_id in alternatives[alternative_id]["group_impacts"]
        }
    )
    if not metric_ids:
        return None
    left, top = 300, 180
    cell_width = (WIDTH - left - 34) / len(metric_ids)
    row_height = 76
    height = top + row_height * len(ranking) + 62
    body: list[str] = []
    for column, metric_id in enumerate(metric_ids):
        x = left + column * cell_width
        body.append(rounded_rect(x + 4, 132, cell_width - 9, 38, fill=NAVY, stroke=NAVY, radius=8))
        body.append(
            wrapped_text(
                x + cell_width / 2,
                148,
                metric_id.replace("_", " "),
                chars=max(12, int(cell_width / 8)),
                line_height=14,
                css="pill",
                anchor="middle",
                fill=PAPER,
            )
        )
    for row, alternative_id in enumerate(ranking):
        y = top + row * row_height
        is_recommended = alternative_id == recommendation
        body.append(rounded_rect(30, y, 1134, row_height - 8, fill=accent_tint if is_recommended else PAPER, stroke=accent if is_recommended else GRID, radius=10, stroke_width=2 if is_recommended else 1))
        body.append(wrapped_text(48, y + 29, alternatives[alternative_id]["label"], chars=29, line_height=16, css="section" if is_recommended else "label"))
        for column, metric_id in enumerate(metric_ids):
            x = left + column * cell_width + 14
            metric = alternatives[alternative_id]["group_impacts"].get(metric_id)
            ratio = metric.get("parity_ratio") if metric else None
            if ratio is None:
                body.append(text(x, y + 29, "n/a", css="small"))
                continue
            bounded = min(1.0, max(0.0, float(ratio)))
            body.append(text(x, y + 27, f"{ratio:.2f}", css="value"))
            body.append(progress_bar(x, y + 39, cell_width - 34, bounded, color=accent if bounded >= 0.8 else WARNING, height=8, marker=0.8))
            body.append(text(x, y + 61, f"gap to parity {1 - bounded:.0%}", css="small"))
    body.append(text(48, height - 34, "Ratio = lowest group value ÷ highest group value · similarity is not proof of fairness", css="small"))
    return svg_document(
        "Distributional impact screen",
        "Descriptive parity ratios identify where separate subgroup judgment is required",
        "\n".join(body),
        height=height,
        accent=accent,
        description=(
            "A directly labeled scorecard compares supplied group parity ratios, distance from "
            "parity, and a review reference without treating similarity as proof of fairness."
        ),
    )


def generate_visuals(
    case: dict[str, Any],
    result: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, str]:
    figures_dir = Path(output_dir) / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    visual_specs: list[tuple[str, str, str, str, str, str]] = [
        (
            "decision_scorecard",
            "decision-scorecard.svg",
            _decision_scorecard(result),
            "Executive Summary",
            "executive scorecard",
            "The preferred option, decision status, and risk boundary are visible together.",
        ),
        (
            "robustness_profile",
            "robustness-profile.svg",
            _robustness_profile(result),
            "Decision status and robustness",
            "donut and bullet profile",
            "Robustness is decomposed into four transparent diagnostics.",
        ),
        (
            "alternative_ranking",
            "alternative-ranking.svg",
            _alternative_ranking(result),
            "Alternative ranking",
            "ranked horizontal bar",
            "The ordering combines decision value with explicit feasibility status.",
        ),
        (
            "constraint_risk",
            "constraint-risk.svg",
            _constraint_risk(result),
            "Constraint risk boundary",
            "dot, interval, and threshold",
            "Feasibility depends on the one-sided U95 relative to the risk tolerance.",
        ),
        (
            "criterion_scorecard",
            "criterion-scorecard.svg",
            _criterion_scorecard(result),
            "Criterion trade-offs",
            "direct-labeled scorecard",
            "The visual shows where each alternative earns and gives up value.",
        ),
        (
            "utility_uncertainty",
            "utility-uncertainty.svg",
            _uncertainty_plot(result),
            "Downside and uncertainty",
            "dot and interval",
            "Expected utility is interpreted alongside overlap and worst-decile outcomes.",
        ),
        (
            "correlation_stress",
            "correlation-stress.svg",
            _correlation_stress(result),
            "Correlation and tail-risk stress",
            "three-state diagnostic scorecard",
            "P(best), CVaR10, and breach risk are recomputed under independent, declared, and stressed dependence.",
        ),
        (
            "scenario_performance",
            "scenario-performance.svg",
            _scenario_plot(result),
            "Scenario resilience",
            "small-multiple bullet bars",
            "Scenario panels reveal when the baseline preference is preserved or overturned.",
        ),
        (
            "weight_sensitivity",
            "weight-sensitivity.svg",
            _sensitivity_heatmap(result),
            "Weight sensitivity",
            "direct-labeled heatmap",
            "Winner outlines identify which value-weight changes can change the decision.",
        ),
    ]
    group_svg = _group_impact_heatmap(result)
    if group_svg:
        visual_specs.append(
            (
                "group_impact",
                "group-impact.svg",
                group_svg,
                "Distributional effects",
                "direct-labeled ratio scorecard",
                "Parity ratios locate review needs without making a fairness claim.",
            )
        )

    analytical_questions = {
        "decision_scorecard": "What is the headline decision result?",
        "robustness_profile": "Why is the decision status what it is?",
        "alternative_ranking": "Which feasible alternative leads on risk-adjusted value?",
        "constraint_risk": "Which alternatives pass the modeled risk boundary?",
        "criterion_scorecard": "Where are the material criterion trade-offs?",
        "utility_uncertainty": "How much uncertainty, overlap, and downside remain?",
        "correlation_stress": "How do shared shocks change P(best), tail value, and feasibility?",
        "scenario_performance": "Which modeled conditions preserve or overturn the preference?",
        "weight_sensitivity": "Which stakeholder priorities can change the winner?",
        "group_impact": "Where might distributional review be needed?",
    }
    paths: dict[str, str] = {}
    chart_map: list[dict[str, Any]] = []
    for visual_id, filename, svg, section, family, takeaway in visual_specs:
        path = figures_dir / filename
        path.write_text(svg, encoding="utf-8")
        relative = f"figures/{filename}"
        paths[visual_id] = relative
        chart_map.append(
            {
                "id": visual_id,
                "section": section,
                "analytical_question": analytical_questions[visual_id],
                "supported_takeaway": takeaway,
                "family": family,
                "benchmark": (
                    "Explicit tolerance/target is drawn where it determines interpretation."
                    if visual_id in {"robustness_profile", "constraint_risk", "group_impact"}
                    else "Shared scale and direct labels support the primary comparison."
                ),
                "palette_policy": (
                    "One domain accent for the preferred result; additional categorical roots "
                    "only preserve alternative identity in scenario panels."
                ),
                "accessibility": (
                    "Title and description, direct numeric labels, and non-color status encoding "
                    "through ranks, shapes, outlines, text, or line style."
                ),
                "file": relative,
                "source": "decision-results.json",
            }
        )
    (figures_dir / "chart-map.json").write_text(
        json.dumps(chart_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return paths
