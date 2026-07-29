#!/usr/bin/env python3
"""Validate binary prediction scores with calibration, discrimination, and subgroup checks."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_system import (
    GRID,
    INK,
    NAVY,
    PAPER,
    VIOLET,
    rounded_rect,
    svg_document,
    text,
    wrapped_text,
)


def _safe_divide(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def _auc(labels: list[int], scores: list[float]) -> float | None:
    positive_scores = [score for label, score in zip(labels, scores) if label == 1]
    negative_scores = [score for label, score in zip(labels, scores) if label == 0]
    if not positive_scores or not negative_scores:
        return None
    wins = 0.0
    for positive in positive_scores:
        for negative in negative_scores:
            wins += 1.0 if positive > negative else 0.5 if positive == negative else 0.0
    return wins / (len(positive_scores) * len(negative_scores))


def _classification_metrics(
    labels: list[int],
    scores: list[float],
    threshold: float,
) -> dict[str, Any]:
    predictions = [int(score >= threshold) for score in scores]
    true_positive = sum(label == 1 and prediction == 1 for label, prediction in zip(labels, predictions))
    true_negative = sum(label == 0 and prediction == 0 for label, prediction in zip(labels, predictions))
    false_positive = sum(label == 0 and prediction == 1 for label, prediction in zip(labels, predictions))
    false_negative = sum(label == 1 and prediction == 0 for label, prediction in zip(labels, predictions))
    return {
        "n": len(labels),
        "prevalence": sum(labels) / len(labels),
        "auc": _auc(labels, scores),
        "brier_score": sum((score - label) ** 2 for label, score in zip(labels, scores)) / len(labels),
        "threshold": threshold,
        "accuracy": (true_positive + true_negative) / len(labels),
        "precision": _safe_divide(true_positive, true_positive + false_positive),
        "recall_sensitivity": _safe_divide(true_positive, true_positive + false_negative),
        "specificity": _safe_divide(true_negative, true_negative + false_positive),
        "false_positive_rate": _safe_divide(false_positive, false_positive + true_negative),
        "false_negative_rate": _safe_divide(false_negative, false_negative + true_positive),
        "confusion_matrix": {
            "true_positive": true_positive,
            "true_negative": true_negative,
            "false_positive": false_positive,
            "false_negative": false_negative,
        },
    }


def _calibration(labels: list[int], scores: list[float], bins: int) -> tuple[list[dict[str, Any]], float]:
    calibration: list[dict[str, Any]] = []
    expected_calibration_error = 0.0
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        members = [
            (label, score)
            for label, score in zip(labels, scores)
            if low <= score < high or (index == bins - 1 and score == 1.0)
        ]
        if not members:
            continue
        mean_score = sum(score for _, score in members) / len(members)
        observed_rate = sum(label for label, _ in members) / len(members)
        expected_calibration_error += (
            len(members) / len(labels) * abs(mean_score - observed_rate)
        )
        calibration.append(
            {
                "bin": index + 1,
                "low": low,
                "high": high,
                "n": len(members),
                "mean_score": mean_score,
                "observed_rate": observed_rate,
                "absolute_gap": abs(mean_score - observed_rate),
            }
        )
    return calibration, expected_calibration_error


def _population_stability_index(
    reference_scores: list[float],
    current_scores: list[float],
    bins: int = 10,
) -> float:
    epsilon = 1e-6
    total = 0.0
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        reference_share = sum(
            low <= score < high or (index == bins - 1 and score == 1.0)
            for score in reference_scores
        ) / len(reference_scores)
        current_share = sum(
            low <= score < high or (index == bins - 1 and score == 1.0)
            for score in current_scores
        ) / len(current_scores)
        reference_share = max(reference_share, epsilon)
        current_share = max(current_share, epsilon)
        total += (current_share - reference_share) * math.log(
            current_share / reference_share
        )
    return total


def _ordered_periods(values: list[str]) -> tuple[list[str], str]:
    """Return periods in verified chronological or declared lifecycle order."""

    unique = list(dict.fromkeys(values))
    if len(unique) < 2:
        return unique, "single_period"
    numeric_values: dict[str, float] = {}
    numeric = True
    for value in unique:
        try:
            numeric_values[value] = float(value)
        except ValueError:
            numeric = False
            break
    if numeric:
        if len(set(numeric_values.values())) != len(numeric_values):
            raise ValueError(
                "Distinct period labels map to duplicate numeric time values."
            )
        return (
            sorted(unique, key=numeric_values.__getitem__),
            "numeric_ascending",
        )

    parsed_values: dict[str, datetime] = {}
    for value in unique:
        parsed: datetime | None = None
        normalized = value.strip()
        for pattern in ("%Y", "%Y-%m", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(normalized, pattern).replace(
                    tzinfo=timezone.utc
                )
                break
            except ValueError:
                pass
        if parsed is None:
            try:
                parsed = datetime.fromisoformat(
                    normalized.replace("Z", "+00:00")
                )
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                parsed = parsed.astimezone(timezone.utc)
            except ValueError:
                parsed = None
        if parsed is None:
            parsed_values = {}
            break
        parsed_values[value] = parsed
    if parsed_values:
        if len(set(parsed_values.values())) != len(parsed_values):
            raise ValueError(
                "Distinct period labels map to duplicate timestamps."
            )
        return (
            sorted(unique, key=parsed_values.__getitem__),
            "iso8601_chronological",
        )

    lifecycle_order = {
        "baseline": 0,
        "reference": 0,
        "training": 0,
        "validation": 1,
        "monitoring": 2,
        "current": 3,
        "latest": 3,
    }
    normalized_values = {value: value.casefold() for value in unique}
    if all(value in lifecycle_order for value in normalized_values.values()):
        order_keys = {
            label: lifecycle_order[value]
            for label, value in normalized_values.items()
        }
        if len(set(order_keys.values())) != len(order_keys):
            raise ValueError(
                "Period lifecycle labels are ambiguous; use ISO-8601 or numeric periods."
            )
        return sorted(unique, key=order_keys.__getitem__), "declared_lifecycle_order"

    raise ValueError(
        "Period values must be numeric, ISO-8601 dates/timestamps, or supported "
        "lifecycle labels (baseline/reference/training, validation, monitoring, current/latest)."
    )


def validate_predictions(
    rows: list[dict[str, str]],
    *,
    label_column: str,
    score_column: str,
    threshold: float = 0.5,
    group_column: str | None = None,
    period_column: str | None = None,
    calibration_bins: int = 10,
) -> dict[str, Any]:
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be a finite number between 0 and 1.")
    if not math.isfinite(float(threshold)) or not 0 <= float(threshold) <= 1:
        raise ValueError("threshold must be a finite number between 0 and 1.")
    if isinstance(calibration_bins, bool) or not isinstance(calibration_bins, int):
        raise ValueError("calibration_bins must be an integer.")
    if not 2 <= calibration_bins <= 100:
        raise ValueError("calibration_bins must be between 2 and 100.")
    if not rows:
        raise ValueError("At least one prediction row is required.")
    required_columns = {label_column, score_column}
    if group_column:
        required_columns.add(group_column)
    if period_column:
        required_columns.add(period_column)
    missing_columns = sorted(
        column
        for column in required_columns
        if not any(column in row for row in rows)
    )
    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing_columns) + "."
        )

    clean: list[dict[str, Any]] = []
    missing = 0
    for row in rows:
        if not row.get(label_column, "").strip() or not row.get(score_column, "").strip():
            missing += 1
            continue
        try:
            label_value = float(row[label_column])
            score = float(row[score_column])
        except ValueError as error:
            raise ValueError(
                f"{label_column} and {score_column} must be numeric."
            ) from error
        if not math.isfinite(label_value) or label_value not in {0.0, 1.0}:
            raise ValueError(f"{label_column} must contain only 0/1 values.")
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError(f"{score_column} must be between 0 and 1.")
        period = row.get(period_column, "").strip() if period_column else ""
        if period_column and not period:
            raise ValueError(
                f"{period_column} must be complete when period-based drift is requested."
            )
        clean.append(
            {
                "label": int(label_value),
                "score": score,
                "group": row.get(group_column, "").strip() if group_column else "",
                "period": period,
            }
        )
    if not clean:
        raise ValueError("No complete label-score rows were found.")
    if calibration_bins > len(clean):
        raise ValueError(
            "calibration_bins cannot exceed the number of complete observations."
        )
    labels = [row["label"] for row in clean]
    scores = [row["score"] for row in clean]
    overall = _classification_metrics(labels, scores, threshold)
    calibration, expected_calibration_error = _calibration(
        labels,
        scores,
        calibration_bins,
    )
    subgroup_metrics: dict[str, Any] = {}
    if group_column:
        for group in sorted({row["group"] for row in clean if row["group"]}):
            members = [row for row in clean if row["group"] == group]
            subgroup_metrics[group] = _classification_metrics(
                [row["label"] for row in members],
                [row["score"] for row in members],
                threshold,
            )
    drift = None
    period_ordering = None
    if period_column:
        periods, period_ordering = _ordered_periods(
            [row["period"] for row in clean]
        )
        if len(periods) >= 2:
            reference = periods[0]
            current = periods[-1]
            drift = {
                "reference_period": reference,
                "current_period": current,
                "period_ordering": period_ordering,
                "ordered_periods": periods,
                "population_stability_index": _population_stability_index(
                    [row["score"] for row in clean if row["period"] == reference],
                    [row["score"] for row in clean if row["period"] == current],
                ),
                "interpretation": (
                    "PSI is a descriptive score-distribution diagnostic; investigate "
                    "data, label, population, and policy changes before attributing a cause."
                ),
            }
    return {
        "analysis_type": "binary_prediction_validation",
        "data_quality": {
            "rows_received": len(rows),
            "rows_analyzed": len(clean),
            "rows_missing_label_or_score": missing,
            "threshold_validation": "finite_closed_unit_interval",
            "calibration_bins": calibration_bins,
            "period_ordering": period_ordering,
        },
        "overall": {
            **overall,
            "expected_calibration_error": expected_calibration_error,
        },
        "calibration": calibration,
        "subgroups": subgroup_metrics,
        "drift": drift,
        "interpretation_boundary": (
            "This evaluates predictions, not intervention effects. Threshold choice "
            "must reflect error costs, capacity, subgroup impacts, and contestability."
        ),
    }


def _metric_text(value: float | None, digits: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def _svg(result: dict[str, Any], title: str) -> str:
    height = 620
    left, top, size = 74, 162, 330
    body: list[str] = [
        rounded_rect(36, 134, 396, 402, fill=PAPER, stroke=GRID, radius=17),
        text(58, 160, "RELIABILITY", css="eyebrow"),
    ]
    for tick in range(5):
        value = tick / 4
        x = left + value * size
        y = top + (1 - value) * size
        body.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + size}" stroke="{GRID}"/>')
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + size}" y2="{y:.1f}" stroke="{GRID}"/>')
        body.append(text(x, top + size + 22, f"{value:.2g}", css="small", anchor="middle"))
        body.append(text(left - 12, y + 4, f"{value:.2g}", css="small", anchor="end"))
    body.extend(
        [
            f'<line x1="{left}" y1="{top + size}" x2="{left + size}" y2="{top}" stroke="{NAVY}" stroke-width="2" stroke-dasharray="7 6"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + size}" stroke="{INK}" stroke-width="1.5"/>',
            f'<line x1="{left}" y1="{top + size}" x2="{left + size}" y2="{top + size}" stroke="{INK}" stroke-width="1.5"/>',
        ]
    )
    points = []
    for item in result["calibration"]:
        x = left + item["mean_score"] * size
        y = top + (1 - item["observed_rate"]) * size
        points.append(f"{x:.1f},{y:.1f}")
        radius = min(15, 4 + math.sqrt(item["n"]))
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{VIOLET}" opacity=".84" stroke="{PAPER}" stroke-width="2"/>')
    if points:
        body.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{VIOLET}" stroke-width="3"/>')
    overall = result["overall"]
    cards = [
        ("DISCRIMINATION", "AUC", _metric_text(overall["auc"]), "higher separates classes"),
        ("PROBABILITY ERROR", "Brier", _metric_text(overall["brier_score"]), "lower is better"),
        ("CALIBRATION", "ECE", _metric_text(overall["expected_calibration_error"]), "lower average gap"),
        ("THRESHOLD", "Recall", _metric_text(overall["recall_sensitivity"]), f"at {overall['threshold']:.2f}"),
    ]
    for index, (kicker, label, value, note) in enumerate(cards):
        column = index % 2
        row = index // 2
        x = 454 + column * 352
        y = 134 + row * 112
        body.extend(
            [
                rounded_rect(x, y, 330, 94, fill=PAPER, stroke=GRID, radius=14),
                text(x + 18, y + 25, kicker, css="eyebrow"),
                text(x + 18, y + 54, label, css="section"),
                text(x + 306, y + 53, value, css="big", anchor="end", fill=VIOLET),
                text(x + 18, y + 78, note, css="small"),
            ]
        )
    body.append(rounded_rect(454, 370, 682, 166, fill=NAVY, stroke=NAVY, radius=16))
    body.append(text(476, 399, "DEPLOYMENT DIAGNOSTICS", css="eyebrow", fill=VIOLET))
    if result["subgroups"]:
        fprs = [
            value["false_positive_rate"]
            for value in result["subgroups"].values()
            if value["false_positive_rate"] is not None
        ]
        fnrs = [
            value["false_negative_rate"]
            for value in result["subgroups"].values()
            if value["false_negative_rate"] is not None
        ]
        fpr_gap = max(fprs) - min(fprs) if fprs else 0.0
        fnr_gap = max(fnrs) - min(fnrs) if fnrs else 0.0
        body.append(text(476, 438, f"{len(result['subgroups'])}", css="display", fill=PAPER))
        body.append(text(520, 438, "subgroups reviewed", css="label", fill="#C7D4E4"))
        body.append(text(476, 472, f"FPR range gap {fpr_gap:.1%}", css="section", fill=PAPER))
        body.append(text(476, 500, f"FNR range gap {fnr_gap:.1%}", css="section", fill=PAPER))
    else:
        body.append(text(476, 443, "No subgroup field supplied", css="section", fill=PAPER))
        body.append(text(476, 474, "Add affected groups before deployment review.", css="label", fill="#C7D4E4"))
    if result["drift"]:
        psi = result["drift"]["population_stability_index"]
        body.append(text(902, 438, f"{psi:.3f}", css="display", fill=PAPER, anchor="middle"))
        body.append(text(902, 466, "score PSI", css="label", fill="#C7D4E4", anchor="middle"))
        body.append(
            wrapped_text(
                902,
                494,
                result["drift"]["interpretation"],
                chars=37,
                line_height=16,
                css="small",
                fill="#C7D4E4",
                anchor="middle",
            )
        )
    else:
        body.append(text(902, 443, "Drift not supplied", css="section", fill=PAPER, anchor="middle"))
        body.append(text(902, 474, "Add time periods for stability review.", css="small", fill="#C7D4E4", anchor="middle"))
    body.extend(
        [
            text(left + size / 2, 526, "Mean predicted probability", css="small", anchor="middle"),
            text(64, top + size / 2, "Observed event rate", css="small", anchor="middle", transform=f"rotate(-90 64 {top + size / 2})"),
        ]
    )
    return svg_document(
        title,
        "Reliability, discrimination, calibration, threshold performance, subgroup error, and drift",
        "\n".join(body),
        height=height,
        accent=VIOLET,
        kicker="PREDICTION VALIDATION",
        source="Source: prediction-results.json",
        note="Prediction quality · not intervention effect",
        description=(
            "Reliability points are plotted against perfect calibration and sized by bin count. "
            "Cards show AUC, Brier score, calibration error, recall, subgroup error gaps, and drift."
        ),
    )


def render_report(result: dict[str, Any], title: str) -> str:
    overall = result["overall"]
    lines = [
        f"# {title}",
        "",
        "## Executive Summary",
        "",
        f"The model's AUC is **{_metric_text(overall['auc'])}**, Brier score is "
        f"**{overall['brier_score']:.3f}**, and expected calibration error is "
        f"**{overall['expected_calibration_error']:.3f}** on "
        f"**{overall['n']} reviewed observations**.",
        "",
        "![Prediction validation](prediction-validation.svg)",
        "",
        "## Key findings",
        "",
        "| Threshold | Accuracy | Precision | Recall | Specificity | FPR | FNR |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        f"| {overall['threshold']:.2f} | {overall['accuracy']:.1%} | "
        f"{_metric_text(overall['precision'])} | {_metric_text(overall['recall_sensitivity'])} | "
        f"{_metric_text(overall['specificity'])} | {_metric_text(overall['false_positive_rate'])} | "
        f"{_metric_text(overall['false_negative_rate'])} |",
        "",
    ]
    if result["subgroups"]:
        lines.extend(
            [
                "## Subgroup diagnostics",
                "",
                "| Group | n | Prevalence | AUC | Brier | FPR | FNR |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for group, metrics in result["subgroups"].items():
            lines.append(
                f"| {group} | {metrics['n']} | {metrics['prevalence']:.1%} | "
                f"{_metric_text(metrics['auc'])} | {metrics['brier_score']:.3f} | "
                f"{_metric_text(metrics['false_positive_rate'])} | "
                f"{_metric_text(metrics['false_negative_rate'])} |"
            )
        lines.append("")
    if result["drift"]:
        lines.extend(
            [
                "## Drift diagnostic",
                "",
                f"Score-distribution PSI from **{result['drift']['reference_period']}** to "
                f"**{result['drift']['current_period']}** is "
                f"**{result['drift']['population_stability_index']:.3f}**. "
                f"Periods were ordered using "
                f"`{result['drift']['period_ordering']}`. "
                f"{result['drift']['interpretation']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Recommended next steps",
            "",
            "1. Select the operating threshold from explicit error costs, capacity, and contestability.",
            "2. Investigate calibration, subgroup error, and drift before any deployment change.",
            "3. Revalidate on a time- or source-separated dataset and define monitoring triggers.",
            "",
            "## Further questions",
            "",
            "- Is the validation sample independent of model development and threshold selection?",
            "- Which subgroup error asymmetries are materially harmful in the decision context?",
            "- What action follows a high score, and is that action itself causally beneficial?",
            "",
            "## Caveats and assumptions",
            "",
            f"- {result['interpretation_boundary']}",
            f"- Missing label/score rows: {result['data_quality']['rows_missing_label_or_score']}",
            f"- Threshold validation: {result['data_quality']['threshold_validation']}",
            f"- Calibration bins: {result['data_quality']['calibration_bins']}",
            f"- Period ordering: {result['data_quality']['period_ordering'] or 'not requested'}",
            "- Validate on data separated in time or source from model development; this script "
            "does not certify independence or detect leakage automatically.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(result: dict[str, Any], output_dir: str | Path, title: str) -> tuple[Path, Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "prediction-results.json"
    report_path = directory / "prediction-report.md"
    figure_path = directory / "prediction-validation.svg"
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
    parser.add_argument("--label", required=True)
    parser.add_argument("--score", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--group")
    parser.add_argument("--period")
    parser.add_argument("--bins", type=int, default=10)
    parser.add_argument("--title", default="Prediction Model Validation")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    with Path(args.csv_path).open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = validate_predictions(
        rows,
        label_column=args.label,
        score_column=args.score,
        threshold=args.threshold,
        group_column=args.group,
        period_column=args.period,
        calibration_bins=args.bins,
    )
    paths = write_outputs(result, args.output_dir, args.title)
    print("\n".join(str(path) for path in paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
