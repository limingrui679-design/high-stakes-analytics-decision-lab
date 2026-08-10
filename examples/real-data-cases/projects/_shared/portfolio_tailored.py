#!/usr/bin/env python3
"""One-program/one-case real-data extensions.

These cases intentionally share infrastructure, not substantive claims.  Each
project has a different official or terms-governed source, analytical grain,
decision question, and terminal evidence boundary.
"""

from __future__ import annotations

import csv
import io
import json
import math
import random
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from portfolio_core import (
    PREPARERS,
    mean,
    quantile,
    read_csv,
    svg_bar,
    svg_interval,
    svg_line,
    write_csv,
)
from portfolio_reporting import ANALYZERS, REPORT_COPY, VISUAL_COPY
from portfolio_spatial import _haversine, analyze_spatial


def _number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _weighted_mean(values: Iterable[tuple[float, float]]) -> float:
    pairs = [(value, weight) for value, weight in values if weight > 0]
    total = sum(weight for _, weight in pairs)
    return sum(value * weight for value, weight in pairs) / total if total else 0.0


def _weighted_auc(rows: list[tuple[float, int, float]]) -> float:
    ordered = sorted(rows, key=lambda item: item[0])
    positive = sum(weight for _, label, weight in ordered if label == 1)
    negative = sum(weight for _, label, weight in ordered if label == 0)
    if not positive or not negative:
        return 0.5
    concordance = 0.0
    cumulative_negative = 0.0
    index = 0
    while index < len(ordered):
        score = ordered[index][0]
        group_positive = 0.0
        group_negative = 0.0
        while index < len(ordered) and ordered[index][0] == score:
            _, label, weight = ordered[index]
            if label:
                group_positive += weight
            else:
                group_negative += weight
            index += 1
        concordance += group_positive * (
            cumulative_negative + 0.5 * group_negative
        )
        cumulative_negative += group_negative
    return concordance / (positive * negative)


def _weighted_brier(rows: list[tuple[float, int, float]]) -> float:
    return _weighted_mean(((score - label) ** 2, weight) for score, label, weight in rows)


def _weighted_rate(rows: list[dict[str, Any]], outcome: str) -> float:
    return _weighted_mean(
        (_number(row[outcome]), max(_number(row.get("weight"), 1.0), 0.0))
        for row in rows
    )


def _copy_csv_prepare(
    project_root: Path,
    filename: str,
    *,
    grain: str,
    primary_key: str | list[str] | None,
    target: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = read_csv(project_root / "data/raw" / filename)
    write_csv(project_root / "data/processed/analysis.csv", rows, list(rows[0]))
    dictionary: dict[str, Any] = {
        "grain": grain,
        "primary_key": primary_key,
        "fields": {field: field.replace("_", " ") for field in rows[0]},
    }
    if target:
        dictionary["target"] = target
    return rows, dictionary


def prepare_nhis(project_root: Path):
    rows, dictionary = _copy_csv_prepare(
        project_root,
        "nhis-2016-2017-linked-mortality-extract.csv",
        grain="NHIS sampled adult linked to public mortality status",
        primary_key="publicid",
        target="death_within_two_years",
    )
    dictionary["claim_boundary"] = (
        "Survey-linked observational prediction; no diagnosis, treatment, or "
        "individual clinical recommendation."
    )
    return rows, dictionary


def prepare_bike(project_root: Path):
    source = project_root / "data/raw/citibike-jc-2021-station-hour.csv"
    aggregates: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {"pickups": 0, "returns": 0, "dates": set()}
    )
    station: dict[str, tuple[str, str, str]] = {}
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["date"][:7], row["hour"], row["station_id"])
            aggregates[key]["pickups"] += int(row["pickups"])
            aggregates[key]["returns"] += int(row["returns"])
            aggregates[key]["dates"].add(row["date"])
            station[row["station_id"]] = (
                row["station_name"],
                row["latitude"],
                row["longitude"],
            )
    rows = []
    for (month, hour, station_id), item in sorted(aggregates.items()):
        name, latitude, longitude = station[station_id]
        rows.append(
            {
                "month": month,
                "hour": hour,
                "station_id": station_id,
                "station_name": name,
                "latitude": latitude,
                "longitude": longitude,
                "observed_days": len(item["dates"]),
                "pickups": item["pickups"],
                "returns": item["returns"],
            }
        )
    write_csv(project_root / "data/processed/analysis.csv", rows, list(rows[0]))
    return rows, {
        "grain": "Jersey City station-hour-month",
        "primary_key": ["month", "hour", "station_id"],
        "fields": {field: field.replace("_", " ") for field in rows[0]},
        "modeled_quantity_boundary": (
            "Residual imbalance is a planning scenario derived from observed "
            "pickups and returns, not an observed service improvement."
        ),
    }


def _age_band(age: int) -> str:
    if age < 35:
        return "18-34"
    if age < 50:
        return "35-49"
    return "50-64"


def _education_band(code: int) -> str:
    if code <= 15:
        return "below_high_school"
    if code <= 19:
        return "high_school_some_college"
    if code <= 21:
        return "associate_bachelor"
    return "graduate"


def prepare_pums(project_root: Path):
    rows = []
    fields = [
        "person_id",
        "cohort",
        "weight",
        "age",
        "age_band",
        "education_band",
        "worker_class",
        "puma",
        "sex",
        "race",
        "hispanic_origin",
        "employed",
    ]
    for year in (2019, 2023):
        archive_path = project_root / f"data/raw/acs{year}-ri-person-pums.zip"
        with zipfile.ZipFile(archive_path) as archive:
            member = next(name for name in archive.namelist() if name.endswith(".csv"))
            with archive.open(member) as source:
                reader = csv.DictReader(io.TextIOWrapper(source, encoding="utf-8-sig"))
                for row in reader:
                    age = int(row["AGEP"])
                    if not 18 <= age <= 64 or row.get("ESR") not in {
                        "1", "2", "3", "4", "5", "6"
                    }:
                        continue
                    rows.append(
                        {
                            "person_id": f"{year}-{row['SERIALNO']}-{row['SPORDER']}",
                            "cohort": year,
                            "weight": row["PWGTP"],
                            "age": age,
                            "age_band": _age_band(age),
                            "education_band": _education_band(int(row.get("SCHL") or 0)),
                            "worker_class": row.get("COW") or "missing",
                            "puma": row["PUMA"],
                            "sex": row["SEX"],
                            "race": row["RAC1P"],
                            "hispanic_origin": row["HISP"],
                            "employed": int(row["ESR"] in {"1", "2", "4", "5"}),
                        }
                    )
    write_csv(project_root / "data/processed/analysis.csv", rows, fields)
    return rows, {
        "grain": "ACS PUMS working-age person record",
        "primary_key": "person_id",
        "target": "employed",
        "train_test_contract": "2019 model development; 2023 temporal transport test",
        "protected_attribute_contract": (
            "Sex, race, and Hispanic origin are used only for audit slices, "
            "not as model inputs."
        ),
        "fields": {field: field.replace("_", " ") for field in fields},
    }


def prepare_nport(project_root: Path):
    return _copy_csv_prepare(
        project_root,
        "sec-nport-2025q4-fund-risk.csv",
        grain="one Form N-PORT fund filing snapshot",
        primary_key="accession_number",
    )


ONTOLOGY = (
    (
        "sanitation",
        ("garbage", "trash", "waste", "recycl", "rodent", "litter", "sanitation"),
    ),
    (
        "transport_public_realm",
        ("street", "pothole", "sidewalk", "traffic", "vehicle", "alley", "sign", "light"),
    ),
    (
        "housing_buildings",
        ("building", "housing", "heat", "plumb", "sewer", "water", "elevator"),
    ),
    ("noise", ("noise",)),
    (
        "information_administration",
        ("information", "general", "request", "complaint", "service"),
    ),
)


def _service_family(category: str) -> str:
    folded = category.casefold()
    for family, tokens in ONTOLOGY:
        if any(token in folded for token in tokens):
            return family
    return "other"


def prepare_311(project_root: Path):
    source = read_csv(project_root / "data/raw/cross-city-311-daily.csv")
    totals: Counter[tuple[str, str, str]] = Counter()
    raw_categories: dict[str, Counter[str]] = defaultdict(Counter)
    for row in source:
        family = _service_family(row["category"])
        count = int(row["requests"])
        totals[(row["city"], row["date"], family)] += count
        raw_categories[row["city"]][family] += count
    rows = [
        {"city": city, "date": day, "service_family": family, "requests": value}
        for (city, day, family), value in sorted(totals.items())
    ]
    write_csv(project_root / "data/processed/analysis.csv", rows, list(rows[0]))
    return rows, {
        "grain": "city-day-audited service-family aggregate",
        "primary_key": ["city", "date", "service_family"],
        "ontology": {family: list(tokens) for family, tokens in ONTOLOGY},
        "unmapped_policy": "Preserve unmatched source categories in `other`.",
        "mapped_request_totals": {
            city: dict(counts) for city, counts in raw_categories.items()
        },
        "fields": {field: field.replace("_", " ") for field in rows[0]},
    }


def prepare_fire(project_root: Path):
    return _copy_csv_prepare(
        project_root,
        "calfire-fire-perimeters-2000-2025.csv",
        grain="one historical fire-perimeter record",
        primary_key="OBJECTID",
    )


def prepare_social(project_root: Path):
    rows, dictionary = _copy_csv_prepare(
        project_root,
        "terms-compliant-treatment-aggregate.csv",
        grain="treatment by prior-turnout aggregate",
        primary_key=["treatment", "prior_turnout_stratum"],
    )
    dictionary["restricted_source_contract"] = (
        "Participant rows were used locally to compute household-clustered "
        "statistics and were not copied into the repository."
    )
    return rows, dictionary


def prepare_qoz(project_root: Path):
    return _copy_csv_prepare(
        project_root,
        "massachusetts-qoz-tract-panel.csv",
        grain="Massachusetts tract-year panel row",
        primary_key=["geoid", "year"],
    )


def prepare_nhanes(project_root: Path):
    return _copy_csv_prepare(
        project_root,
        "nhanes-36-month-mortality-cohorts.csv",
        grain="NHANES adult linked to 36-month mortality follow-up",
        primary_key=["cohort", "seqn"],
        target="death_within_36_months",
    )


def _calibration(rows: list[tuple[float, int, float]], groups: int = 5):
    ordered = sorted(rows, key=lambda item: item[0])
    chunks = []
    for index in range(groups):
        left = index * len(ordered) // groups
        right = (index + 1) * len(ordered) // groups
        part = ordered[left:right]
        if not part:
            continue
        chunks.append(
            {
                "predicted": _weighted_mean((score, weight) for score, _, weight in part),
                "observed": _weighted_mean((label, weight) for _, label, weight in part),
                "rows": len(part),
            }
        )
    return chunks


def analyze_nhis(project_root: Path):
    rows = read_csv(project_root / "data/processed/analysis.csv")
    materialized = []
    for row in rows:
        age = int(row["age"])
        conditions = sum(
            (
                row["hypertension"] == "1",
                row["diabetes"] == "1",
                row["ever_smoked"] == "1",
            )
        )
        band = "18-44" if age < 45 else "45-64" if age < 65 else "65-74" if age < 75 else "75+"
        materialized.append(
            {
                **row,
                "age_band": band,
                "condition_count": conditions,
                "weight": max(_number(row["survey_weight"], 1.0), 1.0),
                "outcome": int(row["death_within_two_years"]),
            }
        )
    train = [row for row in materialized if row["cohort_year"] == "2016"]
    test = [row for row in materialized if row["cohort_year"] == "2017"]
    global_rate = _weighted_mean((row["outcome"], row["weight"]) for row in train)
    cells: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in train:
        cells[(row["age_band"], row["condition_count"])].append(row)
    rates = {
        key: _weighted_mean((row["outcome"], row["weight"]) for row in group)
        for key, group in cells.items()
    }
    scored = []
    for row in test:
        score = rates.get((row["age_band"], row["condition_count"]), global_rate)
        row["score"] = score
        scored.append((score, row["outcome"], row["weight"]))
    cohort_rates = {
        cohort: _weighted_mean((row["outcome"], row["weight"]) for row in materialized if row["cohort_year"] == cohort)
        for cohort in ("2016", "2017")
    }
    protocols = {}
    ordered = sorted(test, key=lambda row: row["score"], reverse=True)
    total_events = sum(row["outcome"] * row["weight"] for row in test)
    for share in (0.10, 0.20, 0.30):
        selected = ordered[: max(1, int(len(ordered) * share))]
        capture = sum(row["outcome"] * row["weight"] for row in selected) / total_events
        selected_by_sex = {
            sex: sum(row["weight"] for row in selected if row["sex"] == sex)
            / sum(row["weight"] for row in test if row["sex"] == sex)
            for sex in ("1", "2")
        }
        protocols[f"top-{int(share*100)}%-review"] = {
            "high_risk_capture": capture,
            "workload_share": len(selected) / len(test),
            "sex_selection_gap": abs(selected_by_sex["1"] - selected_by_sex["2"]),
        }
    calibration = _calibration(scored)
    figures = project_root / "outputs/figures"
    source = "CDC/NCHS NHIS 2016-2017 linked mortality public-use files"
    svg_bar(figures / "cohort-mortality.svg", "Survey-weighted two-year mortality", "Observed linked outcomes by cohort", [(key, value) for key, value in cohort_rates.items()], source, percent=True)
    age_rates = {
        band: _weighted_mean((row["outcome"], row["weight"]) for row in test if row["age_band"] == band)
        for band in ("18-44", "45-64", "65-74", "75+")
    }
    svg_bar(figures / "age-gradient.svg", "Mortality gradient by age band", "2017 temporal test cohort", list(age_rates.items()), source, percent=True)
    svg_line(figures / "temporal-calibration.svg", "Temporal calibration", "2016 cell rates evaluated in 2017", [("observed", [(item["predicted"], item["observed"]) for item in calibration]), ("ideal", [(0.0, 0.0), (max(item["predicted"] for item in calibration), max(item["predicted"] for item in calibration))])], source, y_percent=True)
    return {
        "project_id": "population-health-survival",
        "data": {"rows": len(materialized), "train_rows": len(train), "test_rows": len(test)},
        "study_design": {"design": "survey-linked observational temporal validation", "development_cohort": "NHIS 2016", "test_cohort": "NHIS 2017", "estimand": "survey-weighted two-year mortality association"},
        "temporal_validation": {"auc": _weighted_auc(scored), "brier": _weighted_brier(scored), "calibration": calibration},
        "cohort_mortality": cohort_rates,
        "candidate_protocols": protocols,
        "headline_metrics": [f"2017 temporal-test AUC: {_weighted_auc(scored):.3f}", f"2017 weighted two-year mortality: {cohort_rates['2017']:.2%}", f"Linked adult records: {len(materialized):,}", "Terminal use: research triage validation only"],
        "decision_support": {"status": "prospective_validation_required", "reversal_conditions": ["A later linked cohort materially changes calibration.", "Survey design review changes the weighting or variance treatment.", "Clinical stakeholders reject the non-diagnostic triage endpoint."]},
    }


def analyze_bike(project_root: Path):
    rows = read_csv(project_root / "data/processed/analysis.csv")
    materialized = []
    for row in rows:
        days = max(int(row["observed_days"]), 1)
        materialized.append({**row, "pickups_per_day": int(row["pickups"]) / days, "returns_per_day": int(row["returns"]) / days, "days": days})
    train = [row for row in materialized if row["month"] <= "2021-09"]
    test = [row for row in materialized if row["month"] >= "2021-10"]
    by_station_hour: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_hour: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in train:
        by_station_hour[(row["station_id"], row["hour"])].append(row)
        by_hour[row["hour"]].append(row)
    prediction = {key: _weighted_mean((row["pickups_per_day"], row["days"]) for row in group) for key, group in by_station_hour.items()}
    hour_prediction = {key: _weighted_mean((row["pickups_per_day"], row["days"]) for row in group) for key, group in by_hour.items()}
    errors = []
    baseline_errors = []
    for row in test:
        actual = row["pickups_per_day"]
        errors.append((abs(actual - prediction.get((row["station_id"], row["hour"]), hour_prediction[row["hour"]])), row["days"]))
        baseline_errors.append((abs(actual - hour_prediction[row["hour"]]), row["days"]))
    mae = _weighted_mean(errors)
    baseline_mae = _weighted_mean(baseline_errors)
    training_deficit: Counter[tuple[str, str]] = Counter()
    for row in train:
        training_deficit[(row["station_id"], row["hour"])] += max(0.0, row["pickups_per_day"] - row["returns_per_day"])
    ranked_keys = [key for key, _ in training_deficit.most_common()]
    budget = float(json.loads((project_root / "config.json").read_text())["parameters"]["modeled_daily_rebalancing_units"])
    options = {}
    for count in (0, 10, 25):
        chosen = set(ranked_keys[:count])
        denominator = sum(training_deficit[key] for key in chosen)
        allocation = {key: (budget * training_deficit[key] / denominator if denominator else 0.0) for key in chosen}
        observed = 0.0
        residual = 0.0
        uncovered = 0
        for row in test:
            deficit = max(0.0, row["pickups_per_day"] - row["returns_per_day"])
            observed += deficit * row["days"]
            remaining = max(0.0, deficit - allocation.get((row["station_id"], row["hour"]), 0.0))
            residual += remaining * row["days"]
            uncovered += int(remaining > 0)
        shares = [value / budget for value in allocation.values()] if budget else []
        options[f"top-{count}-station-hours" if count else "monitoring-only"] = {
            "modeled_residual_imbalance": residual / observed if observed else 0.0,
            "unserved_station_hour_share": uncovered / len(test),
            "allocation_concentration": sum(value * value for value in shares),
            "modeled_units_per_day": budget if count else 0.0,
        }
    monthly = Counter()
    for row in materialized:
        monthly[row["month"]] += int(row["pickups"])
    figures = project_root / "outputs/figures"
    source = "Citi Bike Jersey City trip history, 2021"
    svg_bar(figures / "forecast-mae.svg", "Held-out forecast error", "October-December 2021 weighted MAE", [("hour-only baseline", baseline_mae), ("station-hour history", mae)], source)
    svg_line(figures / "monthly-demand.svg", "Observed monthly pickups", "All Jersey City stations", [("pickups", [(index + 1, monthly[f"2021-{index+1:02d}"]) for index in range(12)])], source)
    svg_bar(figures / "modeled-imbalance.svg", "Modeled residual imbalance", "Scenario output; not observed service improvement", [(key, value["modeled_residual_imbalance"]) for key, value in options.items()], source, percent=True)
    improvement = 1 - mae / baseline_mae
    return {
        "project_id": "bike-demand-operations",
        "data": {"rows": len(materialized), "train_rows": len(train), "test_rows": len(test)},
        "study_design": {"design": "station-hour temporal holdout", "development_period": "January-September 2021", "test_period": "October-December 2021", "modeled_scenario": "fixed daily rebalancing-unit budget"},
        "forecast": {"station_hour_mae": mae, "hour_baseline_mae": baseline_mae, "relative_mae_improvement": improvement},
        "decision_options": options,
        "optimization": {"policies_2012_evaluation": options},
        "headline_metrics": [f"Held-out station-hour MAE: {mae:.2f} pickups/day", f"Improvement vs hour-only baseline: {improvement:.1%}", f"Observed station-hour-month rows: {len(materialized):,}", "Rebalancing results: modeled scenario only"],
        "decision_support": {"status": "bounded_operations_pilot_only", "reversal_conditions": ["Travel-time or truck-capacity constraints make the allocation infeasible.", "A later seasonal holdout reverses the station-hour ranking.", "Observed dock inventory invalidates pickups-minus-returns as an imbalance proxy."]},
    }


def _group_rate_model(train: list[dict[str, str]]):
    groups: dict[tuple[str, str, str, str], list[tuple[int, float]]] = defaultdict(list)
    global_rate = _weighted_mean((int(row["employed"]), _number(row["weight"])) for row in train)
    for row in train:
        key = (row["age_band"], row["education_band"], row["worker_class"], row["puma"])
        groups[key].append((int(row["employed"]), _number(row["weight"])))
    rates = {}
    for key, values in groups.items():
        total = sum(weight for _, weight in values)
        rates[key] = (sum(label * weight for label, weight in values) + global_rate * 100) / (total + 100)
    return rates, global_rate


def analyze_pums(project_root: Path):
    rows = read_csv(project_root / "data/processed/analysis.csv")
    train = [row for row in rows if row["cohort"] == "2019"]
    test = [row for row in rows if row["cohort"] == "2023"]
    rates, global_rate = _group_rate_model(train)
    scored = []
    enriched = []
    for row in test:
        key = (row["age_band"], row["education_band"], row["worker_class"], row["puma"])
        score = rates.get(key, global_rate)
        scored.append((score, int(row["employed"]), _number(row["weight"])))
        enriched.append((row, score))
    calibration = _calibration(scored)
    subgroup = {}
    for field in ("sex", "race"):
        subgroup[field] = {}
        for value in sorted({row[field] for row in test}):
            subset = [(score, int(row["employed"]), _number(row["weight"])) for row, score in enriched if row[field] == value]
            if len(subset) >= 30:
                subgroup[field][value] = {"rows": len(subset), "auc": _weighted_auc(subset), "brier": _weighted_brier(subset), "employment_rate": _weighted_mean((label, weight) for _, label, weight in subset)}
    cohort_rates = {year: _weighted_mean((int(row["employed"]), _number(row["weight"])) for row in rows if row["cohort"] == year) for year in ("2019", "2023")}
    figures = project_root / "outputs/figures"
    source = "U.S. Census Bureau ACS PUMS, Rhode Island 2019 and 2023"
    auc = _weighted_auc(scored)
    brier = _weighted_brier(scored)
    svg_bar(figures / "temporal-performance.svg", "Temporal model validation", "2019 development to 2023 transport", [("AUC", auc), ("1 - Brier", 1 - brier)], source)
    svg_line(figures / "calibration.svg", "2023 calibration", "Predicted versus survey-weighted observed employment", [("observed", [(item["predicted"], item["observed"]) for item in calibration]), ("ideal", [(0.0, 0.0), (1.0, 1.0)])], source, y_percent=True)
    sex_rates = [(f"sex code {key}", value["employment_rate"]) for key, value in subgroup["sex"].items()]
    svg_bar(figures / "audit-slices.svg", "Protected-attribute audit slices", "2023 weighted employment rates; attributes excluded from model inputs", sex_rates, source, percent=True)
    return {
        "project_id": "census-income-ai",
        "data": {"rows": len(rows), "train_rows": len(train), "test_rows": len(test)},
        "study_design": {"design": "survey-weighted temporal transport test", "model_inputs": ["age band", "education band", "worker class", "PUMA"], "audit_only_fields": ["sex", "race", "Hispanic origin"], "target": "current employment status"},
        "temporal_test": {"auc": auc, "brier": brier, "calibration": calibration},
        "cohort_employment_rates": cohort_rates,
        "subgroup_audit": subgroup,
        "deployment_gate": {"status": "do_not_use_for_consequential_action", "passes": False, "reversal_conditions": ["A current external population reproduces calibration and subgroup performance.", "A real decision owner supplies a lawful, valid target and governance review.", "Protected-class audit and error-cost review support a bounded use."]},
        "headline_metrics": [f"2023 temporal-test AUC: {auc:.3f}", f"2023 weighted Brier score: {brier:.3f}", f"2019/2023 analyzed people: {len(train):,} / {len(test):,}", "Decision status: no consequential use"],
    }


def _ranks(values: list[float], *, reverse: bool = False) -> list[float]:
    ordered = sorted(range(len(values)), key=lambda index: values[index], reverse=reverse)
    result = [0.0] * len(values)
    denominator = max(1, len(values) - 1)
    for rank, index in enumerate(ordered):
        result[index] = rank / denominator
    return result


def analyze_nport(project_root: Path):
    rows = read_csv(project_root / "data/processed/analysis.csv")
    fields = ["top10_concentration", "restricted_share", "fair_value_level3_share", "crowded_security_share", "three_month_redemption_share"]
    ranks = {field: _ranks([_number(row[field]) for row in rows]) for field in fields}
    low_cash_rank = _ranks([_number(row["cash_like_share"]) for row in rows], reverse=True)
    scores = []
    for index, row in enumerate(rows):
        score = mean([ranks[field][index] for field in fields] + [low_cash_rank[index]])
        scores.append(score)
        row["risk_review_score"] = score
    order = sorted(range(len(rows)), key=lambda index: scores[index], reverse=True)
    high_risk = set(order[: max(1, int(len(rows) * 0.10))])
    options = {}
    for share in (0.05, 0.10, 0.20):
        selected = set(order[: max(1, int(len(rows) * share))])
        options[f"review-top-{int(share*100)}%"] = {
            "review_share": len(selected) / len(rows),
            "high_risk_capture": len(selected & high_risk) / len(high_risk),
            "average_review_score": mean(scores[index] for index in selected),
        }
    quantiles = {field: {"p50": quantile([_number(row[field]) for row in rows], 0.5), "p90": quantile([_number(row[field]) for row in rows], 0.9), "p99": quantile([_number(row[field]) for row in rows], 0.99)} for field in fields + ["cash_like_share"]}
    figures = project_root / "outputs/figures"
    source = "SEC Form N-PORT Data Set, 2025 Q4"
    svg_bar(figures / "risk-indicator-p90.svg", "Fund risk-indicator 90th percentiles", "Observed filing values; not expected returns", [(field.replace("_", " "), value["p90"]) for field, value in quantiles.items()], source, percent=True)
    deciles = []
    sorted_scores = sorted(scores)
    for decile in range(10):
        block = sorted_scores[decile * len(scores) // 10:(decile + 1) * len(scores) // 10]
        deciles.append((str(decile + 1), mean(block)))
    svg_bar(figures / "review-score-deciles.svg", "Composite review-score deciles", "Percentile-based filing screen", deciles, source)
    svg_bar(figures / "review-capacity.svg", "Review threshold trade-off", "Capture of the internally defined top-risk decile", [(key, value["high_risk_capture"]) for key, value in options.items()], source, percent=True)
    return {
        "project_id": "sec-nport-filing-review",
        "data": {"rows": len(rows), "filing_period": "2025 Q4"},
        "study_design": {"design": "cross-sectional regulatory filing screen", "unit": "fund filing", "decision_use": "targeted filing review only", "forbidden_use": "investment recommendation or expected-return claim"},
        "indicator_quantiles": quantiles,
        "decision_options": options,
        "headline_metrics": [f"Reviewed fund filings: {len(rows):,}", f"Median top-10 holding concentration: {quantiles['top10_concentration']['p50']:.1%}", f"90th-percentile Level-3 share: {quantiles['fair_value_level3_share']['p90']:.1%}", "Terminal use: targeted filing review only"],
        "decision_support": {"status": "targeted_filing_review_only", "reversal_conditions": ["A filing amendment changes a fund's reported holdings or flows.", "A domain reviewer rejects the percentile-based composite score.", "A different filing population changes the risk-indicator distribution."]},
    }


def _distribution_distance(left: dict[str, float], right: dict[str, float]) -> tuple[float, float]:
    keys = set(left) | set(right)
    left_total, right_total = sum(left.values()), sum(right.values())
    p = {key: left.get(key, 0.0) / left_total for key in keys}
    q = {key: right.get(key, 0.0) / right_total for key in keys}
    tv = 0.5 * sum(abs(p[key] - q[key]) for key in keys)
    midpoint = {key: 0.5 * (p[key] + q[key]) for key in keys}
    def kl(source, target):
        return sum(source[key] * math.log(source[key] / target[key], 2) for key in keys if source[key] > 0)
    return tv, 0.5 * kl(p, midpoint) + 0.5 * kl(q, midpoint)


def analyze_311(project_root: Path):
    rows = read_csv(project_root / "data/processed/analysis.csv")
    totals: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    daily: dict[tuple[str, str], int] = Counter()
    for row in rows:
        year = row["date"][:4]
        value = int(row["requests"])
        totals[(row["city"], year)][row["service_family"]] += value
        daily[(row["city"], row["date"])] += value
    cities = ("Chicago", "New York City")
    within = {city: dict(zip(("total_variation", "jensen_shannon_bits"), _distribution_distance(totals[(city, "2022")], totals[(city, "2023")]))) for city in cities}
    cross_tv, cross_js = _distribution_distance(totals[("Chicago", "2023")], totals[("New York City", "2023")])
    threshold = json.loads((project_root / "config.json").read_text())["parameters"]["maximum_transfer_total_variation"]
    families = sorted({row["service_family"] for row in rows})
    shares_2023 = {city: {family: totals[(city, "2023")][family] / sum(totals[(city, "2023")].values()) for family in families} for city in cities}
    figures = project_root / "outputs/figures"
    source = "Chicago and New York City official 311 open-data APIs, 2022-2023"
    svg_bar(figures / "service-mix-2023.svg", "2023 service-family mix", "Audited keyword ontology; `other` remains visible", [(f"{city}: {family}", shares_2023[city][family]) for city in cities for family in families], source, percent=True)
    svg_bar(figures / "within-city-shift.svg", "Within-city category shift", "2022 to 2023 total-variation distance", [(city, within[city]["total_variation"]) for city in cities], source, percent=True, benchmark=threshold)
    monthly: dict[tuple[str, str], int] = Counter()
    for (city, day), value in daily.items():
        monthly[(city, day[:7])] += value
    svg_line(figures / "monthly-requests.svg", "Monthly 311 request volume", "Observed requests; city systems have different intake definitions", [(city, [(index + 1, monthly[(city, f"2023-{index+1:02d}")]) for index in range(12)]) for city in cities], source)
    mapped_share = {city: 1 - shares_2023[city].get("other", 0.0) for city in cities}
    return {
        "project_id": "cross-city-311-shift",
        "data": {"rows": len(rows), "cities": list(cities), "years": [2022, 2023]},
        "study_design": {"design": "cross-city administrative distribution-shift audit", "ontology": "versioned keyword mapping with unmatched `other`", "claim_class": "descriptive transportability diagnostic"},
        "within_city_shift": within,
        "cross_city_2023": {"total_variation": cross_tv, "jensen_shannon_bits": cross_js},
        "ontology_coverage": mapped_share,
        "transfer_gate": {"threshold": threshold, "passes": cross_tv <= threshold, "status": "transfer_refused" if cross_tv > threshold else "transfer_requires_local_validation", "reversal_conditions": ["The two cities adopt a harmonized service taxonomy.", "A reviewed crosswalk materially reduces the measured distance.", "A local validation period supports stable transfer."]},
        "headline_metrics": [f"Cross-city 2023 total-variation distance: {cross_tv:.1%}", f"Chicago mapped share: {mapped_share['Chicago']:.1%}", f"New York mapped share: {mapped_share['New York City']:.1%}", f"Transfer gate: {'refused' if cross_tv > threshold else 'local validation required'}"],
    }


def _normalize(counter: Counter[str]) -> dict[str, float]:
    total = sum(counter.values())
    return {key: value / total for key, value in counter.items()} if total else {}


def analyze_fire(project_root: Path):
    rows = read_csv(project_root / "data/processed/analysis.csv")
    valid = [row for row in rows if 2000 <= int(_number(row["YEAR_"])) <= 2025 and _number(row["GIS_ACRES"]) > 0]
    historical, recent, tail, frequency = Counter(), Counter(), Counter(), Counter()
    yearly = Counter()
    acres = sorted(_number(row["GIS_ACRES"]) for row in valid)
    tail_cut = quantile(acres, 0.90)
    for row in valid:
        year = int(row["YEAR_"])
        unit = row["UNIT_ID"] or "UNSPECIFIED"
        area = _number(row["GIS_ACRES"])
        yearly[year] += area
        if year <= 2019:
            historical[unit] += area
        if 2020 <= year <= 2024:
            recent[unit] += area
        if area >= tail_cut and year <= 2024:
            tail[unit] += area
        if year <= 2024:
            frequency[unit] += 1
    scenarios = {"historical_acres": _normalize(historical), "recent_acres": _normalize(recent), "tail_acres": _normalize(tail)}
    allocations = {"frequency": _normalize(frequency), "recent_acres": _normalize(recent)}
    units = set().union(*[set(item) for item in scenarios.values()])
    robust = {unit: mean(scenario.get(unit, 0.0) for scenario in scenarios.values()) for unit in units}
    allocations["robust_blend"] = _normalize(Counter(robust))
    coverage = {name: {scenario: sum(min(weights.get(unit, 0.0), exposure.get(unit, 0.0)) for unit in units) for scenario, exposure in scenarios.items()} for name, weights in allocations.items()}
    best = {scenario: max(value[scenario] for value in coverage.values()) for scenario in scenarios}
    options = {}
    for name, weights in allocations.items():
        regrets = [best[scenario] - coverage[name][scenario] for scenario in scenarios]
        options[name] = {"worst_case_regret": max(regrets), "minimum_scenario_alignment": min(coverage[name].values()), "allocation_concentration": sum(value * value for value in weights.values()), "scenario_alignment": coverage[name]}
    figures = project_root / "outputs/figures"
    source = "CAL FIRE California Historic Fire Perimeters, accessed 2026-08-10"
    svg_line(figures / "annual-observed-acres.svg", "Observed mapped fire-perimeter acres", "2025 may be incomplete; no acres-prevented claim", [("acres", [(year, yearly[year]) for year in range(2000, 2026)])], source)
    svg_bar(figures / "recent-unit-exposure.svg", "Recent observed unit exposure", "Top unit IDs by mapped 2020-2024 acres", recent.most_common(10), source)
    svg_bar(figures / "scenario-regret.svg", "Worst-case allocation regret", "Modeled alignment across historical, recent, and tail exposure", [(name, value["worst_case_regret"]) for name, value in options.items()], source, percent=True)
    preferred = min(options, key=lambda name: options[name]["worst_case_regret"])
    return {
        "project_id": "wildfire-mitigation-under-uncertainty",
        "data": {"rows": len(rows), "valid_area_records": len(valid), "partial_year": 2025},
        "study_design": {"design": "robust allocation stress test over observed exposure scenarios", "outcome": "alignment with mapped historical exposure", "not_estimated": "fires or acres prevented"},
        "observed_exposure": {"annual_acres": dict(yearly), "tail_cutoff_acres": tail_cut},
        "decision_options": options,
        "decision_support": {"status": "evidence_request_before_mitigation_allocation", "lowest_regret_option": preferred, "reversal_conditions": ["Local prevention effectiveness estimates become available.", "Unit boundaries or 2025 perimeter records are materially revised.", "Feasibility, ecology, or community constraints rule out the modeled allocation."]},
        "headline_metrics": [f"Valid mapped perimeters: {len(valid):,}", f"90th-percentile perimeter size: {tail_cut:,.0f} acres", f"Lowest-regret proxy allocation: {preferred.replace('_', ' ')}", "Terminal status: request effectiveness and feasibility evidence"],
    }


def analyze_social(project_root: Path):
    rows = read_csv(project_root / "data/processed/analysis.csv")
    summary = json.loads((project_root / "data/raw/cluster-robust-itt.json").read_text())
    effects = {item["treatment"]: item for item in summary["effects"]}
    aggregate: dict[str, dict[str, int]] = defaultdict(lambda: {"individuals": 0, "voters": 0})
    strata: dict[tuple[str, str], float] = {}
    for row in rows:
        aggregate[row["treatment"]]["individuals"] += int(row["individuals"])
        aggregate[row["treatment"]]["voters"] += int(row["voters"])
        strata[(row["treatment"], row["prior_turnout_stratum"])] = _number(row["turnout_rate"])
    rates = {treatment: value["voters"] / value["individuals"] for treatment, value in aggregate.items()}
    figures = project_root / "outputs/figures"
    source = "Yale ISPS D001 Gerber-Green-Larimer social-pressure field experiment"
    svg_bar(figures / "treatment-turnout.svg", "Observed turnout by randomized arm", "Intent-to-treat outcome", sorted(rates.items()), source, percent=True)
    svg_interval(figures / "cluster-robust-itt.svg", "Household-clustered intent-to-treat effects", "Percentage-point difference versus control", [(name, item["intent_to_treat_difference"] * 100, item["confidence_interval_95"][0] * 100, item["confidence_interval_95"][1] * 100) for name, item in effects.items()], source)
    strata_effects = []
    for treatment in sorted(effects):
        for stratum in ("not_prior_primary_voter", "prior_primary_voter"):
            strata_effects.append((f"{treatment}: {stratum}", strata[(treatment, stratum)] - strata[("Control", stratum)]))
    svg_bar(figures / "stratum-effects.svg", "Turnout differences within prior-vote strata", "Descriptive subgroup contrasts versus control", strata_effects, source, percent=True)
    largest = max(effects.values(), key=lambda item: item["intent_to_treat_difference"])
    return {
        "project_id": "social-norm-field-experiment",
        "data": {"aggregate_rows": len(rows), "source_individuals": summary["source_rows_used"]},
        "study_design": {"design": "household-randomized field experiment", "estimand": summary["estimand"], "variance": summary["variance_estimator"], "repository_storage": "non-identifying aggregates only"},
        "turnout_rates": rates,
        "intent_to_treat": effects,
        "decision_support": {"status": "observed_field_effect_no_new_campaign_authorization", "reversal_conditions": ["A replication in the intended population fails to reproduce the effect.", "Ethics or legal review rejects the intervention content.", "Household clustering or interference assumptions require a different estimand."]},
        "headline_metrics": [f"Source individuals analyzed: {summary['source_rows_used']:,}", f"Largest observed ITT: {largest['treatment']} {largest['intent_to_treat_difference']:.1%}", f"Household-clustered 95% interval: {largest['confidence_interval_95'][0]:.1%} to {largest['confidence_interval_95'][1]:.1%}", "Causal scope: the randomized experiment only"],
    }


def _standardize(values: list[float]) -> list[float]:
    center = mean(values)
    spread = math.sqrt(mean((value - center) ** 2 for value in values)) or 1.0
    return [(value - center) / spread for value in values]


def analyze_qoz(project_root: Path):
    rows = read_csv(project_root / "data/processed/analysis.csv")
    panel: dict[str, dict[int, dict[str, float]]] = defaultdict(dict)
    fields = ["poverty_count", "poverty_universe", "median_household_income", "median_gross_rent", "civilian_labor_force", "unemployed", "workplace_jobs"]
    for row in rows:
        panel[row["geoid"]][int(row["year"])] = {field: _number(row[field]) for field in fields} | {"qoz": int(row["qoz_2018"]), "population": _number(row["population"])}
    tracts = []
    for geoid, years in panel.items():
        if 2018 not in years or 2019 not in years:
            continue
        before, after = years[2018], years[2019]
        if before["poverty_universe"] <= 0 or before["civilian_labor_force"] <= 0 or after["poverty_universe"] <= 0 or after["civilian_labor_force"] <= 0:
            continue
        tracts.append({"geoid": geoid, "qoz": before["qoz"], "poverty_before": before["poverty_count"] / before["poverty_universe"], "income_before": before["median_household_income"], "jobs_before": before["workplace_jobs"], "unemployment_before": before["unemployed"] / before["civilian_labor_force"], "change_poverty": after["poverty_count"] / after["poverty_universe"] - before["poverty_count"] / before["poverty_universe"], "change_income": after["median_household_income"] - before["median_household_income"], "change_rent": after["median_gross_rent"] - before["median_gross_rent"], "change_jobs": after["workplace_jobs"] - before["workplace_jobs"], "change_unemployment": after["unemployed"] / after["civilian_labor_force"] - before["unemployed"] / before["civilian_labor_force"]})
    covariates = ["poverty_before", "income_before", "jobs_before", "unemployment_before"]
    standardized = {field: _standardize([row[field] for row in tracts]) for field in covariates}
    for index, row in enumerate(tracts):
        row["vector"] = [standardized[field][index] for field in covariates]
    treated = [row for row in tracts if row["qoz"]]
    controls = [row for row in tracts if not row["qoz"]]
    pairs = []
    for treated_row in treated:
        control = min(controls, key=lambda candidate: sum((left - right) ** 2 for left, right in zip(treated_row["vector"], candidate["vector"])))
        pairs.append((treated_row, control))
    outcomes = ["change_poverty", "change_income", "change_rent", "change_jobs", "change_unemployment"]
    effects = {}
    rng = random.Random(20260810)
    samples = json.loads((project_root / "config.json").read_text())["parameters"]["bootstrap_samples"]
    for outcome in outcomes:
        differences = [left[outcome] - right[outcome] for left, right in pairs]
        bootstrap = [mean(differences[rng.randrange(len(differences))] for _ in differences) for _ in range(samples)]
        effects[outcome] = {"matched_difference_in_change": mean(differences), "bootstrap_95_interval": [quantile(bootstrap, 0.025), quantile(bootstrap, 0.975)]}
    reuse = Counter(right["geoid"] for _, right in pairs)
    figures = project_root / "outputs/figures"
    source = "CDFI Fund 2018 QOZ designations; Census ACS and LODES 2018-2019"
    svg_interval(figures / "matched-change-effects.svg", "Matched differences in one-year change", "Tract-level screen; units vary and are shown in results.json", [(name.replace("change_", ""), item["matched_difference_in_change"], item["bootstrap_95_interval"][0], item["bootstrap_95_interval"][1]) for name, item in effects.items()], source)
    before_balance = [(field, abs(mean(row[field] for row in treated) - mean(row[field] for row in controls))) for field in covariates]
    svg_bar(figures / "baseline-balance.svg", "Raw baseline differences", "Absolute treated-versus-all-control differences before matching", before_balance, source)
    svg_bar(figures / "control-reuse.svg", "Matched-control reuse", "Sensitivity signal for nearest-neighbor support", [("unique controls", len(reuse)), ("treated tracts", len(treated)), ("maximum reuse", max(reuse.values()))], source)
    return {
        "project_id": "opportunity-zone-policy-evaluation",
        "data": {"panel_rows": len(rows), "complete_tracts": len(tracts), "qoz_tracts": len(treated), "matched_control_tracts": len(reuse)},
        "study_design": {"design": "one-year matched pre/post association screen", "treatment": "2018 QOZ designation", "period": "2018 to 2019", "causal_status": "not identified; no parallel-trends evidence"},
        "matched_change_effects": effects,
        "support_diagnostic": {"unique_controls": len(reuse), "maximum_control_reuse": max(reuse.values())},
        "decision_support": {"status": "associational_policy_screen_only", "reversal_conditions": ["A multi-year pre-period fails a parallel-trends diagnostic.", "Alternative comparison groups reverse the change contrast.", "Updated ACS or LODES vintages materially change tract outcomes."]},
        "headline_metrics": [f"Complete tract panels: {len(tracts):,}", f"Designated QOZ tracts analyzed: {len(treated):,}", f"Unique matched controls: {len(reuse):,}", "Causal status: not identified"],
    }


def _nhanes_age_band(age: int) -> str:
    if age < 40:
        return "18-39"
    if age < 60:
        return "40-59"
    return "60+"


def analyze_nhanes(project_root: Path):
    rows = read_csv(project_root / "data/processed/analysis.csv")
    materialized = []
    for row in rows:
        age = int(row["age"])
        materialized.append({**row, "weight": max(_number(row["exam_weight"]), 1.0), "outcome": int(row["death_within_36_months"]), "age_band": _nhanes_age_band(age), "pir": _number(row["poverty_income_ratio"], -1.0)})
    train = [row for row in materialized if row["cohort"] == "2011-2012"]
    test = [row for row in materialized if row["cohort"] == "2015-2016"]
    global_rate = _weighted_mean((row["outcome"], row["weight"]) for row in train)
    cells: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in train:
        cells[(row["age_band"], row["sex"])].append(row)
    rates = {key: _weighted_mean((row["outcome"], row["weight"]) for row in group) for key, group in cells.items()}
    scored = [(rates.get((row["age_band"], row["sex"]), global_rate), row["outcome"], row["weight"]) for row in test]
    calibration = _calibration(scored, 4)
    cohort_rates = {cohort: _weighted_mean((row["outcome"], row["weight"]) for row in materialized if row["cohort"] == cohort) for cohort in ("2011-2012", "2015-2016")}
    income_groups = {"PIR < 1": lambda value: 0 <= value < 1, "PIR 1-3": lambda value: 1 <= value < 3, "PIR >= 3": lambda value: value >= 3}
    income_rates = {label: _weighted_mean((row["outcome"], row["weight"]) for row in test if rule(row["pir"])) for label, rule in income_groups.items()}
    figures = project_root / "outputs/figures"
    source = "CDC NHANES 2011-2012 and 2015-2016 linked mortality public-use files"
    svg_bar(figures / "cohort-mortality.svg", "Observed 36-month mortality", "Survey-weighted cohort estimates", list(cohort_rates.items()), source, percent=True)
    svg_line(figures / "transport-calibration.svg", "Cross-cohort transport calibration", "2011-2012 age/sex rates evaluated in 2015-2016", [("observed", [(item["predicted"], item["observed"]) for item in calibration]), ("ideal", [(0.0, 0.0), (max(item["predicted"] for item in calibration), max(item["predicted"] for item in calibration))])], source, y_percent=True)
    svg_bar(figures / "income-gradient.svg", "Mortality by poverty-income ratio", "2015-2016 cohort; descriptive inequality diagnostic", list(income_rates.items()), source, percent=True)
    auc = _weighted_auc(scored)
    brier = _weighted_brier(scored)
    return {
        "project_id": "nhanes-population-transportability",
        "data": {"rows": len(materialized), "development_rows": len(train), "external_validation_rows": len(test)},
        "study_design": {"design": "survey-weighted cross-cohort transportability audit", "development": "NHANES 2011-2012", "validation": "NHANES 2015-2016", "horizon": "36-month linked mortality"},
        "transport_validation": {"auc": auc, "brier": brier, "calibration": calibration},
        "cohort_mortality": cohort_rates,
        "income_gradient": income_rates,
        "decision_support": {"status": "population_research_only", "reversal_conditions": ["A newer linked cohort changes transport calibration.", "Complex-survey variance estimation changes uncertainty conclusions.", "The intended population differs materially from NHANES coverage."]},
        "headline_metrics": [f"External-cohort AUC: {auc:.3f}", f"External-cohort Brier score: {brier:.3f}", f"Linked adults: {len(materialized):,}", "Terminal use: population research only"],
    }


def analyze_spatial_transit(project_root: Path):
    result = analyze_spatial(project_root)
    rows = read_csv(project_root / "data/processed/analysis.csv")
    stops_payload = json.loads((project_root / "data/raw/mbta-rapid-transit-stops.json").read_text())
    stops = [(item["latitude"], item["longitude"]) for item in stops_payload["data"] if item.get("latitude") is not None]
    distances = []
    high_poverty = []
    for row in rows:
        population = _number(row["population"])
        universe = _number(row["poverty_population"])
        poverty = _number(row["poverty_count"]) / universe if universe else 0.0
        coordinate = (_number(row["latitude"]), _number(row["longitude"]))
        nearest = min(_haversine(coordinate, stop) for stop in stops)
        distances.append((nearest, population))
        if poverty >= 0.20:
            high_poverty.append((nearest, population))
    all_distance = _weighted_mean(distances)
    high_distance = _weighted_mean(high_poverty)
    figures = project_root / "outputs/figures"
    source = "U.S. Census Bureau ACS 2019-2023 and MBTA V3 rapid-transit stops"
    svg_bar(figures / "mbta-access-gap.svg", "Observed proximity to rapid transit", "Population-weighted straight-line distance to nearest stop", [("all analyzed tracts", all_distance), ("high-poverty tracts", high_distance)], source)
    result["transit_access"] = {"mbta_stops": len(stops), "population_weighted_nearest_stop_km": all_distance, "high_poverty_weighted_nearest_stop_km": high_distance}
    result["site_feasibility_gate"] = {"status": "evidence_required_before_site_recommendation", "missing_evidence": ["parcel availability", "land ownership", "zoning and permitting", "network travel times", "capital and operating cost", "community review"]}
    result["headline_metrics"] = [f"Analyzed Massachusetts tracts: {result['data']['tracts_analyzed']:,}", f"MBTA rapid-transit stop records: {len(stops):,}", f"High-poverty weighted nearest-stop distance: {high_distance:.2f} km", "Site decision: blocked pending land and feasibility evidence"]
    result.setdefault("decision_support", {})["reversal_conditions"] = ["Parcel and zoning evidence makes a selected tract infeasible.", "Network travel times reverse straight-line access rankings.", "Stakeholder-defined equity priorities change the need weights."]
    return result


PREPARERS.update(
    {
        "population-health-survival": prepare_nhis,
        "bike-demand-operations": prepare_bike,
        "census-income-ai": prepare_pums,
        "sec-nport-filing-review": prepare_nport,
        "cross-city-311-shift": prepare_311,
        "wildfire-mitigation-under-uncertainty": prepare_fire,
        "social-norm-field-experiment": prepare_social,
        "opportunity-zone-policy-evaluation": prepare_qoz,
        "nhanes-population-transportability": prepare_nhanes,
    }
)

ANALYZERS.update(
    {
        "population-health-survival": analyze_nhis,
        "bike-demand-operations": analyze_bike,
        "census-income-ai": analyze_pums,
        "sec-nport-filing-review": analyze_nport,
        "cross-city-311-shift": analyze_311,
        "wildfire-mitigation-under-uncertainty": analyze_fire,
        "social-norm-field-experiment": analyze_social,
        "opportunity-zone-policy-evaluation": analyze_qoz,
        "nhanes-population-transportability": analyze_nhanes,
        "spatial-equity-planning": analyze_spatial_transit,
    }
)


REPORT_COPY.update(
    {
        "population-health-survival": {"answer": "The 2016 NHIS risk cells show measurable but imperfect transport to 2017 linked mortality; the output supports population-risk validation, not individual clinical action.", "findings": [], "methods": "Survey-weighted cohort rates, pre-specified age/condition cells, temporal AUC, Brier score, calibration, and workload/capture protocol screens.", "limits": "Public linked mortality is observational and uses public-use linkage fields; the simple score is not a diagnostic model and variance estimates do not replace a full complex-survey analysis."},
        "bike-demand-operations": {"answer": "Station-hour history improves held-out pickup forecasts, while rebalancing outputs remain explicitly modeled scenarios because inventory, routing, labor, and dock-capacity data are absent.", "findings": [], "methods": "Station-hour-month aggregation, January-September development, October-December holdout, weighted MAE, observed pickup-return imbalance, and fixed-budget allocation scenarios.", "limits": "Pickups minus returns is an imbalance proxy, not observed stockout demand; modeled residual imbalance is not an achieved service result."},
        "census-income-ai": {"answer": "A 2019 ACS PUMS employment model is tested on 2023 Rhode Island records with protected attributes reserved for audit; it is not authorized for eligibility, hiring, or other consequential use.", "findings": [], "methods": "Survey-weighted grouped-rate model, temporal AUC/Brier/calibration, cohort drift, and sex/race audit slices excluded from model inputs.", "limits": "Employment status is not suitability or merit; PUMS is a survey sample, the model is deliberately simple, and no real decision owner or lawful use has validated it."},
        "sec-nport-filing-review": {"answer": "SEC N-PORT indicators support a transparent filing-review queue, not a return forecast, fund ranking, or investment recommendation.", "findings": [], "methods": "Official filing extraction, concentration/liquidity/redemption indicators, percentile ranks, capacity thresholds, and explicit filing-review-only governance.", "limits": "N-PORT fields are reported snapshots and may be amended; the composite is an analyst screen, not SEC risk classification, investor suitability, or expected performance."},
        "cross-city-311-shift": {"answer": "Chicago and New York 311 systems show material taxonomy and distribution differences, so the cross-city transfer gate can refuse reuse rather than disguise incompatible service definitions.", "findings": [], "methods": "Versioned keyword ontology, unmatched-category retention, within-city year shift, total variation, Jensen-Shannon divergence, and a predeclared transfer gate.", "limits": "311 use reflects access, awareness, intake policy, and local taxonomy; request counts do not equal latent service need or agency performance."},
        "wildfire-mitigation-under-uncertainty": {"answer": "Historical perimeter data can stress-test where evidence collection should focus, but it cannot estimate fires or acres prevented; mitigation allocation remains blocked pending effectiveness and feasibility evidence.", "findings": [], "methods": "Historical, recent, and tail-acre exposure scenarios; allocation-share alignment; minimax regret; and an explicit evidence-request terminal state.", "limits": "Perimeter completeness, unit coding, suppression effectiveness, ecology, community priorities, costs, and 2025 completeness are not established by this dataset."},
        "social-norm-field-experiment": {"answer": "The household-randomized field experiment identifies intent-to-treat turnout differences in its study population; public artifacts retain clustered inference without redistributing participant rows.", "findings": [], "methods": "Randomized-arm turnout rates, household-clustered sandwich standard errors, 95% intervals, and descriptive prior-turnout-stratum contrasts.", "limits": "The historical election setting, intervention wording, interference, ethics, and population transport limit any new campaign use."},
        "opportunity-zone-policy-evaluation": {"answer": "The Massachusetts panel provides a matched one-year change screen, but no parallel-trends evidence; every result remains associational rather than a causal QOZ effect.", "findings": [], "methods": "Official designation linkage, tract panel construction, baseline nearest-neighbor matching, change contrasts, bootstrap intervals, and support diagnostics.", "limits": "Only one pre/post interval is used, controls are reused, ACS estimates overlap in time, and selection into designation is not eliminated."},
        "nhanes-population-transportability": {"answer": "Age/sex risk cells trained in NHANES 2011-2012 are externally checked in 2015-2016 linked mortality, with income gradients reported as population inequality evidence rather than clinical prediction.", "findings": [], "methods": "Survey-weighted cohort mortality, cross-cohort AUC/Brier/calibration, and poverty-income-ratio mortality gradients.", "limits": "This compact audit does not implement the full NHANES complex-survey variance design and cannot support individual diagnosis or treatment."},
        "spatial-equity-planning": {"answer": "ACS need patterns and observed MBTA stop proximity can prioritize local review, but no site recommendation is released until parcel, zoning, network, cost, and stakeholder evidence is supplied.", "findings": [], "methods": "ACS tract indicators, spatial autocorrelation, heuristic five-hub allocation, bootstrap/sensitivity checks, and population-weighted nearest-MBTA-stop distance.", "limits": "Tract internal points and straight-line distance are planning screens; land availability, ownership, zoning, travel networks, capacity, cost, and community consent are missing."},
    }
)


def _visuals(items):
    return [
        {"file": filename, "title": title, "finding": finding, "boundary": boundary}
        for filename, title, finding, boundary in items
    ]


VISUAL_COPY.update(
    {
        "population-health-survival": _visuals([("cohort-mortality.svg", "Linked mortality by cohort", "Survey weights preserve the population-estimation target.", "Observed association only."), ("age-gradient.svg", "Age risk gradient", "The later cohort shows the expected age pattern.", "Age bands do not authorize individual triage."), ("temporal-calibration.svg", "Temporal calibration", "2016 risk cells are evaluated in 2017.", "Apparent transport does not establish clinical validity.")]),
        "bike-demand-operations": _visuals([("forecast-mae.svg", "Held-out forecast error", "Station-hour history is compared with an hour-only baseline.", "Forecast accuracy is not service impact."), ("monthly-demand.svg", "Monthly observed demand", "Seasonality is visible before the holdout assessment.", "Trip records omit unmet demand."), ("modeled-imbalance.svg", "Modeled imbalance scenarios", "All options use one declared daily budget.", "These are modeled, not observed, outcomes.")]),
        "census-income-ai": _visuals([("temporal-performance.svg", "Temporal performance", "The 2023 cohort is untouched during model construction.", "No consequential use is authorized."), ("calibration.svg", "2023 calibration", "Predicted and survey-weighted observed rates are compared.", "Calibration is population- and period-specific."), ("audit-slices.svg", "Protected-attribute audit", "Audit fields remain outside model inputs.", "Displayed differences are not causal explanations.")]),
        "sec-nport-filing-review": _visuals([("risk-indicator-p90.svg", "N-PORT indicator tails", "Observed filing distributions define review signals.", "Indicators are not expected returns."), ("review-score-deciles.svg", "Transparent score deciles", "Every score component is percentile-based.", "The composite is analyst-defined."), ("review-capacity.svg", "Review capacity trade-off", "Thresholds determine workload and internal high-score capture.", "Selection triggers filing review only.")]),
        "cross-city-311-shift": _visuals([("service-mix-2023.svg", "Cross-city service mix", "Unmatched categories stay visible as other.", "Local taxonomies are not equivalent."), ("within-city-shift.svg", "Within-city shift", "Each city is first compared with itself over time.", "Administrative shift is not latent-need change."), ("monthly-requests.svg", "Monthly request volumes", "Observed intake patterns preserve city labels.", "Counts do not measure service quality.")]),
        "wildfire-mitigation-under-uncertainty": _visuals([("annual-observed-acres.svg", "Observed mapped acres", "The historical sequence includes an explicitly partial 2025.", "Mapped acres are not damages or preventable acres."), ("recent-unit-exposure.svg", "Recent unit exposure", "Unit IDs are ranked by observed 2020-2024 acres.", "Exposure is not mitigation effectiveness."), ("scenario-regret.svg", "Allocation regret", "Strategies are stressed across three observed-exposure scenarios.", "Regret is a modeled alignment proxy.")]),
        "social-norm-field-experiment": _visuals([("treatment-turnout.svg", "Randomized-arm turnout", "Observed treatment rates come from the full replication file.", "The causal scope is the experiment."), ("cluster-robust-itt.svg", "Clustered treatment effects", "Standard errors account for household assignment.", "Intervals do not establish transport."), ("stratum-effects.svg", "Prior-turnout strata", "Subgroup contrasts expose heterogeneity.", "These strata comparisons are descriptive.")]),
        "opportunity-zone-policy-evaluation": _visuals([("matched-change-effects.svg", "Matched change contrasts", "One-year changes are compared within matched pairs.", "Causality is not identified."), ("baseline-balance.svg", "Baseline support", "Raw baseline differences motivate matching.", "Balance on observed fields does not remove hidden confounding."), ("control-reuse.svg", "Control reuse", "Reuse is exposed as a support diagnostic.", "Effective comparison diversity is limited.")]),
        "nhanes-population-transportability": _visuals([("cohort-mortality.svg", "Cross-cohort mortality", "Both cohorts use the same 36-month horizon.", "Cohort differences are not causal."), ("transport-calibration.svg", "Transport calibration", "Earlier age/sex cells are tested later.", "This is not a clinical model."), ("income-gradient.svg", "Income gradient", "Survey-weighted mortality is stratified by PIR.", "The gradient is descriptive inequality evidence.")]),
        "spatial-equity-planning": VISUAL_COPY["spatial-equity-planning"] + _visuals([("mbta-access-gap.svg", "Observed MBTA access gap", "Actual rapid-transit stop coordinates supplement ACS need indicators.", "Straight-line proximity does not replace network or site feasibility.")]),
    }
)


__all__ = [name for name in globals() if not name.startswith("__")]
