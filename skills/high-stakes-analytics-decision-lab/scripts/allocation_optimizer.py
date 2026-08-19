#!/usr/bin/env python3
"""Exact grid optimization for small resource-allocation decisions under scenarios."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

from visual_system import (
    GREEN,
    GREEN_TINT,
    GRID,
    INK,
    NAVY,
    PAPER,
    rounded_rect,
    svg_document,
    text,
    wrapped_text,
)


def _constraint_holds(value: float, operator: str, threshold: float) -> bool:
    if operator == "<=":
        return value <= threshold + 1e-12
    if operator == "<":
        return value < threshold
    if operator == ">=":
        return value >= threshold - 1e-12
    if operator == ">":
        return value > threshold
    if operator == "==":
        return abs(value - threshold) <= 1e-9
    raise ValueError(f"Unsupported constraint operator: {operator}")


def _linear_value(coefficients: dict[str, float], allocation: dict[str, float]) -> float:
    return sum(float(coefficients.get(key, 0.0)) * value for key, value in allocation.items())


def validate_config(config: dict[str, Any]) -> None:
    if not isinstance(config.get("resources"), list) or not config["resources"]:
        raise ValueError("resources must be a non-empty list.")
    resource_ids: list[str] = []
    for resource in config["resources"]:
        resource_id = resource.get("id")
        if not isinstance(resource_id, str) or not resource_id:
            raise ValueError("Every resource needs a non-empty id.")
        resource_ids.append(resource_id)
        if float(resource.get("step", 0)) <= 0:
            raise ValueError(f"Resource {resource_id} requires step > 0.")
        if float(resource.get("max", 0)) < float(resource.get("min", 0)):
            raise ValueError(f"Resource {resource_id} requires max >= min.")
    if len(set(resource_ids)) != len(resource_ids):
        raise ValueError("Resource ids must be unique.")
    if not isinstance(config.get("scenarios"), list) or not config["scenarios"]:
        raise ValueError("scenarios must be a non-empty list.")
    probability_sum = sum(float(item["probability"]) for item in config["scenarios"])
    if abs(probability_sum - 1.0) > 1e-6:
        raise ValueError("Scenario probabilities must sum to one.")
    for constraint in config.get("constraints", []):
        if constraint.get("operator") not in {"<=", "<", ">=", ">", "=="}:
            raise ValueError("Constraint operator is unsupported.")


def optimize_allocation(config: dict[str, Any]) -> dict[str, Any]:
    validate_config(config)
    resources = config["resources"]
    resource_ids = [resource["id"] for resource in resources]
    value_grids: list[list[float]] = []
    for resource in resources:
        minimum = float(resource.get("min", 0))
        maximum = float(resource["max"])
        step = float(resource["step"])
        count = int(round((maximum - minimum) / step))
        values = [minimum + index * step for index in range(count + 1)]
        if values[-1] < maximum - 1e-9:
            values.append(maximum)
        value_grids.append(values)

    constraints = list(config.get("constraints", []))
    if "budget" in config:
        constraints.append(
            {
                "id": "budget",
                "label": "Budget",
                "coefficients": {
                    resource["id"]: float(resource.get("unit_cost", 0))
                    for resource in resources
                },
                "operator": "<=",
                "threshold": float(config["budget"]),
            }
        )
    scenarios = config["scenarios"]
    risk_aversion = float(config.get("risk_aversion", 0.5))
    candidates: list[dict[str, Any]] = []
    evaluated = 0
    for allocation_values in itertools.product(*value_grids):
        evaluated += 1
        allocation = dict(zip(resource_ids, allocation_values, strict=True))
        diagnostics = []
        feasible = True
        for constraint in constraints:
            value = _linear_value(constraint.get("coefficients", {}), allocation)
            threshold = float(constraint["threshold"])
            holds = _constraint_holds(value, constraint["operator"], threshold)
            feasible &= holds
            diagnostics.append(
                {
                    "id": constraint.get("id", constraint.get("label", "constraint")),
                    "label": constraint.get("label", "Constraint"),
                    "value": value,
                    "operator": constraint["operator"],
                    "threshold": threshold,
                    "holds": holds,
                }
            )
        if not feasible:
            continue
        scenario_values = {
            scenario["id"]: _linear_value(
                scenario["benefit_coefficients"],
                allocation,
            )
            for scenario in scenarios
        }
        expected_value = sum(
            float(scenario["probability"]) * scenario_values[scenario["id"]]
            for scenario in scenarios
        )
        worst_case_value = min(scenario_values.values())
        robust_value = expected_value - risk_aversion * (
            expected_value - worst_case_value
        )
        candidates.append(
            {
                "allocation": allocation,
                "expected_value": expected_value,
                "worst_case_value": worst_case_value,
                "robust_value": robust_value,
                "scenario_values": scenario_values,
                "constraints": diagnostics,
            }
        )
    if not candidates:
        return {
            "analysis_type": "exact_grid_resource_optimization",
            "status": "no_feasible_allocation",
            "evaluated_allocations": evaluated,
            "feasible_allocations": 0,
            "config_summary": {
                "resources": resource_ids,
                "risk_aversion": risk_aversion,
            },
            "ranking": [],
        }
    best_by_scenario = {
        scenario["id"]: max(
            candidate["scenario_values"][scenario["id"]]
            for candidate in candidates
        )
        for scenario in scenarios
    }
    for candidate in candidates:
        candidate["maximum_regret"] = max(
            best_by_scenario[scenario_id] - candidate["scenario_values"][scenario_id]
            for scenario_id in best_by_scenario
        )
    ranking = sorted(
        candidates,
        key=lambda item: (
            item["robust_value"],
            item["expected_value"],
            -item["maximum_regret"],
        ),
        reverse=True,
    )
    top_k = int(config.get("top_k", 10))
    return {
        "analysis_type": "exact_grid_resource_optimization",
        "status": "optimal_on_declared_grid",
        "title": config.get("title", "Resource Allocation Optimization"),
        "evaluated_allocations": evaluated,
        "feasible_allocations": len(candidates),
        "config_summary": {
            "resources": resource_ids,
            "risk_aversion": risk_aversion,
            "objective": (
                "expected scenario value minus risk_aversion times the gap "
                "between expected and worst-case value"
            ),
        },
        "best_by_scenario": best_by_scenario,
        "ranking": ranking[:top_k],
        "optimal_allocation": ranking[0],
        "interpretation_boundary": (
            "Optimality holds only on the declared discrete grid, linear "
            "coefficients, constraints, and scenarios. Validate coefficients and "
            "use a production solver for larger or nonlinear problems."
        ),
    }


def _allocation_label(allocation: dict[str, float]) -> str:
    return " · ".join(f"{key}={value:g}" for key, value in allocation.items())


def _svg(result: dict[str, Any], title: str) -> str:
    ranking = result["ranking"][:5]
    row_height = 76
    height = 294 + row_height * len(ranking) + 56
    minimum = min(0.0, min(item["robust_value"] for item in ranking))
    maximum = max(0.0, max(item["robust_value"] for item in ranking))
    spread = maximum - minimum or 1.0
    chart_left, chart_right = 414, 1080
    zero_x = chart_left + (0 - minimum) / spread * (chart_right - chart_left)
    best = ranking[0]
    body: list[str] = [
        rounded_rect(36, 134, 1128, 106, fill=NAVY, stroke=NAVY, radius=17),
        text(58, 164, "OPTIMAL FEASIBLE ALLOCATION", css="eyebrow", fill=GREEN),
        wrapped_text(58, 198, _allocation_label(best["allocation"]), chars=62, line_height=22, css="section", fill=PAPER),
        text(804, 175, f"{best['robust_value']:.1f}", css="display", fill=PAPER, anchor="middle"),
        text(804, 207, "ROBUST VALUE", css="eyebrow", fill="#C7D4E4", anchor="middle"),
        text(970, 175, f"{best['expected_value']:.1f}", css="big", fill=PAPER, anchor="middle"),
        text(970, 207, "EXPECTED", css="eyebrow", fill="#C7D4E4", anchor="middle"),
        text(1100, 175, f"{best['worst_case_value']:.1f}", css="big", fill=PAPER, anchor="middle"),
        text(1100, 207, "WORST CASE", css="eyebrow", fill="#C7D4E4", anchor="middle"),
        text(36, 274, "TOP FEASIBLE ALLOCATIONS", css="eyebrow"),
        text(1080, 274, f"common scale {minimum:.1f} to {maximum:.1f}", css="small", anchor="end"),
    ]
    for tick in range(5):
        value = minimum + spread * tick / 4
        x = chart_left + (chart_right - chart_left) * tick / 4
        body.append(f'<line x1="{x:.1f}" y1="288" x2="{x:.1f}" y2="{height - 78}" stroke="{GRID}"/>')
        body.append(text(x, height - 56, f"{value:.1f}", css="small", anchor="middle"))
    body.append(f'<line x1="{zero_x:.1f}" y1="284" x2="{zero_x:.1f}" y2="{height - 78}" stroke="{INK}" stroke-width="1.5"/>')
    for index, item in enumerate(ranking):
        y = 316 + index * row_height
        value_x = chart_left + (item["robust_value"] - minimum) / spread * (chart_right - chart_left)
        start_x = min(zero_x, value_x)
        bar_width = max(3, abs(value_x - zero_x))
        is_best = index == 0
        color = GREEN if is_best else GREEN_TINT
        body.extend(
            [
                rounded_rect(30, y - 25, 1134, 64, fill=PAPER, stroke=GREEN if is_best else "none", radius=10, stroke_width=2 if is_best else 1),
                f'<circle cx="56" cy="{y + 1}" r="16" fill="{GREEN if is_best else NAVY}"/>',
                text(56, y + 6, str(index + 1), css="pill", fill=PAPER, anchor="middle"),
                wrapped_text(84, y - 2, _allocation_label(item["allocation"]), chars=38, line_height=15, css="section" if is_best else "label"),
                f'<rect x="{start_x:.1f}" y="{y - 10}" width="{bar_width:.1f}" height="22" rx="6" fill="{color}" stroke="{GREEN}"/>',
                text(value_x + (10 if value_x >= zero_x else -10), y + 6, f"{item['robust_value']:.1f}", css="value", anchor="start" if value_x >= zero_x else "end"),
                text(chart_left, y + 31, f"expected {item['expected_value']:.1f} · worst {item['worst_case_value']:.1f} · max regret {item['maximum_regret']:.1f}", css="small"),
            ]
        )
    return svg_document(
        title,
        "Exact discrete search · feasibility, expected value, worst case, and maximum regret",
        "\n".join(body),
        height=height,
        accent=GREEN,
        kicker="RESOURCE OPTIMIZATION",
        source="Source: optimization-results.json",
        note="Optimal only on the declared grid and scenarios",
        description=(
            "The optimal feasible allocation is summarized above ranked horizontal bars. "
            "Each row directly labels robust value, expected value, worst case, and maximum regret."
        ),
    )


def render_report(result: dict[str, Any], title: str) -> str:
    if result["status"] == "no_feasible_allocation":
        return "\n".join(
            [
                f"# {title}",
                "",
                "## Executive Summary",
                "",
                f"No feasible allocation was found across {result['evaluated_allocations']:,} "
                "grid points. Review the bounds, budget, or hard constraints.",
                "",
            ]
        )
    optimal = result["optimal_allocation"]
    lines = [
        f"# {title}",
        "",
        "## Executive Summary",
        "",
        f"The best allocation on the declared grid is **{_allocation_label(optimal['allocation'])}**. "
        f"It has robust value **{optimal['robust_value']:.1f}**, expected value "
        f"**{optimal['expected_value']:.1f}**, and worst-case value "
        f"**{optimal['worst_case_value']:.1f}**.",
        "",
        "![Optimization ranking](allocation-ranking.svg)",
        "",
        "## Key findings",
        "",
        "| Rank | Allocation | Robust value | Expected | Worst case | Maximum regret |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for index, item in enumerate(result["ranking"], start=1):
        lines.append(
            f"| {index} | {_allocation_label(item['allocation'])} | "
            f"{item['robust_value']:.2f} | {item['expected_value']:.2f} | "
            f"{item['worst_case_value']:.2f} | {item['maximum_regret']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Recommended next steps",
            "",
            "1. Validate resource coefficients and scenario values with domain owners.",
            "2. Stress-test budgets, access rules, and the worst-case scenario before implementation.",
            "3. Re-solve with a production optimizer if the decision becomes larger, nonlinear, or dynamic.",
            "",
            "## Further questions",
            "",
            "- Which omitted constraint could make the top allocation operationally infeasible?",
            "- How sensitive is the result to scenario probabilities and risk aversion?",
            "- Which affected group bears the largest opportunity cost?",
            "",
            "## Caveats and assumptions",
            "",
            f"- Grid points evaluated: {result['evaluated_allocations']:,}",
            f"- Feasible grid points: {result['feasible_allocations']:,}",
            f"- {result['interpretation_boundary']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(result: dict[str, Any], output_dir: str | Path, title: str) -> tuple[Path, Path, Path | None]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "optimization-results.json"
    report_path = directory / "optimization-report.md"
    figure_path = directory / "allocation-ranking.svg"
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_report(result, title), encoding="utf-8")
    if result["ranking"]:
        figure_path.write_text(_svg(result, title), encoding="utf-8")
        return json_path, report_path, figure_path
    return json_path, report_path, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_path")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config_path).read_text(encoding="utf-8"))
    result = optimize_allocation(config)
    title = config.get("title", "Resource Allocation Optimization")
    paths = write_outputs(result, args.output_dir, title)
    print("\n".join(str(path) for path in paths if path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
