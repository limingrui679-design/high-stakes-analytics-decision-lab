#!/usr/bin/env python3
"""Dependency-free evidence analysis for two-group health and policy studies."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from visual_system import (
    GRID,
    NAVY,
    PAPER,
    TEAL,
    TEAL_TINT,
    progress_bar,
    rounded_rect,
    svg_document,
    text,
)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    center = _mean(values)
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def _ci(center: float, standard_error: float) -> list[float]:
    return [center - 1.96 * standard_error, center + 1.96 * standard_error]


def _binary_effect(
    exposed_events: int,
    exposed_n: int,
    reference_events: int,
    reference_n: int,
) -> dict[str, Any]:
    exposed_risk = exposed_events / exposed_n
    reference_risk = reference_events / reference_n
    risk_difference = exposed_risk - reference_risk
    rd_se = math.sqrt(
        exposed_risk * (1 - exposed_risk) / exposed_n
        + reference_risk * (1 - reference_risk) / reference_n
    )

    raw_cells = (
        exposed_events,
        exposed_n - exposed_events,
        reference_events,
        reference_n - reference_events,
    )
    correction = 0.5 if any(cell == 0 for cell in raw_cells) else 0.0
    a = exposed_events + correction
    b = exposed_n - exposed_events + correction
    c = reference_events + correction
    d = reference_n - reference_events + correction
    risk_ratio = (a / (a + b)) / (c / (c + d))
    rr_se = math.sqrt(1 / a - 1 / (a + b) + 1 / c - 1 / (c + d))
    odds_ratio = (a * d) / (b * c)
    or_se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return {
        "risk_difference": risk_difference,
        "risk_difference_ci95": _ci(risk_difference, rd_se),
        "risk_ratio": risk_ratio,
        "risk_ratio_ci95": [
            math.exp(math.log(risk_ratio) - 1.96 * rr_se),
            math.exp(math.log(risk_ratio) + 1.96 * rr_se),
        ],
        "odds_ratio": odds_ratio,
        "odds_ratio_ci95": [
            math.exp(math.log(odds_ratio) - 1.96 * or_se),
            math.exp(math.log(odds_ratio) + 1.96 * or_se),
        ],
        "continuity_correction": correction,
        "interval_method": "Wald intervals; log scale for ratios",
    }


def _kaplan_meier(
    observations: list[tuple[float, int]],
    horizon: float,
) -> dict[str, Any]:
    at_risk = len(observations)
    survival = 1.0
    greenwood = 0.0
    event_times = sorted(
        {
            time
            for time, event in observations
            if event == 1 and time <= horizon
        }
    )
    for event_time in event_times:
        at_risk = sum(time >= event_time for time, _ in observations)
        events = sum(
            time == event_time and event == 1
            for time, event in observations
        )
        if at_risk <= 0:
            continue
        survival *= 1.0 - events / at_risk
        if at_risk > events:
            greenwood += events / (at_risk * (at_risk - events))
    standard_error = survival * math.sqrt(greenwood)
    interval = _ci(survival, standard_error)
    return {
        "horizon": horizon,
        "n": len(observations),
        "survival_probability": survival,
        "ci95": [max(0.0, interval[0]), min(1.0, interval[1])],
        "method": "Kaplan–Meier with Greenwood standard error",
    }


def analyze_evidence(
    rows: list[dict[str, str]],
    *,
    group_column: str,
    binary_outcome: str,
    exposed_group: str,
    reference_group: str,
    continuous_outcome: str | None = None,
    time_column: str | None = None,
    event_column: str | None = None,
    horizon: float | None = None,
) -> dict[str, Any]:
    groups = [reference_group, exposed_group]
    missingness = {
        column: sum(not row.get(column, "").strip() for row in rows)
        for column in {
            group_column,
            binary_outcome,
            *(column for column in (continuous_outcome, time_column, event_column) if column),
        }
    }
    binary: dict[str, list[int]] = {group: [] for group in groups}
    continuous: dict[str, list[float]] = {group: [] for group in groups}
    survival: dict[str, list[tuple[float, int]]] = {group: [] for group in groups}
    excluded = 0
    for row in rows:
        group = row.get(group_column, "").strip()
        if group not in binary:
            excluded += 1
            continue
        outcome_text = row.get(binary_outcome, "").strip()
        if outcome_text:
            outcome = int(float(outcome_text))
            if outcome not in {0, 1}:
                raise ValueError(f"{binary_outcome} must contain only 0/1 values.")
            binary[group].append(outcome)
        if continuous_outcome and row.get(continuous_outcome, "").strip():
            continuous[group].append(float(row[continuous_outcome]))
        if (
            time_column
            and event_column
            and row.get(time_column, "").strip()
            and row.get(event_column, "").strip()
        ):
            event = int(float(row[event_column]))
            if event not in {0, 1}:
                raise ValueError(f"{event_column} must contain only 0/1 values.")
            survival[group].append((float(row[time_column]), event))

    if any(not binary[group] for group in groups):
        raise ValueError("Each comparison group needs at least one complete binary outcome.")

    binary_summary = {
        group: {
            "n": len(binary[group]),
            "events": sum(binary[group]),
            "risk": sum(binary[group]) / len(binary[group]),
        }
        for group in groups
    }
    effect = _binary_effect(
        binary_summary[exposed_group]["events"],
        binary_summary[exposed_group]["n"],
        binary_summary[reference_group]["events"],
        binary_summary[reference_group]["n"],
    )

    continuous_result = None
    if continuous_outcome and all(continuous[group] for group in groups):
        exposed_values = continuous[exposed_group]
        reference_values = continuous[reference_group]
        difference = _mean(exposed_values) - _mean(reference_values)
        standard_error = math.sqrt(
            _variance(exposed_values) / len(exposed_values)
            + _variance(reference_values) / len(reference_values)
        )
        continuous_result = {
            "outcome": continuous_outcome,
            "groups": {
                group: {
                    "n": len(continuous[group]),
                    "mean": _mean(continuous[group]),
                    "sd": math.sqrt(_variance(continuous[group])),
                }
                for group in groups
            },
            "mean_difference": difference,
            "mean_difference_ci95": _ci(difference, standard_error),
            "interval_method": "Normal approximation with unequal variances",
        }

    survival_result = None
    if time_column and event_column and horizon is not None and all(survival[group] for group in groups):
        survival_result = {
            "time_column": time_column,
            "event_column": event_column,
            "groups": {
                group: _kaplan_meier(survival[group], horizon)
                for group in groups
            },
        }

    return {
        "analysis_type": "two_group_evidence_analysis",
        "data_quality": {
            "rows_received": len(rows),
            "rows_outside_comparison_groups": excluded,
            "missing_count_by_column": missingness,
        },
        "comparison": {
            "exposed_group": exposed_group,
            "reference_group": reference_group,
            "binary_outcome": binary_outcome,
        },
        "binary_outcome": {
            "groups": binary_summary,
            **effect,
        },
        "continuous_outcome": continuous_result,
        "time_to_event": survival_result,
        "interpretation_boundary": (
            "Effect estimates are descriptive unless assignment and identification "
            "justify causal interpretation. Approximate intervals do not replace a "
            "study-specific analysis plan."
        ),
    }


def _svg(result: dict[str, Any], title: str) -> str:
    height = 548
    groups = result["binary_outcome"]["groups"]
    reference = result["comparison"]["reference_group"]
    exposed = result["comparison"]["exposed_group"]
    rd = result["binary_outcome"]["risk_difference"]
    rd_ci = result["binary_outcome"]["risk_difference_ci95"]
    colors = {reference: "#617084", exposed: TEAL}
    body: list[str] = [
        rounded_rect(36, 134, 680, 226, fill=PAPER, stroke=GRID, radius=17),
        text(58, 166, "OBSERVED EVENT RISK", css="eyebrow"),
        text(58, 188, "Same 0–100% scale for both groups", css="small"),
    ]
    for index, group in enumerate((reference, exposed)):
        risk = groups[group]["risk"]
        y = 222 + index * 76
        body.extend(
            [
                text(58, y, group, css="section" if group == exposed else "label"),
                text(686, y, f"{risk:.1%}", css="value", anchor="end"),
                progress_bar(240, y - 10, 410, risk, color=colors[group], height=14),
                text(240, y + 22, f"{groups[group]['events']} events / {groups[group]['n']} observations", css="small"),
            ]
        )
    body.extend(
        [
            rounded_rect(736, 134, 428, 226, fill=NAVY, stroke=NAVY, radius=17),
            text(760, 166, "EFFECT ESTIMATE", css="eyebrow", fill=TEAL),
            text(760, 216, f"{rd:+.1%}", css="display", fill=PAPER),
            text(760, 244, "risk difference", css="label", fill="#C7D4E4"),
            text(760, 285, f"95% CI  {rd_ci[0]:+.1%}  to  {rd_ci[1]:+.1%}", css="section", fill=PAPER),
            text(760, 320, f"RR {result['binary_outcome']['risk_ratio']:.2f}   ·   OR {result['binary_outcome']['odds_ratio']:.2f}", css="label", fill="#C7D4E4"),
            rounded_rect(36, 382, 1128, 104, fill=TEAL_TINT, stroke=TEAL, radius=15),
            text(58, 412, "INTERPRETATION BOUNDARY", css="eyebrow", fill=TEAL),
            text(58, 444, "Observed comparison—not automatically a causal effect", css="section"),
            text(58, 469, "Approximate intervals require a study-specific analysis plan and defensible assignment or identification.", css="small"),
        ]
    )
    return svg_document(
        title,
        "Observed binary outcomes · effect magnitude, uncertainty, sample size, and causal boundary",
        "\n".join(body),
        height=height,
        accent=TEAL,
        kicker="EVIDENCE ANALYSIS",
        source="Source: evidence-results.json",
        note="Approximate intervals · causal design required",
        description=(
            "Two group risks are compared on a common zero-to-one scale. A separate effect "
            "panel shows the risk difference, confidence interval, risk ratio, and odds ratio."
        ),
    )


def render_report(result: dict[str, Any], title: str) -> str:
    outcome = result["comparison"]["binary_outcome"]
    exposed = result["comparison"]["exposed_group"]
    reference = result["comparison"]["reference_group"]
    binary = result["binary_outcome"]
    rd_ci = binary["risk_difference_ci95"]
    lines = [
        f"# {title}",
        "",
        "## Executive Summary",
        "",
        f"Observed **{outcome}** risk was **{binary['groups'][exposed]['risk']:.1%}** in "
        f"{exposed} and **{binary['groups'][reference]['risk']:.1%}** in {reference}. "
        f"The risk difference was **{binary['risk_difference']:+.1%}** "
        f"(approximate 95% CI {rd_ci[0]:+.1%} to {rd_ci[1]:+.1%}).",
        "",
        "![Evidence effect summary](evidence-summary.svg)",
        "",
        "## Key findings",
        "",
        "| Estimand | Estimate | Approximate 95% CI |",
        "|---|---:|---:|",
        f"| Risk difference | {binary['risk_difference']:+.3f} | "
        f"{binary['risk_difference_ci95'][0]:+.3f} to {binary['risk_difference_ci95'][1]:+.3f} |",
        f"| Risk ratio | {binary['risk_ratio']:.3f} | "
        f"{binary['risk_ratio_ci95'][0]:.3f} to {binary['risk_ratio_ci95'][1]:.3f} |",
        f"| Odds ratio | {binary['odds_ratio']:.3f} | "
        f"{binary['odds_ratio_ci95'][0]:.3f} to {binary['odds_ratio_ci95'][1]:.3f} |",
        "",
    ]
    if result["continuous_outcome"]:
        continuous = result["continuous_outcome"]
        lines.extend(
            [
                "## Continuous outcome",
                "",
                f"The mean difference in **{continuous['outcome']}** was "
                f"**{continuous['mean_difference']:+.2f}** "
                f"(95% CI {continuous['mean_difference_ci95'][0]:+.2f} to "
                f"{continuous['mean_difference_ci95'][1]:+.2f}).",
                "",
            ]
        )
    if result["time_to_event"]:
        lines.extend(["## Time-to-event summary", "", "| Group | Horizon | Survival | 95% CI |", "|---|---:|---:|---:|"])
        for group, summary in result["time_to_event"]["groups"].items():
            lines.append(
                f"| {group} | {summary['horizon']:.0f} | {summary['survival_probability']:.1%} | "
                f"{summary['ci95'][0]:.1%}–{summary['ci95'][1]:.1%} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Recommended next steps",
            "",
            "1. Confirm whether assignment and identification support a causal estimand.",
            "2. Reconcile missingness, follow-up, protocol deviations, and outcome definitions.",
            "3. Pre-specify the study-specific model, multiplicity approach, and sensitivity analyses.",
            "",
            "## Further questions",
            "",
            "- Are the comparison groups exchangeable at baseline?",
            "- Could censoring, missing outcomes, or measurement error change the effect estimate?",
            "- Which subgroup effects are decision-relevant and sufficiently powered?",
            "",
            "## Caveats and assumptions",
            "",
            f"- Rows received: {result['data_quality']['rows_received']}",
            f"- Rows outside comparison groups: {result['data_quality']['rows_outside_comparison_groups']}",
            f"- Missingness: {json.dumps(result['data_quality']['missing_count_by_column'], ensure_ascii=False)}",
            f"- {result['interpretation_boundary']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(result: dict[str, Any], output_dir: str | Path, title: str) -> tuple[Path, Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "evidence-results.json"
    report_path = directory / "evidence-report.md"
    figure_path = directory / "evidence-summary.svg"
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_report(result, title), encoding="utf-8")
    figure_path.write_text(_svg(result, title), encoding="utf-8")
    return json_path, report_path, figure_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--group", required=True)
    parser.add_argument("--outcome", required=True)
    parser.add_argument("--exposed", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--continuous")
    parser.add_argument("--time")
    parser.add_argument("--event")
    parser.add_argument("--horizon", type=float)
    parser.add_argument("--title", default="Evidence Analysis")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    with Path(args.csv_path).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = analyze_evidence(
        rows,
        group_column=args.group,
        binary_outcome=args.outcome,
        exposed_group=args.exposed,
        reference_group=args.reference,
        continuous_outcome=args.continuous,
        time_column=args.time,
        event_column=args.event,
        horizon=args.horizon,
    )
    paths = write_outputs(result, args.output_dir, args.title)
    print("\n".join(str(path) for path in paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
