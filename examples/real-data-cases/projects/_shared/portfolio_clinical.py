#!/usr/bin/env python3
"""Clinical and behavioral analysis modules."""

from __future__ import annotations

from portfolio_core import *

def analyze_population(project_root: Path) -> dict[str, Any]:
    rows = read_csv(project_root / "data/processed/analysis.csv")
    cox_features = [
        "age",
        "ejection_fraction",
        "serum_creatinine",
        "serum_sodium",
        "sex",
        "diabetes",
        "high_blood_pressure",
        "smoking",
    ]
    cox = _cox_ph(rows, cox_features)
    km = _km(rows)
    low = [row for row in rows if float(row["ejection_fraction"]) < 35]
    high = [row for row in rows if float(row["ejection_fraction"]) >= 35]
    death = lambda group: mean(float(row["DEATH_EVENT"]) for row in group)
    pairs = [(float(row["ejection_fraction"]), int(row["DEATH_EVENT"])) for row in rows]
    rng = random.Random(20260727)
    differences = []
    for _ in range(2000):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        lower = [event for ef, event in sample if ef < 35]
        upper = [event for ef, event in sample if ef >= 35]
        differences.append(mean(lower) - mean(upper))
    protocols = {
        "current-age-rule": _protocol_bootstrap(
            rows, lambda row: float(row["age"]) >= 65, 11
        ),
        "ejection-triage": _protocol_bootstrap(
            rows, lambda row: float(row["ejection_fraction"]) < 35, 12
        ),
        "dual-marker-triage": _protocol_bootstrap(
            rows,
            lambda row: (
                float(row["ejection_fraction"]) < 35
                or float(row["serum_creatinine"]) > 1.5
            ),
            13,
        ),
    }
    result = {
        "project_id": "population-health-survival",
        "study_design": {
            "target_population": (
                "Patients represented by the source hospital cohort with heart "
                "failure and recorded follow-up"
            ),
            "time_zero": "source-defined start of follow-up",
            "outcome": "recorded death event during follow-up",
            "estimand": (
                "association between baseline predictors and all-cause event hazard, "
                "plus absolute observed event risk by 180 days"
            ),
            "inclusion": "all 299 source records with nonmissing time and event",
            "exclusion": "none",
            "causal_status": "observational association; no treatment estimand",
        },
        "cohort_flow": {
            "source_records": len(rows),
            "eligible_time_and_event": len(rows),
            "complete_primary_model": len(rows),
            "analyzed": len(rows),
        },
        "missingness": {
            field: sum(row.get(field, "") in ("", "?", "NA", "N/A") for row in rows)
            for field in ["time", "DEATH_EVENT", *cox_features]
        },
        "data": {"rows": len(rows), "follow_up_days": [1, 285]},
        "survival": {str(day): _km_at(km, day) for day in (30, 90, 180)},
        "death_rate": death(rows),
        "low_ejection_death_rate": death(low),
        "higher_ejection_death_rate": death(high),
        "risk_difference": death(low) - death(high),
        "risk_difference_bootstrap_95": [
            quantile(differences, 0.025),
            quantile(differences, 0.975),
        ],
        "candidate_protocols": protocols,
        "cox_proportional_hazards": cox,
        "selection_and_transport": {
            "selection_bias": (
                "The public cohort is a convenience clinical sample; referral, "
                "care, and measurement processes are not fully observed."
            ),
            "representativeness": (
                "No sampling weights or external target-population benchmark are "
                "available, so transport beyond the source setting is unverified."
            ),
            "measurement_error": (
                "Single recorded baseline measures may contain biological and "
                "laboratory variation; no replicate-measure correction is possible."
            ),
        },
        "claim_class": "observational association",
    }
    write_json(project_root / "outputs/cox-model.json", cox)
    figures = project_root / "outputs/figures"
    source = "UCI Heart Failure Clinical Records, DOI 10.24432/C5Z89R"
    svg_line(
        figures / "kaplan-meier.svg",
        "Observed survival across follow-up",
        "Kaplan–Meier estimate; n=299; censoring reflected in the risk set",
        [("All participants", km)],
        source,
        y_percent=True,
    )
    svg_bar(
        figures / "ejection-risk.svg",
        "Observed death-event rate by ejection fraction",
        "Threshold chosen for an exploratory subgroup contrast; not a treatment rule",
        [("<35%", death(low)), ("≥35%", death(high))],
        source,
        percent=True,
    )
    svg_interval(
        figures / "protocol-comparison.svg",
        "Candidate follow-up triage protocols",
        "Share of observed death events captured; 95% patient-bootstrap intervals",
        [
            (
                key.replace("-", " ").title(),
                value["high_risk_capture"],
                quantile(value["bootstrap"]["high_risk_capture"], 0.025),
                quantile(value["bootstrap"]["high_risk_capture"], 0.975),
            )
            for key, value in protocols.items()
        ],
        source,
    )
    svg_interval(
        figures / "cox-hazard-ratios.svg",
        "Adjusted associational hazard ratios",
        "Per one sample standard deviation; Breslow-tie Cox model, apparent fit",
        [
            (
                field.replace("_", " ").title(),
                values["hazard_ratio_per_sd"],
                values["ci95"][0],
                values["ci95"][1],
            )
            for field, values in cox["coefficients"].items()
        ],
        source,
    )
    return result


def _permutation_pvalue(left: list[float], right: list[float], seed: int) -> float:
    observed = abs(mean(left) - mean(right))
    pooled = left + right
    rng = random.Random(seed)
    exceed = 0
    for _ in range(5000):
        shuffled = pooled[:]
        rng.shuffle(shuffled)
        statistic = abs(mean(shuffled[: len(left)]) - mean(shuffled[len(left) :]))
        exceed += statistic >= observed
    return (exceed + 1) / 5001


def _sign_flip_pvalue(
    differences: list[float],
    *,
    seed: int,
    repetitions: int = 10_000,
) -> float:
    observed = abs(mean(differences))
    rng = random.Random(seed)
    exceed = 0
    for _ in range(repetitions):
        statistic = abs(
            mean(
                value if rng.random() < 0.5 else -value
                for value in differences
            )
        )
        exceed += statistic >= observed
    return (exceed + 1) / (repetitions + 1)


def _holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues, key=pvalues.get)
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, name in enumerate(ordered):
        running = max(running, (total - index) * pvalues[name])
        adjusted[name] = min(1.0, running)
    return adjusted


def analyze_behavioral(project_root: Path) -> dict[str, Any]:
    rows = read_csv(project_root / "data/processed/analysis.csv")
    usable = [
        row
        for row in rows
        if _safe_number(row.get("Vd")) is not None
        and _safe_number(row.get("Td")) is not None
    ]
    groups = {"control": [], "dyslexic": []}
    for row in usable:
        group = "control" if int(float(row["group"])) == 1 else "dyslexic"
        groups[group].append(float(row["Vd"]) - float(row["Td"]))
    all_differences = groups["control"] + groups["dyslexic"]
    outcome_fields = {
        "fixation_duration": ("Vd", "Td"),
        "fixation_count": ("Vf", "Tf"),
        "regression_count": ("Vr", "Tr"),
    }
    paired_outcomes = {
        name: [
            float(row[pseudo]) - float(row[meaningful])
            for row in usable
            if _safe_number(row.get(pseudo)) is not None
            and _safe_number(row.get(meaningful)) is not None
        ]
        for name, (pseudo, meaningful) in outcome_fields.items()
    }
    raw_pvalues = {
        name: _sign_flip_pvalue(
            values,
            seed=31 + index,
        )
        for index, (name, values) in enumerate(paired_outcomes.items())
    }
    adjusted_pvalues = _holm_adjust(raw_pvalues)
    outcome_summary = {}
    for index, (name, values) in enumerate(paired_outcomes.items()):
        bootstrap = bootstrap_statistic(
            values,
            mean,
            samples=1500,
            seed=41 + index,
        )
        outcome_summary[name] = {
            "n": len(values),
            "mean_pseudoword_minus_meaningful": mean(values),
            "ci95": [
                quantile(bootstrap, 0.025),
                quantile(bootstrap, 0.975),
            ],
            "sign_flip_p": raw_pvalues[name],
            "holm_adjusted_p": adjusted_pvalues[name],
        }
    order_groups = {
        order: [
            float(row["Vd"]) - float(row["Td"])
            for row in usable
            if row["typeorder"] == order
        ]
        for order in sorted({row["typeorder"] for row in usable})
    }
    order_p = (
        _permutation_pvalue(
            order_groups.get("1", []),
            order_groups.get("2", []),
            39,
        )
        if order_groups.get("1") and order_groups.get("2")
        else None
    )
    bootstraps = {
        group: bootstrap_statistic(values, mean, samples=1500, seed=21 + index)
        for index, (group, values) in enumerate(groups.items())
    }
    protocols: dict[str, dict[str, Any]] = {}
    duration_fields = {
        "meaningful-only": "Td",
        "pseudoword-only": "Vd",
    }

    def protocol_metrics(
        sample: list[dict[str, str]],
        field: str | None,
    ) -> dict[str, float]:
        if field:
            values = [float(row[field]) for row in sample]
            control = [
                float(row[field])
                for row in sample
                if int(float(row["group"])) == 1
            ]
            dyslexic = [
                float(row[field])
                for row in sample
                if int(float(row["group"])) == 2
            ]
            burden = mean(values)
            stability = 1 / (1 + sd(values) / burden)
        else:
            differences = [float(row["Vd"]) - float(row["Td"]) for row in sample]
            control = [
                float(row["Vd"]) - float(row["Td"])
                for row in sample
                if int(float(row["group"])) == 1
            ]
            dyslexic = [
                float(row["Vd"]) - float(row["Td"])
                for row in sample
                if int(float(row["group"])) == 2
            ]
            burden = mean(float(row["Vd"]) + float(row["Td"]) for row in sample)
            stability = 1 / (
                1
                + sd(differences)
                / (abs(mean(differences)) + mean(abs(item) for item in differences))
            )
        pooled_sd = math.sqrt((sd(control) ** 2 + sd(dyslexic) ** 2) / 2) or 1
        return {
            "group_separation": abs(mean(dyslexic) - mean(control)) / pooled_sd,
            "mean_fixation_duration": burden,
            "measurement_stability": stability,
        }

    for name, field in duration_fields.items():
        protocols[name] = protocol_metrics(usable, field)
    protocols["combined-protocol"] = protocol_metrics(usable, None)

    source_groups = {
        group_id: [
            row for row in usable if int(float(row["group"])) == group_id
        ]
        for group_id in (1, 2)
    }
    rng = random.Random(29)
    bootstrap_by_protocol = {
        name: {key: [] for key in metrics}
        for name, metrics in protocols.items()
    }
    for _ in range(400):
        sample = []
        for group_rows in source_groups.values():
            sample.extend(
                group_rows[rng.randrange(len(group_rows))]
                for _ in group_rows
            )
        for name, field in {**duration_fields, "combined-protocol": None}.items():
            sampled = protocol_metrics(sample, field)
            for key, value in sampled.items():
                bootstrap_by_protocol[name][key].append(value)
    for name, metrics in protocols.items():
        metrics["bootstrap"] = bootstrap_by_protocol[name]
    result = {
        "project_id": "behavioral-reading-experiment",
        "study_design": {
            "analysis_unit": "participant",
            "within_participant_conditions": [
                "meaningful passage",
                "pseudoword passage",
            ],
            "primary_estimand": (
                "mean within-participant difference in fixation duration, "
                "pseudoword minus meaningful"
            ),
            "primary_hypothesis": "mean paired duration difference equals zero",
            "secondary_outcomes": [
                "fixation count",
                "regression count",
            ],
            "group_role": (
                "reader group is an observed status used for heterogeneity, not "
                "a randomized treatment"
            ),
        },
        "data": {"rows": len(rows), "complete_pairs": len(usable)},
        "cohort_flow": {
            "source_participants": len(rows),
            "complete_primary_pairs": len(usable),
            "primary_attrition": len(rows) - len(usable),
        },
        "counterbalancing": {
            "type_order_counts": dict(Counter(row["typeorder"] for row in usable)),
            "topic_order_counts": dict(Counter(row["topicorder"] for row in usable)),
            "primary_difference_by_type_order": {
                order: mean(values) for order, values in order_groups.items()
            },
            "between_order_permutation_p": order_p,
            "interpretation": (
                "Order imbalance or order-by-condition differences are treated as "
                "carryover sensitivity, not discarded."
            ),
        },
        "paired_difference_overall": mean(all_differences),
        "paired_difference_by_group": {
            group: {
                "mean": mean(values),
                "ci95": [
                    quantile(bootstraps[group], 0.025),
                    quantile(bootstraps[group], 0.975),
                ],
                "n": len(values),
            }
            for group, values in groups.items()
        },
        "between_group_permutation_p": _permutation_pvalue(
            groups["control"], groups["dyslexic"], 27
        ),
        "paired_outcomes_with_multiplicity": outcome_summary,
        "design_sensitivity": {
            "two_sided_80_percent_power_mde_primary_scale": (
                (1.959963984540054 + 0.8416212335729143)
                * sd(all_differences)
                / math.sqrt(len(all_differences))
            ),
            "assumptions": (
                "Normal approximation for paired mean, alpha 0.05, 80% power; "
                "reported as design sensitivity rather than a retrospective power claim."
            ),
            "spillover": (
                "No network or classroom identifiers are available; interference "
                "cannot be tested and is a limitation."
            ),
            "noncompliance": (
                "Both passage measures are present for all primary-analysis "
                "participants; detailed protocol adherence is not observed."
            ),
        },
        "candidate_protocols": protocols,
        "claim_class": "within-study behavioral contrast; no policy outcome",
    }
    source = "Harvard Dataverse DOI 10.7910/DVN/3YCB56, V1"
    figures = project_root / "outputs/figures"
    svg_interval(
        figures / "paired-effect.svg",
        "Pseudoword minus meaningful fixation duration",
        "Participant-level paired contrast with 95% bootstrap intervals",
        [
            (
                group.title(),
                value["mean"],
                value["ci95"][0],
                value["ci95"][1],
            )
            for group, value in result["paired_difference_by_group"].items()
        ],
        source,
    )
    svg_bar(
        figures / "protocol-burden.svg",
        "Mean fixation-duration burden by protocol",
        "Combined protocol sums both passage conditions",
        [
            (name.replace("-", " ").title(), value["mean_fixation_duration"])
            for name, value in protocols.items()
        ],
        source,
    )
    svg_interval(
        figures / "paired-outcomes.svg",
        "Paired pseudoword-minus-meaningful outcomes",
        "Participant bootstrap intervals; outcome scales differ",
        [
            (
                name.replace("_", " ").title(),
                value["mean_pseudoword_minus_meaningful"],
                value["ci95"][0],
                value["ci95"][1],
            )
            for name, value in outcome_summary.items()
        ],
        source,
    )
    return result

__all__ = [name for name in globals() if not name.startswith("__")]
