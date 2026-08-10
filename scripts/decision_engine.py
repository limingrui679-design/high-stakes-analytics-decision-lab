#!/usr/bin/env python3
"""Decision-analysis engine for High-Stakes Analytics & Decision Lab."""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable, cast

from report_visuals import generate_visuals

ENGINE_VERSION = "7.0.0"
SUPPORTED_SCHEMA_VERSIONS = {"1.2", "1.3"}
SUPPORTED_DISTRIBUTIONS = {
    "fixed",
    "normal",
    "uniform",
    "triangular",
    "empirical",
    "bootstrap",
}
SUPPORTED_UNCERTAINTY_TYPES = {
    "none",
    "parameter",
    "process",
    "scenario",
}
SUPPORTED_OPERATORS = {"<=", "<", ">=", ">"}
SUPPORTED_DECISION_USES = {"illustrative", "exploratory", "operational"}
UNCERTAINTY_METHOD = "latent_factor_gaussian_copula"
REQUIRED_PROVENANCE_RULES = {
    "criterion_weight",
    "criterion_scale",
    "metric_distribution",
    "scenario_probability",
    "scenario_adjustment",
    "constraint_threshold",
    "risk_aversion",
    "maximum_violation_rate",
    "weight_sensitivity",
    "correlation_loading",
    "correlation_stress",
}
DEFAULT_READINESS_THRESHOLDS = {
    "minimum_probability_best": 0.50,
    "minimum_weight_stability": 0.75,
    "minimum_scenario_stability": 0.75,
    "maximum_scale_clipping_rate": 0.05,
}


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def load_case(path: str | Path) -> dict[str, Any]:
    case_path = Path(path)
    with case_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("The case file must contain a JSON object.")
    return data


def case_hash(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _validate_distribution(spec: Any, path: str, errors: list[str]) -> None:
    if not isinstance(spec, dict):
        errors.append(f"{path} must be an object.")
        return
    kind = spec.get("distribution")
    if kind not in SUPPORTED_DISTRIBUTIONS:
        errors.append(
            f"{path}.distribution must be one of {sorted(SUPPORTED_DISTRIBUTIONS)}."
        )
        return
    required_by_kind = {
        "fixed": ("value",),
        "normal": ("mean", "sd"),
        "uniform": ("low", "high"),
        "triangular": ("low", "mode", "high"),
        "empirical": ("values",),
        "bootstrap": ("values",),
    }
    for field in required_by_kind[kind]:
        if field == "values":
            values = spec.get("values")
            if (
                not isinstance(values, list)
                or not values
                or not all(_is_number(value) for value in values)
            ):
                errors.append(
                    f"{path}.values must be a non-empty list of finite numbers."
                )
        elif not _is_number(spec.get(field)):
            errors.append(f"{path}.{field} must be a finite number.")
    if kind == "normal" and _is_number(spec.get("sd")) and spec["sd"] < 0:
        errors.append(f"{path}.sd must be nonnegative.")
    if kind == "uniform" and all(_is_number(spec.get(k)) for k in ("low", "high")):
        if spec["high"] < spec["low"]:
            errors.append(f"{path}.high must be greater than or equal to low.")
    if kind == "triangular" and all(
        _is_number(spec.get(k)) for k in ("low", "mode", "high")
    ):
        if not spec["low"] <= spec["mode"] <= spec["high"]:
            errors.append(f"{path} must satisfy low <= mode <= high.")
    for bound in ("min", "max"):
        if bound in spec and not _is_number(spec[bound]):
            errors.append(f"{path}.{bound} must be a finite number when present.")
    if _is_number(spec.get("min")) and _is_number(spec.get("max")):
        if spec["min"] > spec["max"]:
            errors.append(f"{path}.min must be less than or equal to max.")
    uncertainty_type = spec.get("uncertainty_type")
    if uncertainty_type is not None and uncertainty_type not in SUPPORTED_UNCERTAINTY_TYPES:
        errors.append(
            f"{path}.uncertainty_type must be one of "
            f"{sorted(SUPPORTED_UNCERTAINTY_TYPES)}."
        )
    if kind == "fixed" and uncertainty_type not in (None, "none"):
        errors.append(f"{path}.uncertainty_type must be none for a fixed distribution.")


def _validate_uncertainty_model(
    model: Any,
    criterion_ids: list[str],
    errors: list[str],
) -> None:
    if not isinstance(model, dict):
        errors.append("uncertainty_model must be an object.")
        return
    if model.get("method") != UNCERTAINTY_METHOD:
        errors.append(
            f"uncertainty_model.method must be {UNCERTAINTY_METHOD}."
        )
    stress_multiplier = model.get("stress_multiplier")
    stress_multiplier_value = (
        float(cast(float, stress_multiplier))
        if _is_number(stress_multiplier)
        else 1.0
    )
    if stress_multiplier_value <= 1:
        errors.append(
            "uncertainty_model.stress_multiplier must be a finite number greater than 1."
        )
        stress_multiplier_value = 1.0
    factors = model.get("factors")
    if not isinstance(factors, list) or not factors:
        errors.append("uncertainty_model.factors must be a non-empty list.")
        return
    factor_ids: list[str] = []
    loading_squares = {criterion_id: 0.0 for criterion_id in criterion_ids}
    for index, factor in enumerate(factors):
        path = f"uncertainty_model.factors[{index}]"
        if not isinstance(factor, dict):
            errors.append(f"{path} must be an object.")
            continue
        factor_id = factor.get("id")
        if not isinstance(factor_id, str) or not factor_id.strip():
            errors.append(f"{path}.id must be a non-empty string.")
        else:
            factor_ids.append(factor_id)
        for field in ("label", "description"):
            if not isinstance(factor.get(field), str) or not factor[field].strip():
                errors.append(f"{path}.{field} must be a non-empty string.")
        loadings = factor.get("loadings")
        if not isinstance(loadings, dict) or not loadings:
            errors.append(f"{path}.loadings must be a non-empty object.")
            continue
        unknown = sorted(set(loadings) - set(criterion_ids))
        if unknown:
            errors.append(
                f"{path}.loadings references unknown criteria: {', '.join(unknown)}."
            )
        for criterion_id, loading in loadings.items():
            if not _is_number(loading) or abs(float(loading)) >= 1:
                errors.append(
                    f"{path}.loadings.{criterion_id} must be between -1 and 1."
                )
            elif criterion_id in loading_squares:
                loading_squares[criterion_id] += float(loading) ** 2
    if len(set(factor_ids)) != len(factor_ids):
        errors.append("uncertainty_model factor identifiers must be unique.")
    for criterion_id, squared_sum in loading_squares.items():
        if squared_sum >= 1:
            errors.append(
                f"Squared factor loadings for {criterion_id} must sum to less than 1."
            )
        stressed_squared_sum = squared_sum * stress_multiplier_value**2
        if stressed_squared_sum >= 1:
            errors.append(
                f"Stressed squared factor loadings for {criterion_id} must sum to less than 1."
            )


def _validate_parameter_governance(
    governance: Any,
    decision_use: str | None,
    errors: list[str],
) -> None:
    if not isinstance(governance, dict):
        errors.append("parameter_governance must be an object.")
        return
    sources = governance.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("parameter_governance.sources must be a non-empty list.")
        sources = []
    source_ids: list[str] = []
    for index, source in enumerate(sources):
        path = f"parameter_governance.sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{path} must be an object.")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(f"{path}.id must be a non-empty string.")
        else:
            source_ids.append(source_id)
        for field in ("citation", "source_type", "as_of", "owner"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                errors.append(f"{path}.{field} must be a non-empty string.")
        approved_uses = source.get("approved_decision_uses")
        if not isinstance(approved_uses, list) or not approved_uses:
            errors.append(f"{path}.approved_decision_uses must be a non-empty list.")
        elif any(item not in SUPPORTED_DECISION_USES for item in approved_uses):
            errors.append(
                f"{path}.approved_decision_uses contains an unsupported decision use."
            )
        chain = source.get("approval_chain")
        if not isinstance(chain, list) or not chain:
            errors.append(f"{path}.approval_chain must be a non-empty list.")
        else:
            for step_index, step in enumerate(chain):
                step_path = f"{path}.approval_chain[{step_index}]"
                if not isinstance(step, dict):
                    errors.append(f"{step_path} must be an object.")
                    continue
                if step.get("sequence") != step_index + 1:
                    errors.append(
                        f"{step_path}.sequence must equal {step_index + 1}."
                    )
                for field in ("role", "actor", "status", "scope"):
                    if not isinstance(step.get(field), str) or not step[field].strip():
                        errors.append(f"{step_path}.{field} must be a non-empty string.")
                if step.get("status") == "approved":
                    if not isinstance(step.get("date"), str) or not step["date"].strip():
                        errors.append(
                            f"{step_path}.date must be supplied for an approval."
                        )
    if len(set(source_ids)) != len(source_ids):
        errors.append("parameter_governance source identifiers must be unique.")

    rules = governance.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("parameter_governance.rules must be a non-empty list.")
        rules = []
    rule_types: list[str] = []
    for index, rule in enumerate(rules):
        path = f"parameter_governance.rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{path} must be an object.")
            continue
        parameter_type = rule.get("parameter_type")
        if parameter_type not in REQUIRED_PROVENANCE_RULES:
            errors.append(f"{path}.parameter_type is unsupported.")
        else:
            rule_types.append(parameter_type)
        if rule.get("source_id") not in source_ids:
            errors.append(f"{path}.source_id must reference a declared source.")
    missing_rules = sorted(REQUIRED_PROVENANCE_RULES - set(rule_types))
    if missing_rules:
        errors.append(
            "parameter_governance.rules is missing parameter types: "
            + ", ".join(missing_rules)
            + "."
        )
    if len(set(rule_types)) != len(rule_types):
        errors.append("parameter_governance parameter types must be unique.")
    if decision_use in SUPPORTED_DECISION_USES and sources:
        if not any(
            decision_use in source.get("approved_decision_uses", [])
            for source in sources
            if isinstance(source, dict)
        ):
            errors.append(
                "No parameter source is approved for the declared evidence.decision_use."
            )


def validate_case(case: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    required_strings = (
        "schema_version",
        "case_id",
        "title",
        "domain",
        "decision_owner",
        "decision_question",
        "time_horizon",
    )
    for field in required_strings:
        if not isinstance(case.get(field), str) or not case[field].strip():
            errors.append(f"{field} must be a non-empty string.")
    if case.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            f"schema_version must be one of {sorted(SUPPORTED_SCHEMA_VERSIONS)}."
        )

    evidence = case.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence must be an object.")
    else:
        for field in ("type", "causal_claim_status", "as_of"):
            if not isinstance(evidence.get(field), str) or not evidence[field].strip():
                errors.append(f"evidence.{field} must be a non-empty string.")
        if evidence.get("decision_use") not in SUPPORTED_DECISION_USES:
            errors.append(
                "evidence.decision_use must be illustrative, exploratory, or operational."
            )
        evidence_type = str(evidence.get("type", "")).casefold()
        if evidence.get("decision_use") == "operational" and any(
            token in evidence_type
            for token in ("synthetic", "hypothetical", "illustrative")
        ):
            errors.append(
                "Operational decision use is incompatible with an evidence type "
                "labeled synthetic, hypothetical, or illustrative."
            )
        if not isinstance(evidence.get("sources"), list) or not evidence["sources"]:
            errors.append("evidence.sources must be a non-empty list.")
        elif not all(
            isinstance(source, str) and source.strip() for source in evidence["sources"]
        ):
            errors.append("evidence.sources must contain only non-empty strings.")
        if not isinstance(evidence.get("limitations"), list) or not evidence["limitations"]:
            warnings.append("evidence.limitations should disclose at least one limitation.")
        elif not all(
            isinstance(item, str) and item.strip() for item in evidence["limitations"]
        ):
            errors.append("evidence.limitations must contain only non-empty strings.")

    criteria = case.get("criteria")
    criterion_ids: list[str] = []
    if not isinstance(criteria, list) or len(criteria) < 3:
        errors.append("criteria must contain at least three items.")
        criteria = []
    for index, criterion in enumerate(criteria):
        path = f"criteria[{index}]"
        if not isinstance(criterion, dict):
            errors.append(f"{path} must be an object.")
            continue
        criterion_id = criterion.get("id")
        if not isinstance(criterion_id, str) or not criterion_id:
            errors.append(f"{path}.id must be a non-empty string.")
        else:
            criterion_ids.append(criterion_id)
        if criterion.get("direction") not in {"maximize", "minimize"}:
            errors.append(f"{path}.direction must be maximize or minimize.")
        if not _is_number(criterion.get("weight")) or criterion["weight"] < 0:
            errors.append(f"{path}.weight must be a nonnegative finite number.")
        scale = criterion.get("scale")
        if not isinstance(scale, dict):
            errors.append(f"{path}.scale must be an object.")
        elif not _is_number(scale.get("worst")) or not _is_number(scale.get("best")):
            errors.append(f"{path}.scale requires finite worst and best values.")
        elif criterion.get("direction") == "maximize" and scale["best"] <= scale["worst"]:
            errors.append(f"{path}.scale requires best > worst for maximize.")
        elif criterion.get("direction") == "minimize" and scale["best"] >= scale["worst"]:
            errors.append(f"{path}.scale requires best < worst for minimize.")
    if len(set(criterion_ids)) != len(criterion_ids):
        errors.append("Criterion identifiers must be unique.")
    weight_total = (
        sum(float(item.get("weight", 0)) for item in criteria if isinstance(item, dict))
        if criteria
        else 0.0
    )
    if criteria and weight_total <= 0:
        errors.append("At least one criterion weight must be positive.")
    elif criteria and not math.isclose(weight_total, 1.0, abs_tol=1e-6):
        warnings.append(
            f"Criterion weights sum to {weight_total:.6f}; the engine will normalize them."
        )
    _validate_uncertainty_model(
        case.get("uncertainty_model"),
        criterion_ids,
        errors,
    )

    alternatives = case.get("alternatives")
    alternative_ids: list[str] = []
    if not isinstance(alternatives, list) or len(alternatives) < 2:
        errors.append("alternatives must contain at least two items.")
        alternatives = []
    group_signatures: list[tuple[str, set[str], set[str]]] = []
    for index, alternative in enumerate(alternatives):
        path = f"alternatives[{index}]"
        if not isinstance(alternative, dict):
            errors.append(f"{path} must be an object.")
            continue
        alternative_id = alternative.get("id")
        if not isinstance(alternative_id, str) or not alternative_id:
            errors.append(f"{path}.id must be a non-empty string.")
        else:
            alternative_ids.append(alternative_id)
        for field in ("label", "description"):
            if not isinstance(alternative.get(field), str) or not alternative[field].strip():
                errors.append(f"{path}.{field} must be a non-empty string.")
        metrics = alternative.get("metrics")
        if not isinstance(metrics, dict):
            errors.append(f"{path}.metrics must be an object.")
            continue
        missing = sorted(set(criterion_ids) - set(metrics))
        extra = sorted(set(metrics) - set(criterion_ids))
        if missing:
            errors.append(f"{path}.metrics is missing criteria: {', '.join(missing)}.")
        if extra:
            errors.append(f"{path}.metrics has unknown criteria: {', '.join(extra)}.")
        for criterion_id, spec in metrics.items():
            _validate_distribution(spec, f"{path}.metrics.{criterion_id}", errors)
            if (
                case.get("schema_version") == "1.3"
                and isinstance(spec, dict)
                and "uncertainty_type" not in spec
            ):
                errors.append(
                    f"{path}.metrics.{criterion_id}.uncertainty_type is required "
                    "for schema 1.3."
                )
        groups = alternative.get("groups", [])
        if not isinstance(groups, list):
            errors.append(f"{path}.groups must be a list when present.")
        else:
            group_ids: list[str] = []
            group_metric_ids: set[str] = set()
            for group_index, group in enumerate(groups):
                group_path = f"{path}.groups[{group_index}]"
                if not isinstance(group, dict):
                    errors.append(f"{group_path} must be an object.")
                    continue
                if not isinstance(group.get("id"), str) or not group["id"]:
                    errors.append(f"{group_path}.id must be a non-empty string.")
                else:
                    group_ids.append(group["id"])
                if not isinstance(group.get("metrics"), dict) or not group["metrics"]:
                    errors.append(f"{group_path}.metrics must be a non-empty object.")
                else:
                    for metric_id, value in group["metrics"].items():
                        group_metric_ids.add(metric_id)
                        if not _is_number(value):
                            errors.append(
                                f"{group_path}.metrics.{metric_id} must be a finite number."
                            )
                        elif value < 0:
                            warnings.append(
                                f"{group_path}.metrics.{metric_id} is negative; "
                                "parity ratios will be reported as unavailable."
                            )
            if len(set(group_ids)) != len(group_ids):
                errors.append(f"{path}.groups identifiers must be unique.")
            if group_ids:
                group_signatures.append(
                    (str(alternative_id), set(group_ids), group_metric_ids)
                )
    if len(set(alternative_ids)) != len(alternative_ids):
        errors.append("Alternative identifiers must be unique.")
    if alternatives and not any(
        token in str(alt.get("id", "")).lower() or token in str(alt.get("label", "")).lower()
        for alt in alternatives
        for token in ("status", "baseline", "current", "quo")
    ):
        warnings.append("No obvious status-quo or baseline alternative was found.")
    if group_signatures:
        reference_alternative, reference_groups, reference_metrics = group_signatures[0]
        for alternative_id, compared_group_ids, metric_ids in group_signatures[1:]:
            if compared_group_ids != reference_groups:
                warnings.append(
                    f"Group identifiers differ between {reference_alternative} and "
                    f"{alternative_id}; cross-alternative parity comparisons may be incomplete."
                )
            if metric_ids != reference_metrics:
                warnings.append(
                    f"Group metric identifiers differ between {reference_alternative} and "
                    f"{alternative_id}; cross-alternative parity comparisons may be incomplete."
                )

    scenarios = case.get("scenarios")
    scenario_ids: list[str] = []
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenarios must contain at least one item.")
        scenarios = []
    probability_total = 0.0
    for index, scenario in enumerate(scenarios):
        path = f"scenarios[{index}]"
        if not isinstance(scenario, dict):
            errors.append(f"{path} must be an object.")
            continue
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id:
            errors.append(f"{path}.id must be a non-empty string.")
        else:
            scenario_ids.append(scenario_id)
        probability = scenario.get("probability")
        probability_value = (
            float(cast(float, probability)) if _is_number(probability) else 0.0
        )
        if probability_value <= 0:
            errors.append(f"{path}.probability must be a positive finite number.")
        else:
            probability_total += probability_value
        adjustments = scenario.get("adjustments", {})
        if not isinstance(adjustments, dict):
            errors.append(f"{path}.adjustments must be an object.")
            continue
        for alternative_id, metric_adjustments in adjustments.items():
            if alternative_id != "*" and alternative_id not in alternative_ids:
                errors.append(f"{path}.adjustments references unknown alternative {alternative_id}.")
            if not isinstance(metric_adjustments, dict):
                errors.append(f"{path}.adjustments.{alternative_id} must be an object.")
                continue
            for criterion_id, adjustment in metric_adjustments.items():
                if criterion_id not in criterion_ids:
                    errors.append(f"{path}.adjustments references unknown criterion {criterion_id}.")
                if not isinstance(adjustment, dict):
                    errors.append(
                        f"{path}.adjustments.{alternative_id}.{criterion_id} must be an object."
                    )
                    continue
                for operation in adjustment:
                    if operation not in {"multiply", "add"}:
                        errors.append(
                            f"{path}.adjustments uses unsupported operation {operation}."
                        )
                    elif not _is_number(adjustment[operation]):
                        errors.append(
                            f"{path}.adjustments.{alternative_id}.{criterion_id}.{operation} "
                            "must be a finite number."
                        )
    if scenarios and not math.isclose(probability_total, 1.0, abs_tol=1e-6):
        errors.append(f"Scenario probabilities must sum to 1.0; found {probability_total:.6f}.")
    if len(set(scenario_ids)) != len(scenario_ids):
        errors.append("Scenario identifiers must be unique.")

    constraints = case.get("constraints", [])
    if not isinstance(constraints, list):
        errors.append("constraints must be a list when present.")
    else:
        for index, constraint in enumerate(constraints):
            path = f"constraints[{index}]"
            if not isinstance(constraint, dict):
                errors.append(f"{path} must be an object.")
                continue
            if constraint.get("criterion") not in criterion_ids:
                errors.append(f"{path}.criterion references an unknown criterion.")
            if constraint.get("operator") not in SUPPORTED_OPERATORS:
                errors.append(f"{path}.operator must be one of {sorted(SUPPORTED_OPERATORS)}.")
            if not _is_number(constraint.get("threshold")):
                errors.append(f"{path}.threshold must be a finite number.")
            if not isinstance(constraint.get("label"), str) or not constraint["label"]:
                errors.append(f"{path}.label must be a non-empty string.")

    for field, default in (
        ("risk_aversion", 0.25),
        ("max_constraint_violation_rate", 0.10),
    ):
        value = case.get(field, default)
        if not _is_number(value) or value < 0:
            errors.append(f"{field} must be a nonnegative finite number.")
    sensitivity_multiplier = case.get("sensitivity_weight_multiplier", 1.5)
    if not _is_number(sensitivity_multiplier) or sensitivity_multiplier <= 1:
        errors.append(
            "sensitivity_weight_multiplier must be a finite number greater than 1."
        )
    risk_aversion = case.get("risk_aversion", 0.25)
    if _is_number(risk_aversion) and risk_aversion > 1:
        errors.append("risk_aversion must be between 0 and 1.")
    max_violation = case.get("max_constraint_violation_rate", 0.10)
    if _is_number(max_violation) and max_violation > 1:
        errors.append("max_constraint_violation_rate must be between 0 and 1.")

    readiness_thresholds = case.get("readiness_thresholds", {})
    if not isinstance(readiness_thresholds, dict):
        errors.append("readiness_thresholds must be an object when present.")
    else:
        unknown = sorted(
            set(readiness_thresholds) - set(DEFAULT_READINESS_THRESHOLDS)
        )
        if unknown:
            errors.append(
                "readiness_thresholds has unknown fields: " + ", ".join(unknown) + "."
            )
        for field, default in DEFAULT_READINESS_THRESHOLDS.items():
            value = readiness_thresholds.get(field, default)
            if not _is_number(value) or not 0 <= value <= 1:
                errors.append(
                    f"readiness_thresholds.{field} must be between 0 and 1."
                )

    _validate_parameter_governance(
        case.get("parameter_governance"),
        evidence.get("decision_use") if isinstance(evidence, dict) else None,
        errors,
    )

    return ValidationResult(errors=errors, warnings=warnings)


def _sample_distribution_from_uniform(
    spec: dict[str, Any],
    probability: float,
) -> float:
    """Map a copula uniform to the declared marginal distribution."""

    kind = spec["distribution"]
    probability = min(1.0 - 1e-12, max(1e-12, float(probability)))
    if kind == "fixed":
        value = float(spec["value"])
    elif kind == "normal":
        value = float(spec["mean"]) + float(spec["sd"]) * NormalDist().inv_cdf(
            probability
        )
    elif kind == "uniform":
        low, high = float(spec["low"]), float(spec["high"])
        value = low + probability * (high - low)
    elif kind == "triangular":
        low, mode, high = (
            float(spec["low"]),
            float(spec["mode"]),
            float(spec["high"]),
        )
        if high == low:
            value = low
        else:
            mode_share = (mode - low) / (high - low)
            if probability < mode_share:
                value = low + math.sqrt(
                    probability * (high - low) * (mode - low)
                )
            else:
                value = high - math.sqrt(
                    (1.0 - probability) * (high - low) * (high - mode)
                )
    elif kind in {"empirical", "bootstrap"}:
        values = sorted(float(item) for item in spec["values"])
        index = min(len(values) - 1, int(probability * len(values)))
        value = values[index]
    else:
        raise ValueError(f"Unsupported distribution: {kind}")
    if "min" in spec:
        value = max(value, float(spec["min"]))
    if "max" in spec:
        value = min(value, float(spec["max"]))
    return value


def _sample_distribution(spec: dict[str, Any], rng: random.Random) -> float:
    """Sample a marginal independently; retained as a tested public helper."""

    return _sample_distribution_from_uniform(spec, rng.random())


def _apply_adjustment(
    value: float,
    scenario: dict[str, Any],
    alternative_id: str,
    criterion_id: str,
) -> float:
    adjustments = scenario.get("adjustments", {})
    for key in ("*", alternative_id):
        adjustment = adjustments.get(key, {}).get(criterion_id, {})
        value = value * float(adjustment.get("multiply", 1.0))
        value = value + float(adjustment.get("add", 0.0))
    return value


def _distribution_support(spec: dict[str, Any]) -> tuple[float, float]:
    """Return the declared mathematical support after any explicit clamps."""

    kind = spec["distribution"]
    if kind == "fixed":
        low = high = float(spec["value"])
    elif kind == "normal":
        if float(spec["sd"]) == 0:
            low = high = float(spec["mean"])
        else:
            low = float(spec["min"]) if "min" in spec else -math.inf
            high = float(spec["max"]) if "max" in spec else math.inf
            return low, high
    elif kind == "uniform":
        low, high = float(spec["low"]), float(spec["high"])
    elif kind == "triangular":
        low, high = float(spec["low"]), float(spec["high"])
    elif kind in {"empirical", "bootstrap"}:
        values = [float(item) for item in spec["values"]]
        low, high = min(values), max(values)
    else:
        raise ValueError(f"Unsupported distribution: {kind}")

    if "min" in spec:
        lower_clamp = float(spec["min"])
        low, high = max(low, lower_clamp), max(high, lower_clamp)
    if "max" in spec:
        upper_clamp = float(spec["max"])
        low, high = min(low, upper_clamp), min(high, upper_clamp)
    return min(low, high), max(low, high)


def _adjust_support(
    support: tuple[float, float],
    scenario: dict[str, Any],
    alternative_id: str,
    criterion_id: str,
) -> tuple[float, float]:
    """Apply scenario affine transformations to an interval."""

    low, high = support
    adjustments = scenario.get("adjustments", {})
    for key in ("*", alternative_id):
        adjustment = adjustments.get(key, {}).get(criterion_id, {})
        multiplier = float(adjustment.get("multiply", 1.0))
        addition = float(adjustment.get("add", 0.0))
        if multiplier == 0:
            low = high = addition
        else:
            endpoints = (
                low * multiplier + addition,
                high * multiplier + addition,
            )
            low, high = min(endpoints), max(endpoints)
    return low, high


def _support_can_violate(
    support: tuple[float, float],
    operator: str,
    threshold: float,
) -> bool:
    low, high = support
    if operator == "<=":
        return high > threshold
    if operator == "<":
        return high >= threshold
    if operator == ">=":
        return low < threshold
    if operator == ">":
        return low <= threshold
    raise ValueError(f"Unsupported operator: {operator}")


def _constraint_support(
    alternative: dict[str, Any],
    constraint: dict[str, Any],
    scenarios: list[dict[str, Any]],
) -> dict[str, Any]:
    criterion_id = constraint["criterion"]
    threshold = float(constraint["threshold"])
    operator = constraint["operator"]
    base_support = _distribution_support(alternative["metrics"][criterion_id])
    scenario_supports: list[dict[str, Any]] = []
    for scenario in scenarios:
        support = _adjust_support(
            base_support,
            scenario,
            alternative["id"],
            criterion_id,
        )
        scenario_supports.append(
            {
                "scenario_id": scenario["id"],
                "label": scenario["label"],
                "probability": float(scenario["probability"]),
                "support_min": support[0],
                "support_max": support[1],
                "breach_possible": _support_can_violate(
                    support,
                    operator,
                    threshold,
                ),
            }
        )
    support_min = min(item["support_min"] for item in scenario_supports)
    support_max = max(item["support_max"] for item in scenario_supports)
    structural_breach_possible = any(
        item["breach_possible"] for item in scenario_supports
    )
    unbounded = not math.isfinite(support_min) or not math.isfinite(support_max)
    if not structural_breach_possible:
        support_status = "declared_support_excludes_breach"
    elif unbounded:
        support_status = "unbounded_tail"
    else:
        support_status = "modeled_tail_crosses_threshold"
    serialized_scenario_supports = [
        {
            **item,
            "support_min": (
                item["support_min"] if math.isfinite(item["support_min"]) else None
            ),
            "support_max": (
                item["support_max"] if math.isfinite(item["support_max"]) else None
            ),
        }
        for item in scenario_supports
    ]
    return {
        "support_min": support_min if math.isfinite(support_min) else None,
        "support_max": support_max if math.isfinite(support_max) else None,
        "support_status": support_status,
        "structural_breach_possible": structural_breach_possible,
        "scenario_supports": serialized_scenario_supports,
    }


def _one_sided_binomial_upper_95(events: int, samples: int) -> float:
    """Return a one-sided 95% upper bound for a binomial event probability."""

    if samples <= 0:
        return float("nan")
    if events <= 0:
        return 1.0 - 0.05 ** (1.0 / samples)
    if events >= samples:
        return 1.0
    observed = events / samples
    z = 1.6448536269514722
    z_squared = z * z
    denominator = 1.0 + z_squared / samples
    center = (observed + z_squared / (2.0 * samples)) / denominator
    half_width = (
        z
        * math.sqrt(
            observed * (1.0 - observed) / samples
            + z_squared / (4.0 * samples * samples)
        )
        / denominator
    )
    return min(1.0, center + half_width)


def _raw_normalize(value: float, criterion: dict[str, Any]) -> float:
    worst = float(criterion["scale"]["worst"])
    best = float(criterion["scale"]["best"])
    if criterion["direction"] == "maximize":
        return (value - worst) / (best - worst)
    return (worst - value) / (worst - best)


def _normalize(value: float, criterion: dict[str, Any]) -> float:
    return min(1.0, max(0.0, _raw_normalize(value, criterion)))


def _constraint_holds(value: float, operator: str, threshold: float) -> bool:
    if operator == "<=":
        return value <= threshold
    if operator == "<":
        return value < threshold
    if operator == ">=":
        return value >= threshold
    if operator == ">":
        return value > threshold
    raise ValueError(f"Unsupported operator: {operator}")


def _constraint_margin(value: float, operator: str, threshold: float) -> float:
    """Return a signed margin where positive values satisfy the constraint."""

    if operator in {"<=", "<"}:
        return threshold - value
    if operator in {">=", ">"}:
        return value - threshold
    raise ValueError(f"Unsupported operator: {operator}")


def _quantile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _mean(values: Iterable[float]) -> float:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else float("nan")


def _scenario_draws(
    scenarios: list[dict[str, Any]], samples: int, rng: random.Random
) -> list[dict[str, Any]]:
    if samples < len(scenarios):
        raise ValueError("samples must be at least the number of scenarios.")
    ideals = [float(scenario["probability"]) * samples for scenario in scenarios]
    counts = [max(1, math.floor(value)) for value in ideals]
    while sum(counts) < samples:
        candidates = sorted(
            range(len(scenarios)),
            key=lambda index: ideals[index] - counts[index],
            reverse=True,
        )
        counts[candidates[0]] += 1
    while sum(counts) > samples:
        candidates = sorted(
            (
                index
                for index, count in enumerate(counts)
                if count > 1
            ),
            key=lambda index: counts[index] - ideals[index],
            reverse=True,
        )
        if not candidates:
            raise ValueError("Unable to allocate stratified scenario samples.")
        counts[candidates[0]] -= 1
    draws = [
        scenario
        for scenario, count in zip(scenarios, counts)
        for _ in range(count)
    ]
    rng.shuffle(draws)
    return draws


def _cvar(values: list[float], tail_probability: float = 0.10) -> float:
    cutoff = max(1, math.ceil(len(values) * tail_probability))
    return _mean(sorted(values)[:cutoff])


def _risk_adjusted(
    values: list[float],
    risk_aversion: float,
) -> tuple[float, float, float]:
    expected = _mean(values)
    cvar = _cvar(values)
    adjusted = expected - risk_aversion * (expected - cvar)
    return expected, cvar, adjusted


def _pareto_frontier(
    alternative_ids: list[str],
    expected_metrics: dict[str, dict[str, float]],
    criteria: list[dict[str, Any]],
) -> list[str]:
    frontier: list[str] = []
    for candidate in alternative_ids:
        dominated = False
        for challenger in alternative_ids:
            if challenger == candidate:
                continue
            weakly_better = True
            strictly_better = False
            for criterion in criteria:
                criterion_id = criterion["id"]
                challenger_value = expected_metrics[challenger][criterion_id]
                candidate_value = expected_metrics[candidate][criterion_id]
                if criterion["direction"] == "maximize":
                    weakly_better &= challenger_value >= candidate_value
                    strictly_better |= challenger_value > candidate_value
                else:
                    weakly_better &= challenger_value <= candidate_value
                    strictly_better |= challenger_value < candidate_value
            if weakly_better and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(candidate)
    return frontier


def _group_impact_summary(alternative: dict[str, Any]) -> dict[str, Any]:
    groups = alternative.get("groups", [])
    metric_values: dict[str, list[tuple[str, str, float]]] = {}
    for group in groups:
        for metric_id, value in group.get("metrics", {}).items():
            metric_values.setdefault(metric_id, []).append(
                (group["id"], group.get("label", group["id"]), float(value))
            )
    summary: dict[str, Any] = {}
    for metric_id, values in sorted(metric_values.items()):
        numeric_values = [item[2] for item in values]
        minimum = min(numeric_values)
        maximum = max(numeric_values)
        ratio_supported = minimum >= 0 and maximum >= 0
        summary[metric_id] = {
            "absolute_gap": maximum - minimum,
            "parity_ratio": (
                1.0
                if ratio_supported and maximum == 0 and minimum == 0
                else (
                    minimum / maximum
                    if ratio_supported and maximum != 0
                    else None
                )
            ),
            "parity_ratio_supported": ratio_supported,
            "lowest_group": min(values, key=lambda item: item[2])[1],
            "highest_group": max(values, key=lambda item: item[2])[1],
            "values": {
                group_id: {"label": label, "value": value}
                for group_id, label, value in values
            },
        }
    return summary


def _factor_loading_map(
    case: dict[str, Any],
    multiplier: float,
) -> dict[str, list[tuple[str, float]]]:
    mapping: dict[str, list[tuple[str, float]]] = {
        criterion["id"]: [] for criterion in case["criteria"]
    }
    for factor in case["uncertainty_model"]["factors"]:
        for criterion_id, loading in factor["loadings"].items():
            mapping[criterion_id].append(
                (factor["id"], float(loading) * multiplier)
            )
    return mapping


def _simulate_case_draws(
    case: dict[str, Any],
    *,
    samples: int,
    seed: int,
    loading_multiplier: float,
) -> dict[str, Any]:
    """Generate aligned alternative draws under one shared latent-factor design."""

    rng = random.Random(seed)
    criteria = case["criteria"]
    alternatives = case["alternatives"]
    scenarios = case["scenarios"]
    constraints = case.get("constraints", [])
    total_weight = sum(float(criterion["weight"]) for criterion in criteria)
    weights = {
        criterion["id"]: float(criterion["weight"]) / total_weight
        for criterion in criteria
    }
    scenario_draws = _scenario_draws(scenarios, samples, rng)
    factor_ids = [
        factor["id"] for factor in case["uncertainty_model"]["factors"]
    ]
    loading_map = _factor_loading_map(case, loading_multiplier)

    raw_samples: dict[str, dict[str, list[float]]] = {}
    normalized_samples: dict[str, dict[str, list[float]]] = {}
    scale_clipped: dict[str, dict[str, list[bool]]] = {}
    utilities: dict[str, list[float]] = {}
    violations: dict[str, list[bool]] = {}
    constraint_samples: dict[str, list[dict[str, Any]]] = {}
    scenario_utility: dict[str, dict[str, list[float]]] = {}
    for alternative in alternatives:
        alternative_id = alternative["id"]
        raw_samples[alternative_id] = {
            criterion["id"]: [] for criterion in criteria
        }
        normalized_samples[alternative_id] = {
            criterion["id"]: [] for criterion in criteria
        }
        scale_clipped[alternative_id] = {
            criterion["id"]: [] for criterion in criteria
        }
        utilities[alternative_id] = []
        violations[alternative_id] = []
        constraint_samples[alternative_id] = [
            {
                "constraint_id": f"constraint-{index + 1}",
                "label": constraint["label"],
                "criterion": constraint["criterion"],
                "operator": constraint["operator"],
                "threshold": float(constraint["threshold"]),
                "violations": [],
                "margins": [],
            }
            for index, constraint in enumerate(constraints)
        ]
        scenario_utility[alternative_id] = {
            scenario["id"]: [] for scenario in scenarios
        }

    for scenario in scenario_draws:
        factor_shocks = {factor_id: rng.gauss(0.0, 1.0) for factor_id in factor_ids}
        for alternative in alternatives:
            alternative_id = alternative["id"]
            raw_row: dict[str, float] = {}
            normalized_row: dict[str, float] = {}
            for criterion in criteria:
                criterion_id = criterion["id"]
                loadings = loading_map[criterion_id]
                systematic = sum(
                    loading * factor_shocks[factor_id]
                    for factor_id, loading in loadings
                )
                residual_variance = max(
                    0.0,
                    1.0 - sum(loading**2 for _, loading in loadings),
                )
                latent_value = systematic + math.sqrt(residual_variance) * rng.gauss(
                    0.0, 1.0
                )
                probability = NormalDist().cdf(latent_value)
                value = _sample_distribution_from_uniform(
                    alternative["metrics"][criterion_id],
                    probability,
                )
                value = _apply_adjustment(
                    value,
                    scenario,
                    alternative_id,
                    criterion_id,
                )
                raw_row[criterion_id] = value
                raw_normalized = _raw_normalize(value, criterion)
                normalized_row[criterion_id] = min(
                    1.0, max(0.0, raw_normalized)
                )
                raw_samples[alternative_id][criterion_id].append(value)
                normalized_samples[alternative_id][criterion_id].append(
                    normalized_row[criterion_id]
                )
                scale_clipped[alternative_id][criterion_id].append(
                    raw_normalized < 0.0 or raw_normalized > 1.0
                )
            utility = sum(
                weights[criterion_id] * normalized_row[criterion_id]
                for criterion_id in weights
            )
            utilities[alternative_id].append(utility)
            scenario_utility[alternative_id][scenario["id"]].append(utility)
            row_violations: list[bool] = []
            for index, constraint in enumerate(constraints):
                value = raw_row[constraint["criterion"]]
                threshold = float(constraint["threshold"])
                breached = not _constraint_holds(
                    value,
                    constraint["operator"],
                    threshold,
                )
                row_violations.append(breached)
                constraint_samples[alternative_id][index]["violations"].append(
                    breached
                )
                constraint_samples[alternative_id][index]["margins"].append(
                    _constraint_margin(
                        value,
                        constraint["operator"],
                        threshold,
                    )
                )
            violations[alternative_id].append(any(row_violations))

    return {
        "raw_samples": raw_samples,
        "normalized_samples": normalized_samples,
        "scale_clipped": scale_clipped,
        "utilities": utilities,
        "violations": violations,
        "constraint_samples": constraint_samples,
        "scenario_utility": scenario_utility,
    }


def _probability_best(
    utilities: dict[str, list[float]],
    candidate_ids: list[str],
    samples: int,
) -> dict[str, float]:
    shares = {alternative_id: 0.0 for alternative_id in utilities}
    if not candidate_ids:
        return shares
    for iteration in range(samples):
        best_value = max(
            utilities[alternative_id][iteration]
            for alternative_id in candidate_ids
        )
        winners = [
            alternative_id
            for alternative_id in candidate_ids
            if math.isclose(
                utilities[alternative_id][iteration],
                best_value,
                abs_tol=1e-12,
            )
        ]
        for winner in winners:
            shares[winner] += 1.0 / len(winners)
    return {
        alternative_id: share / samples
        for alternative_id, share in shares.items()
    }


def _comparison_summary(
    simulation: dict[str, Any],
    *,
    case: dict[str, Any],
    samples: int,
) -> dict[str, Any]:
    risk_aversion = float(case.get("risk_aversion", 0.25))
    tolerance = float(case.get("max_constraint_violation_rate", 0.10))
    constraints = case.get("constraints", [])
    alternative_metrics: dict[str, dict[str, Any]] = {}
    for alternative in case["alternatives"]:
        alternative_id = alternative["id"]
        expected, cvar10, adjusted = _risk_adjusted(
            simulation["utilities"][alternative_id],
            risk_aversion,
        )
        breach_count = sum(simulation["violations"][alternative_id])
        upper = (
            _one_sided_binomial_upper_95(breach_count, samples)
            if constraints
            else 0.0
        )
        alternative_metrics[alternative_id] = {
            "expected_utility": expected,
            "cvar10": cvar10,
            "risk_adjusted_utility": adjusted,
            "constraint_violation_rate": breach_count / samples,
            "constraint_violation_rate_upper_95": upper,
            "feasible": upper <= tolerance,
        }
    ranking = sorted(
        alternative_metrics,
        key=lambda alternative_id: (
            alternative_metrics[alternative_id]["feasible"],
            alternative_metrics[alternative_id]["risk_adjusted_utility"],
            alternative_metrics[alternative_id]["expected_utility"],
        ),
        reverse=True,
    )
    feasible_ids = [
        alternative_id
        for alternative_id in ranking
        if alternative_metrics[alternative_id]["feasible"]
    ]
    p_best = _probability_best(
        simulation["utilities"],
        feasible_ids,
        samples,
    )
    for alternative_id, value in p_best.items():
        alternative_metrics[alternative_id]["probability_best"] = value
    return {
        "recommendation": feasible_ids[0] if feasible_ids else None,
        "ranking": ranking,
        "feasible_alternatives": feasible_ids,
        "alternatives": alternative_metrics,
    }


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean, right_mean = _mean(left), _mean(right)
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right)
    )
    left_scale = math.sqrt(
        sum((value - left_mean) ** 2 for value in left)
    )
    right_scale = math.sqrt(
        sum((value - right_mean) ** 2 for value in right)
    )
    return numerator / (left_scale * right_scale) if left_scale and right_scale else None


def _parameter_paths(case: dict[str, Any]) -> list[tuple[str, str]]:
    """Expand governed parameter families to individually traceable JSON paths."""

    records: list[tuple[str, str]] = []
    for criterion_index, criterion in enumerate(case["criteria"]):
        records.append((f"criteria[{criterion_index}].weight", "criterion_weight"))
        for field in ("worst", "best"):
            records.append(
                (
                    f"criteria[{criterion_index}].scale.{field}",
                    "criterion_scale",
                )
            )
    for alternative_index, alternative in enumerate(case["alternatives"]):
        for criterion_id, spec in alternative["metrics"].items():
            for field in spec:
                records.append(
                    (
                        f"alternatives[{alternative_index}].metrics."
                        f"{criterion_id}.{field}",
                        "metric_distribution",
                    )
                )
    for scenario_index, scenario in enumerate(case["scenarios"]):
        records.append(
            (
                f"scenarios[{scenario_index}].probability",
                "scenario_probability",
            )
        )
        for alternative_id, adjustments in scenario.get("adjustments", {}).items():
            for criterion_id, operations in adjustments.items():
                for operation in operations:
                    records.append(
                        (
                            f"scenarios[{scenario_index}].adjustments."
                            f"{alternative_id}.{criterion_id}.{operation}",
                            "scenario_adjustment",
                        )
                    )
    for constraint_index, _ in enumerate(case.get("constraints", [])):
        records.append(
            (
                f"constraints[{constraint_index}].threshold",
                "constraint_threshold",
            )
        )
    records.extend(
        [
            ("risk_aversion", "risk_aversion"),
            ("max_constraint_violation_rate", "maximum_violation_rate"),
            ("sensitivity_weight_multiplier", "weight_sensitivity"),
            (
                "uncertainty_model.stress_multiplier",
                "correlation_stress",
            ),
        ]
    )
    for factor_index, factor in enumerate(case["uncertainty_model"]["factors"]):
        for criterion_id in factor["loadings"]:
            records.append(
                (
                    f"uncertainty_model.factors[{factor_index}]."
                    f"loadings.{criterion_id}",
                    "correlation_loading",
                )
            )
    return records


def _provenance_coverage(case: dict[str, Any]) -> dict[str, Any]:
    governance = case["parameter_governance"]
    sources = {source["id"]: source for source in governance["sources"]}
    rules = {
        rule["parameter_type"]: rule["source_id"]
        for rule in governance["rules"]
    }
    records = []
    for path, parameter_type in _parameter_paths(case):
        source_id = rules.get(parameter_type)
        source = sources.get(source_id, {})
        approved_uses = source.get("approved_decision_uses", [])
        records.append(
            {
                "path": path,
                "parameter_type": parameter_type,
                "source_id": source_id,
                "citation": source.get("citation"),
                "source_type": source.get("source_type"),
                "owner": source.get("owner"),
                "approval_chain": source.get("approval_chain", []),
                "approved_for_declared_use": (
                    case["evidence"]["decision_use"] in approved_uses
                ),
            }
        )
    resolved = sum(bool(record["citation"]) for record in records)
    approved = sum(record["approved_for_declared_use"] for record in records)
    total = len(records)
    return {
        "coverage": {
            "parameters_required": total,
            "parameters_with_resolved_source": resolved,
            "parameters_approved_for_declared_use": approved,
            "source_coverage_rate": resolved / total if total else 1.0,
            "approval_coverage_rate": approved / total if total else 1.0,
        },
        "sources": governance["sources"],
        "records": records,
    }


def _uncertainty_inventory(case: dict[str, Any]) -> dict[str, Any]:
    """Separate marginal uncertainty by its declared substantive source."""

    records: list[dict[str, str]] = []
    counts = {key: 0 for key in sorted(SUPPORTED_UNCERTAINTY_TYPES)}
    for alternative_index, alternative in enumerate(case["alternatives"]):
        for criterion_id, specification in alternative["metrics"].items():
            uncertainty_type = specification.get(
                "uncertainty_type",
                "none" if specification["distribution"] == "fixed" else "parameter",
            )
            counts[uncertainty_type] += 1
            records.append(
                {
                    "path": (
                        f"alternatives[{alternative_index}].metrics."
                        f"{criterion_id}"
                    ),
                    "alternative_id": alternative["id"],
                    "criterion_id": criterion_id,
                    "distribution": specification["distribution"],
                    "uncertainty_type": uncertainty_type,
                }
            )
    return {
        "definitions": {
            "parameter": (
                "Uncertainty in an estimated model input or population quantity."
            ),
            "process": (
                "Irreducible or operational variation in realized outcomes."
            ),
            "scenario": (
                "Conditional uncertainty represented by named future states."
            ),
            "none": "A fixed modeled quantity with no sampled marginal variation.",
        },
        "counts": counts,
        "records": records,
    }


def analyze_case(
    case: dict[str, Any],
    *,
    samples: int = 10_000,
    seed: int = 20260726,
    source_hash: str | None = None,
) -> dict[str, Any]:
    validation = validate_case(case)
    if not validation.valid:
        raise ValueError("Invalid case:\n- " + "\n- ".join(validation.errors))
    if samples < 100:
        raise ValueError("samples must be at least 100.")

    criteria = case["criteria"]
    alternatives = case["alternatives"]
    scenarios = case["scenarios"]
    constraints = case.get("constraints", [])
    total_weight = sum(float(criterion["weight"]) for criterion in criteria)
    weights = {
        criterion["id"]: float(criterion["weight"]) / total_weight
        for criterion in criteria
    }
    main_simulation = _simulate_case_draws(
        case,
        samples=samples,
        seed=seed,
        loading_multiplier=1.0,
    )
    independent_simulation = _simulate_case_draws(
        case,
        samples=samples,
        seed=seed,
        loading_multiplier=0.0,
    )
    stress_multiplier = float(case["uncertainty_model"]["stress_multiplier"])
    stressed_simulation = _simulate_case_draws(
        case,
        samples=samples,
        seed=seed,
        loading_multiplier=stress_multiplier,
    )
    raw_samples = main_simulation["raw_samples"]
    normalized_samples = main_simulation["normalized_samples"]
    scale_clipped = main_simulation["scale_clipped"]
    utilities = main_simulation["utilities"]
    violations = main_simulation["violations"]
    constraint_samples = main_simulation["constraint_samples"]
    scenario_utility = main_simulation["scenario_utility"]

    expected_metrics = {
        alternative["id"]: {
            criterion["id"]: _mean(raw_samples[alternative["id"]][criterion["id"]])
            for criterion in criteria
        }
        for alternative in alternatives
    }

    max_violation_rate = float(case.get("max_constraint_violation_rate", 0.10))
    risk_aversion = float(case.get("risk_aversion", 0.25))
    summaries: dict[str, dict[str, Any]] = {}
    for alternative in alternatives:
        alternative_id = alternative["id"]
        utility_values = utilities[alternative_id]
        expected_utility, cvar10, risk_adjusted_utility = _risk_adjusted(
            utility_values,
            risk_aversion,
        )
        violation_count = sum(violations[alternative_id])
        violation_rate = violation_count / samples
        violation_rate_upper_95 = (
            _one_sided_binomial_upper_95(violation_count, samples)
            if constraints
            else 0.0
        )
        constraint_diagnostics = []
        for diagnostic, constraint in zip(
            constraint_samples[alternative_id],
            constraints,
        ):
            margin_values = diagnostic["margins"]
            diagnostic_violation_count = sum(diagnostic["violations"])
            support = _constraint_support(
                alternative,
                constraint,
                scenarios,
            )
            constraint_diagnostics.append(
                {
                    "constraint_id": diagnostic["constraint_id"],
                    "label": diagnostic["label"],
                    "criterion": diagnostic["criterion"],
                    "operator": diagnostic["operator"],
                    "threshold": diagnostic["threshold"],
                    "violation_count": diagnostic_violation_count,
                    "sample_count": samples,
                    "violation_rate": diagnostic_violation_count / samples,
                    "violation_rate_upper_95": _one_sided_binomial_upper_95(
                        diagnostic_violation_count,
                        samples,
                    ),
                    "mean_margin": _mean(margin_values),
                    "margin_p05": _quantile(margin_values, 0.05),
                    "margin_p95": _quantile(margin_values, 0.95),
                    **support,
                }
            )
        structural_breach_possible = any(
            diagnostic["structural_breach_possible"]
            for diagnostic in constraint_diagnostics
        )
        if any(
            diagnostic["support_status"] == "unbounded_tail"
            for diagnostic in constraint_diagnostics
        ):
            support_status = "unbounded_tail"
        elif structural_breach_possible:
            support_status = "modeled_tail_crosses_threshold"
        else:
            support_status = "declared_support_excludes_breach"
        scenario_summary: dict[str, dict[str, Any]] = {}
        for scenario in scenarios:
            values = scenario_utility[alternative_id][scenario["id"]]
            scenario_expected, scenario_cvar, scenario_adjusted = _risk_adjusted(
                values,
                risk_aversion,
            )
            scenario_summary[scenario["id"]] = {
                "label": scenario["label"],
                "mean": scenario_expected,
                "p05": _quantile(values, 0.05),
                "p95": _quantile(values, 0.95),
                "cvar10": scenario_cvar,
                "risk_adjusted_utility": scenario_adjusted,
                "sample_count": len(values),
            }
        total_clipped = sum(
            sum(scale_clipped[alternative_id][criterion["id"]])
            for criterion in criteria
        )
        total_criterion_draws = samples * len(criteria)
        summaries[alternative_id] = {
            "alternative_id": alternative_id,
            "label": alternative["label"],
            "description": alternative["description"],
            "expected_utility": expected_utility,
            "utility_p05": _quantile(utility_values, 0.05),
            "utility_p95": _quantile(utility_values, 0.95),
            "cvar10": cvar10,
            "risk_adjusted_utility": risk_adjusted_utility,
            "value_score": 100 * risk_adjusted_utility,
            "constraint_violation_count": violation_count,
            "constraint_sample_count": samples,
            "constraint_violation_rate": violation_rate,
            "constraint_violation_rate_upper_95": violation_rate_upper_95,
            "constraint_support_status": support_status,
            "structural_breach_possible": structural_breach_possible,
            "constraint_diagnostics": constraint_diagnostics,
            "feasible": violation_rate_upper_95 <= max_violation_rate,
            "overall_scale_clipping_rate": (
                total_clipped / total_criterion_draws
            ),
            "criteria": {
                criterion["id"]: {
                    "label": criterion["label"],
                    "unit": criterion.get("unit", ""),
                    "mean": expected_metrics[alternative_id][criterion["id"]],
                    "normalized_score": _mean(
                        normalized_samples[alternative_id][criterion["id"]]
                    ),
                    "scale_clipping_rate": (
                        sum(scale_clipped[alternative_id][criterion["id"]])
                        / samples
                    ),
                    "p05": _quantile(
                        raw_samples[alternative_id][criterion["id"]], 0.05
                    ),
                    "p95": _quantile(
                        raw_samples[alternative_id][criterion["id"]], 0.95
                    ),
                }
                for criterion in criteria
            },
            "scenario_utility": scenario_summary,
            "group_impacts": _group_impact_summary(alternative),
        }

    alternative_ids = [alternative["id"] for alternative in alternatives]
    ranking = sorted(
        alternative_ids,
        key=lambda alternative_id: (
            summaries[alternative_id]["feasible"],
            summaries[alternative_id]["risk_adjusted_utility"],
            summaries[alternative_id]["expected_utility"],
        ),
        reverse=True,
    )
    feasible_ids = [
        alternative_id
        for alternative_id in ranking
        if summaries[alternative_id]["feasible"]
    ]
    recommendation = feasible_ids[0] if feasible_ids else None

    probability_best_unconstrained = {
        alternative_id: 0.0 for alternative_id in alternative_ids
    }
    probability_best_feasible = {
        alternative_id: 0.0 for alternative_id in alternative_ids
    }
    for iteration in range(samples):
        best_all = max(utilities[alternative_id][iteration] for alternative_id in alternative_ids)
        winners_all = [
            alternative_id
            for alternative_id in alternative_ids
            if math.isclose(
                utilities[alternative_id][iteration],
                best_all,
                abs_tol=1e-12,
            )
        ]
        for winner in winners_all:
            probability_best_unconstrained[winner] += 1.0 / len(winners_all)
        if feasible_ids:
            best_feasible = max(
                utilities[alternative_id][iteration]
                for alternative_id in feasible_ids
            )
            winners_feasible = [
                alternative_id
                for alternative_id in feasible_ids
                if math.isclose(
                    utilities[alternative_id][iteration],
                    best_feasible,
                    abs_tol=1e-12,
                )
            ]
            for winner in winners_feasible:
                probability_best_feasible[winner] += (
                    1.0 / len(winners_feasible)
                )
    for alternative_id in alternative_ids:
        summaries[alternative_id]["probability_best"] = (
            probability_best_feasible[alternative_id] / samples
            if feasible_ids
            else 0.0
        )
        summaries[alternative_id]["probability_best_unconstrained"] = (
            probability_best_unconstrained[alternative_id] / samples
        )

    declared_comparison = _comparison_summary(
        main_simulation,
        case=case,
        samples=samples,
    )
    independent_comparison = _comparison_summary(
        independent_simulation,
        case=case,
        samples=samples,
    )
    stressed_comparison = _comparison_summary(
        stressed_simulation,
        case=case,
        samples=samples,
    )
    utility_correlations = []
    for left_index, left_id in enumerate(alternative_ids):
        for right_id in alternative_ids[left_index + 1 :]:
            utility_correlations.append(
                {
                    "left_alternative": left_id,
                    "right_alternative": right_id,
                    "correlation": _pearson(
                        utilities[left_id],
                        utilities[right_id],
                    ),
                }
            )
    correlation_sensitivity = {
        "method": UNCERTAINTY_METHOD,
        "factors": case["uncertainty_model"]["factors"],
        "stress_multiplier": stress_multiplier,
        "independent_baseline": independent_comparison,
        "declared_correlation": declared_comparison,
        "correlation_stress": stressed_comparison,
        "recommendation_changed_vs_independent": (
            declared_comparison["recommendation"]
            != independent_comparison["recommendation"]
        ),
        "recommendation_changed_under_stress": (
            declared_comparison["recommendation"]
            != stressed_comparison["recommendation"]
        ),
        "realized_pairwise_utility_correlations": utility_correlations,
    }
    provenance_coverage = _provenance_coverage(case)

    frontier_all = _pareto_frontier(alternative_ids, expected_metrics, criteria)
    frontier_feasible = (
        _pareto_frontier(feasible_ids, expected_metrics, criteria)
        if feasible_ids
        else []
    )
    for alternative_id in alternative_ids:
        summaries[alternative_id]["pareto_efficient"] = (
            alternative_id in frontier_feasible
        )
        summaries[alternative_id]["pareto_efficient_unconstrained"] = (
            alternative_id in frontier_all
        )

    sensitivity_multiplier = float(case.get("sensitivity_weight_multiplier", 1.5))
    sensitivity: list[dict[str, Any]] = []
    eligible_for_sensitivity = feasible_ids or ranking
    for criterion in criteria:
        for direction, factor, symbol in (
            ("decrease", 1.0 / sensitivity_multiplier, "↓"),
            ("increase", sensitivity_multiplier, "↑"),
        ):
            varied_weights = dict(weights)
            varied_weights[criterion["id"]] *= factor
            varied_total = sum(varied_weights.values())
            varied_weights = {
                criterion_id: weight / varied_total
                for criterion_id, weight in varied_weights.items()
            }
            score_details: dict[str, dict[str, float]] = {}
            for alternative_id in eligible_for_sensitivity:
                varied_utilities = [
                    sum(
                        varied_weights[criterion_id]
                        * normalized_samples[alternative_id][criterion_id][iteration]
                        for criterion_id in varied_weights
                    )
                    for iteration in range(samples)
                ]
                expected, cvar, adjusted = _risk_adjusted(
                    varied_utilities,
                    risk_aversion,
                )
                score_details[alternative_id] = {
                    "expected_utility": expected,
                    "cvar10": cvar,
                    "risk_adjusted_utility": adjusted,
                }
            scores = {
                alternative_id: detail["risk_adjusted_utility"]
                for alternative_id, detail in score_details.items()
            }
            winner = max(scores, key=scores.__getitem__)
            sensitivity.append(
                {
                    "criterion": criterion["id"],
                    "label": f"{symbol} {criterion['label']}",
                    "direction": direction,
                    "factor": factor,
                    "winner": winner,
                    "scores": scores,
                    "score_details": score_details,
                }
            )
    stability = (
        sum(item["winner"] == recommendation for item in sensitivity) / len(sensitivity)
        if recommendation and sensitivity
        else 0.0
    )

    scenario_analysis: list[dict[str, Any]] = []
    scenario_stability_weighted = 0.0
    scenario_stability_count = 0.0
    scenario_candidates = feasible_ids or ranking
    for scenario in scenarios:
        scenario_id = scenario["id"]
        best_value = max(
            summaries[alternative_id]["scenario_utility"][scenario_id][
                "risk_adjusted_utility"
            ]
            for alternative_id in scenario_candidates
        )
        winners = [
            alternative_id
            for alternative_id in scenario_candidates
            if math.isclose(
                summaries[alternative_id]["scenario_utility"][scenario_id][
                    "risk_adjusted_utility"
                ],
                best_value,
                abs_tol=1e-12,
            )
        ]
        recommendation_share = (
            1.0 / len(winners)
            if recommendation and recommendation in winners
            else 0.0
        )
        scenario_stability_weighted += (
            float(scenario["probability"]) * recommendation_share
        )
        scenario_stability_count += recommendation_share
        scenario_analysis.append(
            {
                "scenario_id": scenario_id,
                "label": scenario["label"],
                "probability": float(scenario["probability"]),
                "winners": winners,
                "winner": winners[0],
                "recommended_option_wins": bool(
                    recommendation and recommendation in winners
                ),
            }
        )
    scenario_stability_count = (
        scenario_stability_count / len(scenarios) if scenarios else 0.0
    )

    readiness_thresholds = {
        **DEFAULT_READINESS_THRESHOLDS,
        **case.get("readiness_thresholds", {}),
    }
    decision_use = case["evidence"]["decision_use"]
    if recommendation:
        recommended_summary = summaries[recommendation]
        feasible_runners = [
            alternative_id
            for alternative_id in ranking
            if alternative_id != recommendation
            and summaries[alternative_id]["feasible"]
        ]
        utility_margin = (
            recommended_summary["risk_adjusted_utility"]
            - summaries[feasible_runners[0]]["risk_adjusted_utility"]
            if feasible_runners
            else recommended_summary["risk_adjusted_utility"]
        )
        constraint_headroom = (
            max(
                0.0,
                min(
                    1.0,
                    (
                        max_violation_rate
                        - recommended_summary["constraint_violation_rate_upper_95"]
                    )
                    / max_violation_rate,
                ),
            )
            if max_violation_rate > 0
            else (
                1.0
                if recommended_summary["constraint_violation_rate_upper_95"] == 0
                else 0.0
            )
        )
        robustness_components = {
            "probability_best": {
                "value": recommended_summary["probability_best"],
                "weight": 0.30,
            },
            "weight_stability": {
                "value": stability,
                "weight": 0.25,
            },
            "scenario_stability": {
                "value": scenario_stability_weighted,
                "weight": 0.25,
            },
            "constraint_headroom": {
                "value": constraint_headroom,
                "weight": 0.20,
            },
        }
        robustness_score = 100 * sum(
            component["value"] * component["weight"]
            for component in robustness_components.values()
        )
        readiness_checks = {
            "feasible_alternative": True,
            "probability_best": (
                recommended_summary["probability_best"]
                >= readiness_thresholds["minimum_probability_best"]
            ),
            "weight_stability": (
                stability
                >= readiness_thresholds["minimum_weight_stability"]
            ),
            "scenario_stability": (
                scenario_stability_weighted
                >= readiness_thresholds["minimum_scenario_stability"]
            ),
            "scale_clipping": (
                recommended_summary["overall_scale_clipping_rate"]
                <= readiness_thresholds["maximum_scale_clipping_rate"]
            ),
            "parameter_provenance": (
                provenance_coverage["coverage"]["source_coverage_rate"] == 1.0
            ),
            "approval_scope": (
                provenance_coverage["coverage"]["approval_coverage_rate"] == 1.0
            ),
            "operational_evidence": decision_use == "operational",
        }
    else:
        utility_margin = 0.0
        robustness_components = {
            "probability_best": {"value": 0.0, "weight": 0.30},
            "weight_stability": {"value": 0.0, "weight": 0.25},
            "scenario_stability": {"value": 0.0, "weight": 0.25},
            "constraint_headroom": {"value": 0.0, "weight": 0.20},
        }
        robustness_score = 0.0
        readiness_checks = {
            "feasible_alternative": False,
            "probability_best": False,
            "weight_stability": False,
            "scenario_stability": False,
            "scale_clipping": False,
            "parameter_provenance": (
                provenance_coverage["coverage"]["source_coverage_rate"] == 1.0
            ),
            "approval_scope": (
                provenance_coverage["coverage"]["approval_coverage_rate"] == 1.0
            ),
            "operational_evidence": decision_use == "operational",
        }

    blocking_reasons = [
        label
        for key, label in (
            ("feasible_alternative", "no alternative satisfies the feasibility rule"),
            ("probability_best", "modeled preference separation is below threshold"),
            ("weight_stability", "the winner is sensitive to criterion weights"),
            ("scenario_stability", "the winner changes across material scenarios"),
            ("scale_clipping", "reference scales clip too many modeled outcomes"),
            ("parameter_provenance", "one or more parameters lacks a resolved source"),
            ("approval_scope", "parameter approvals do not cover the declared decision use"),
            ("operational_evidence", "evidence is not labeled for operational use"),
        )
        if not readiness_checks[key]
    ]
    if not recommendation:
        decision_status = "no_feasible_option"
    elif decision_use == "illustrative":
        decision_status = "illustrative_preference"
    elif all(readiness_checks.values()):
        decision_status = "decision_ready"
    else:
        decision_status = "provisional"
    decision_status_labels = {
        "no_feasible_option": "No feasible option",
        "illustrative_preference": "Illustrative preference",
        "provisional": "Provisional—validate before action",
        "decision_ready": "Decision-ready under stated thresholds",
    }

    reported_criteria = [
        {
            **criterion,
            "normalized_weight": weights[criterion["id"]],
        }
        for criterion in criteria
    ]

    return {
        "metadata": {
            "engine": "high-stakes-analytics-decision-lab",
            "engine_version": ENGINE_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "case_id": case["case_id"],
            "case_hash_sha256": source_hash,
            "samples": samples,
            "seed": seed,
            "warnings": validation.warnings,
            "sampling_design": (
                "Stratified scenario allocation with a declared latent-factor Gaussian "
                "copula, shared shocks across alternatives, marginal-preserving inverse "
                "transforms, and matched independent/correlation-stress counterfactuals."
            ),
        },
        "decision": {
            "title": case["title"],
            "domain": case["domain"],
            "owner": case["decision_owner"],
            "question": case["decision_question"],
            "time_horizon": case["time_horizon"],
            "recommendation": recommendation,
            "recommendation_available": recommendation is not None,
            "decision_ready": decision_status == "decision_ready",
            "decision_status": decision_status,
            "decision_status_label": decision_status_labels[decision_status],
            "decision_use": decision_use,
            "ranking": ranking,
            "pareto_frontier": frontier_feasible,
            "pareto_frontier_unconstrained": frontier_all,
            "probability_best_scope": "decision-feasible alternatives",
            "utility_margin": utility_margin,
            "weight_sensitivity_stability": stability,
            "scenario_stability_probability_weighted": scenario_stability_weighted,
            "scenario_stability_count": scenario_stability_count,
            "robustness_score": robustness_score,
            "robustness_components": robustness_components,
            "readiness_thresholds": readiness_thresholds,
            "readiness_checks": readiness_checks,
            "blocking_reasons": blocking_reasons,
            "max_constraint_violation_rate": max_violation_rate,
            "feasibility_basis": (
                "one-sided 95% upper confidence bound on simulated "
                "constraint-breach frequency"
            ),
            "risk_aversion": risk_aversion,
        },
        "criteria": reported_criteria,
        "constraints": constraints,
        "scenarios": scenarios,
        "scenario_analysis": scenario_analysis,
        "alternatives": summaries,
        "weight_sensitivity": sensitivity,
        "correlation_sensitivity": correlation_sensitivity,
        "parameter_provenance": provenance_coverage,
        "uncertainty_inventory": _uncertainty_inventory(case),
        "evidence": case["evidence"],
        "decision_notes": case.get("decision_notes", []),
    }


def _format_number(value: float, unit: str = "") -> str:
    absolute = abs(value)
    if absolute >= 1_000_000:
        number = f"{value / 1_000_000:.2f}M"
    elif absolute >= 1_000:
        number = f"{value:,.0f}"
    elif absolute >= 10:
        number = f"{value:.1f}"
    else:
        number = f"{value:.3f}".rstrip("0").rstrip(".")
    return f"{number} {unit}".strip()


def _format_breach_estimate(summary: dict[str, Any]) -> str:
    count = int(summary["constraint_violation_count"])
    samples = int(summary["constraint_sample_count"])
    observed = float(summary["constraint_violation_rate"])
    upper = float(summary["constraint_violation_rate_upper_95"])
    support_status = summary["constraint_support_status"]
    if count == 0:
        support_note = (
            "; declared support excludes breach"
            if support_status == "declared_support_excludes_breach"
            else ""
        )
        return f"0/{samples:,} observed; U95 {upper:.2%}{support_note}"
    return f"{observed:.1%} ({count:,}/{samples:,}); U95 {upper:.1%}"


def _format_support_range(diagnostic: dict[str, Any]) -> str:
    low = diagnostic["support_min"]
    high = diagnostic["support_max"]
    low_text = "−∞" if low is None else f"{low:.3g}"
    high_text = "+∞" if high is None else f"{high:.3g}"
    status_text = {
        "declared_support_excludes_breach": "excludes breach",
        "modeled_tail_crosses_threshold": "tail crosses threshold",
        "unbounded_tail": "unbounded tail",
    }[diagnostic["support_status"]]
    return f"{low_text}–{high_text}; {status_text}"


def render_report(
    case: dict[str, Any],
    result: dict[str, Any],
    figure_paths: dict[str, str] | None = None,
) -> str:
    decision = result["decision"]
    alternatives = result["alternatives"]
    ranking = decision["ranking"]
    recommendation_id = decision["recommendation"]
    figures = figure_paths or {
        "decision_scorecard": "figures/decision-scorecard.svg",
        "robustness_profile": "figures/robustness-profile.svg",
        "alternative_ranking": "figures/alternative-ranking.svg",
        "constraint_risk": "figures/constraint-risk.svg",
        "utility_uncertainty": "figures/utility-uncertainty.svg",
        "correlation_stress": "figures/correlation-stress.svg",
        "criterion_scorecard": "figures/criterion-scorecard.svg",
        "scenario_performance": "figures/scenario-performance.svg",
        "weight_sensitivity": "figures/weight-sensitivity.svg",
        "group_impact": "figures/group-impact.svg",
    }

    recommended = alternatives[recommendation_id] if recommendation_id else None
    feasible_others = [
        alternatives[alternative_id]
        for alternative_id in ranking
        if alternative_id != recommendation_id and alternatives[alternative_id]["feasible"]
    ]
    runner_up = feasible_others[0] if feasible_others else (
        alternatives[ranking[1]] if len(ranking) > 1 else None
    )

    criterion_differences: list[tuple[float, str]] = []
    if recommended and runner_up:
        for criterion in result["criteria"]:
            criterion_id = criterion["id"]
            difference = (
                recommended["criteria"][criterion_id]["normalized_score"]
                - runner_up["criteria"][criterion_id]["normalized_score"]
            )
            criterion_differences.append((difference, criterion["label"]))
    strengths = [item for item in sorted(criterion_differences, reverse=True) if item[0] > 0]
    tradeoffs = [item for item in sorted(criterion_differences) if item[0] < 0]

    scenario_values: list[tuple[float, str, str]] = []
    scenario_overturns: list[str] = []
    if recommended:
        for scenario_analysis in result["scenario_analysis"]:
            scenario_id = scenario_analysis["scenario_id"]
            recommendation_value = recommended["scenario_utility"][scenario_id][
                "risk_adjusted_utility"
            ]
            scenario_values.append(
                (
                    recommendation_value,
                    scenario_analysis["label"],
                    scenario_id,
                )
            )
            if recommendation_id not in scenario_analysis["winners"]:
                scenario_overturns.append(
                    f"{scenario_analysis['label']} favors "
                    f"{alternatives[scenario_analysis['winner']]['label']}"
                )
    worst_scenario = min(scenario_values) if scenario_values else None

    uncertainty_widths: list[tuple[float, str]] = []
    if recommended:
        for criterion in result["criteria"]:
            metric = recommended["criteria"][criterion["id"]]
            width = abs(
                _normalize(metric["p95"], criterion) - _normalize(metric["p05"], criterion)
            )
            uncertainty_widths.append((width, criterion["label"]))
    most_uncertain = max(uncertainty_widths)[1] if uncertainty_widths else "key outcomes"

    sensitivity_switches = [
        item for item in result["weight_sensitivity"] if item["winner"] != recommendation_id
    ]
    group_impact_summary = recommended["group_impacts"] if recommended else {}
    parity_values = [
        (metric["parity_ratio"], metric_id, metric)
        for metric_id, metric in group_impact_summary.items()
        if metric["parity_ratio"] is not None
    ]
    weakest_parity = min(parity_values) if parity_values else None
    correlation = result["correlation_sensitivity"]
    declared_correlation_metrics = (
        correlation["declared_correlation"]["alternatives"].get(recommendation_id)
        if recommendation_id
        else None
    )
    independent_metrics = (
        correlation["independent_baseline"]["alternatives"].get(recommendation_id)
        if recommendation_id
        else None
    )
    stressed_metrics = (
        correlation["correlation_stress"]["alternatives"].get(recommendation_id)
        if recommendation_id
        else None
    )
    provenance_coverage = result["parameter_provenance"]["coverage"]
    if decision["decision_status"] == "illustrative_preference":
        first_next_step = (
            "1. **Replace every synthetic input before any pilot or operational use.** "
            "Re-estimate outcomes from traceable descriptive, predictive, causal, "
            "financial, policy, or engineering evidence."
        )
    elif decision["decision_status"] == "provisional":
        first_next_step = (
            "1. **Resolve the failed readiness checks before acting.** "
            + "; ".join(decision["blocking_reasons"])
            + "."
        )
    elif recommended:
        first_next_step = (
            f"1. **Run a bounded pilot of {recommended['label']}.** Define a stop "
            "rule tied to the modeled constraints and preserve a reversible fallback."
        )
    else:
        first_next_step = (
            "1. **Expand or redesign the alternative set.** No modeled option "
            "currently satisfies the feasibility rule."
        )

    lines: list[str] = [
        f"# {decision['title']}",
        "",
        f"*{decision['domain']} · {decision['time_horizon']} · "
        f"{result['metadata']['samples']:,} modeled simulations*",
        "",
        "## Executive Summary",
        "",
    ]
    if recommended:
        assert declared_correlation_metrics is not None
        assert independent_metrics is not None
        assert stressed_metrics is not None
        utility_gap = decision["utility_margin"]
        utility_gap_text = (
            "<0.001" if 0 <= utility_gap < 0.0005 else f"{utility_gap:.3f}"
        )
        preference_label = {
            "illustrative_preference": "Illustrative preference",
            "provisional": "Provisional preference",
            "decision_ready": "Recommendation",
        }.get(decision["decision_status"], "Preferred modeled option")
        blocking_text = (
            "; ".join(decision["blocking_reasons"])
            if decision["blocking_reasons"]
            else "all configured readiness checks pass"
        )
        lines.extend(
            [
                f"- **{preference_label} — {recommended['label']}.** It is the highest-ranked "
                f"feasible option, with decision value score **{recommended['value_score']:.1f}/100** "
                f"and a modeled **{recommended['probability_best']:.0%} probability of being best "
                "among decision-feasible alternatives**.",
                f"- **The lead is {'narrow' if utility_gap < 0.04 else 'meaningful'} rather than absolute.** "
                + (
                    f"It leads the next feasible option, {runner_up['label']}, by "
                    f"**{utility_gap_text} utility points**."
                    if runner_up
                    else "No other option satisfies the stated feasibility rule."
                ),
                f"- **Modeled robustness is {decision['robustness_score']:.0f}/100.** "
                f"The option remains preferred in **{decision['weight_sensitivity_stability']:.0%}** "
                f"of two-sided weight stresses and **{decision['scenario_stability_probability_weighted']:.0%}** "
                "of probability-weighted scenario comparisons.",
                f"- **Shared-shock sensitivity is explicit.** Relative to independent residuals, "
                f"the declared factor model changes this option's P(best) by "
                f"**{declared_correlation_metrics['probability_best'] - independent_metrics['probability_best']:+.1%}** "
                f"and CVaR10 by **{declared_correlation_metrics['cvar10'] - independent_metrics['cvar10']:+.3f}**; "
                f"the ×{correlation['stress_multiplier']:.2f} loading stress "
                f"{'changes' if correlation['recommendation_changed_under_stress'] else 'does not change'} "
                "the modeled winner.",
                f"- **Constraint-breach evidence — {_format_breach_estimate(recommended)}.** "
                f"Feasibility uses the one-sided 95% upper bound against the "
                f"**{decision['max_constraint_violation_rate']:.1%} tolerance**; a zero event "
                "count is never presented as proof of zero real-world risk.",
                f"- **Decision status — {decision['decision_status_label']}.** "
                f"The current blockers are: {blocking_text}.",
                f"- **Evidence boundary.** {result['evidence']['causal_claim_status']}",
                f"- **Parameter lineage.** {provenance_coverage['parameters_with_resolved_source']}/"
                f"{provenance_coverage['parameters_required']} governed parameters have a resolved "
                "source and approval-chain reference.",
                "",
                f"![Decision summary]({figures['decision_scorecard']})",
                "",
                f"**Decision owner:** {decision['owner']}",
                f"**Decision question:** {decision['question']}",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "- **No feasible modeled alternative.** Every option exceeds at least one "
                "hard-constraint tolerance too often.",
                "- **Revise the choice set or collect better evidence before committing.** "
                "A forced ranking would hide infeasibility.",
                "",
                f"![Decision summary]({figures['decision_scorecard']})",
                "",
            ]
        )

    checks_passed = sum(decision["readiness_checks"].values())
    checks_total = len(decision["readiness_checks"])
    lines.extend(
        [
            "## Decision status and modeled robustness",
            "",
            f"**Status: {decision['decision_status_label']}.** "
            f"{checks_passed} of {checks_total} configured readiness checks pass. "
            "The robustness score summarizes model behavior; it is not a posterior "
            "probability that the real-world decision is correct and cannot upgrade "
            "illustrative evidence into operational evidence.",
            "",
            f"![Decision robustness profile]({figures['robustness_profile']})",
            "",
        ]
    )

    if recommended:
        assert declared_correlation_metrics is not None
        assert independent_metrics is not None
        assert stressed_metrics is not None
        advantage_phrase = (
            ", ".join(label for _, label in strengths[:2])
            if strengths
            else "balanced performance across the weighted criteria"
        )
        tradeoff_phrase = tradeoffs[0][1] if tradeoffs else "no single modeled criterion"
        lines.extend(
            [
                f"## {recommended['label']} leads on balanced value, not every dimension",
                "",
                f"**The preferred option earns its position through {advantage_phrase}.** "
                f"The comparison still exposes a trade-off on **{tradeoff_phrase}**, so the "
                "decision should be presented as a transparent compromise rather than a universal optimum.",
                "",
                f"![Alternative ranking]({figures['alternative_ranking']})",
                "",
                f"The ranking combines expected value with downside performance and excludes options "
                f"whose one-sided 95% breach-frequency upper bound exceeds "
                f"**{decision['max_constraint_violation_rate']:.0%}**. "
                "Probability-best remains visible because a lower-ranked option may still win in a "
                "material share of simulations.",
                "",
                "## The conservative risk boundary determines feasibility",
                "",
                f"**The decision rule compares the one-sided 95% breach-frequency upper bound—not "
                f"only the observed simulation rate—with the {decision['max_constraint_violation_rate']:.1%} "
                "tolerance.** This makes finite-sample uncertainty visible and prevents a zero event "
                "count from being presented as proof of zero risk.",
                "",
                f"![Constraint risk boundary]({figures['constraint_risk']})",
                "",
                "The dark circle is the observed breach rate; the diamond is its conservative upper "
                "bound. An option fails the modeled feasibility rule when that diamond crosses the "
                "red tolerance line. The test is conditional on the declared distributions and cannot "
                "cover omitted real-world hazards.",
                "",
                "## The criterion profile reveals where the preferred option earns—and gives up—value",
                "",
                "Each cell below places an outcome on its declared worst-to-best reference scale. "
                "This avoids recalibrating the chart around whichever alternatives happen to be present.",
                "",
                f"![Criterion scorecard]({figures['criterion_scorecard']})",
                "",
                f"**The decision is therefore driven by an explicit value model.** A stakeholder who "
                f"places substantially more weight on {tradeoff_phrase} may reasonably prefer another "
                "option; the two-sided weight-sensitivity section tests that possibility directly. "
                f"The preferred option clips **{recommended['overall_scale_clipping_rate']:.1%}** "
                "of criterion draws at the declared reference-scale bounds.",
                "",
                "## Downside risk remains visible behind the average",
                "",
                f"**{recommended['label']} has expected utility {recommended['expected_utility']:.3f}, "
                f"but its worst-decile average falls to {recommended['cvar10']:.3f}.** "
                f"The widest criterion-level uncertainty for this option is associated with "
                f"**{most_uncertain}**, making it a priority for further evidence collection.",
                "",
                f"![Utility uncertainty and downside]({figures['utility_uncertainty']})",
                "",
                "The interval chart prevents a precise-looking average from obscuring overlap among "
                "alternatives. A close overlap means the practical decision may depend more on "
                "constraints, reversibility, and the cost of learning than on a small utility difference.",
                "",
                "## Shared shocks change the uncertainty question",
                "",
                f"**The declared factor model gives {recommended['label']} P(best) "
                f"{declared_correlation_metrics['probability_best']:.0%}, versus "
                f"{independent_metrics['probability_best']:.0%} under independent residuals and "
                f"{stressed_metrics['probability_best']:.0%} under the stronger correlation stress.** "
                f"Its CVaR10 moves from {independent_metrics['cvar10']:.3f} independently to "
                f"{declared_correlation_metrics['cvar10']:.3f} under declared dependence and "
                f"{stressed_metrics['cvar10']:.3f} under stress.",
                "",
                f"![Correlation and tail-risk stress]({figures['correlation_stress']})",
                "",
                "The three states use matched seeds, stratified scenario counts, and the same marginal "
                "distributions. Differences therefore isolate the declared dependence structure as closely "
                "as this simulation design allows. The Gaussian copula remains an approximation: factor "
                "definitions, signs, and loadings must be replaced or approved using domain evidence.",
                "",
                "## Scenario tests show when the preferred option is most exposed",
                "",
            ]
        )
        if worst_scenario:
            lines.append(
                f"**The weakest modeled environment is {worst_scenario[1]}, where the preferred "
                f"option's risk-adjusted utility is {worst_scenario[0]:.3f}.** "
                + (
                    "At least one scenario changes the leading feasible alternative: "
                    + "; ".join(scenario_overturns)
                    + "."
                    if scenario_overturns
                    else "The same feasible alternative remains ahead in every modeled scenario."
                )
            )
        lines.extend(
            [
                "",
                f"![Scenario performance]({figures['scenario_performance']})",
                "",
                f"The preferred option leads in **{decision['scenario_stability_probability_weighted']:.0%}** "
                "of the probability-weighted scenario comparison. Scenario probabilities are "
                "assumptions, not forecasts with guaranteed calibration. "
                "They are useful because they reveal which external conditions deserve monitoring and "
                "which contingency plans should be prepared before implementation.",
                "",
            ]
        )

        if "group_impact" in figures and group_impact_summary:
            group_takeaway = (
                f"The weakest descriptive parity ratio is **{weakest_parity[0]:.2f}** for "
                f"**{weakest_parity[1].replace('_', ' ')}**, between "
                f"{weakest_parity[2]['lowest_group']} and {weakest_parity[2]['highest_group']}."
                if weakest_parity
                else "The supplied group metrics do not support a parity comparison."
            )
            lines.extend(
                [
                    "## Distributional effects require a separate judgment",
                    "",
                    f"**Average utility does not establish equitable impact.** {group_takeaway} "
                    "The ratios below are descriptive diagnostics; they cannot resolve questions "
                    "about rights, need, historical disadvantage, or acceptable error asymmetry.",
                    "",
                    f"![Group-impact parity overview]({figures['group_impact']})",
                    "",
                    "Use the visual to locate disparities that require subgroup analysis and stakeholder "
                    "review. Do not optimize the ratios mechanically or treat similarity as proof of fairness.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "## Distributional effects remain an evidence gap",
                    "",
                    "**No group-level outcomes were supplied for this case.** Before operational use, "
                    "the analysis should add affected groups, absolute outcomes, disparity measures, and "
                    "a qualitative review of harms that cannot be reduced to a numeric parity ratio.",
                    "",
                ]
            )

        lines.extend(
            [
                f"## The result is {'stable' if not sensitivity_switches else 'sensitive'} to stakeholder priorities",
                "",
                f"**The baseline choice survives {decision['weight_sensitivity_stability']:.0%} of local "
                "weight stresses.** "
                + (
                    "No single criterion emphasis changes the preferred feasible alternative."
                    if not sensitivity_switches
                    else "The following weight perturbation changes the winner: "
                    + "; ".join(
                        f"{item['label']} → {alternatives[item['winner']]['label']}"
                        for item in sensitivity_switches
                    )
                    + "."
                ),
                "",
                f"![Weight sensitivity]({figures['weight_sensitivity']})",
                "",
                "This test both increases and decreases each criterion weight while preserving "
                "risk adjustment. It remains a local stress test rather than a substitute for formal "
                "stakeholder elicitation. "
                "If the winner changes under a plausible emphasis, the next step is deliberation and better "
                "evidence—not hiding the sensitivity.",
                "",
                "## Recommended next steps",
                "",
                first_next_step,
                f"2. **Reduce uncertainty in {most_uncertain}.** Validate or replace the widest "
                "uncertainty input using experimental, quasi-experimental, observational, or "
                "engineering evidence appropriate to the domain.",
                f"3. **Monitor the {worst_scenario[1] if worst_scenario else 'most adverse'} trigger.** "
                "Specify leading indicators and a contingency response before rollout.",
                "4. **Review distributional impacts with affected stakeholders.** Examine absolute group "
                "outcomes alongside disparity measures and document unresolved normative choices.",
                "",
                "## Further questions",
                "",
                "- Which empirical or elicited evidence would best validate the declared factor loadings?",
                "- Which omitted externality or stakeholder could materially alter the criterion set?",
                "- What evidence would justify replacing the current scenario probabilities?",
                "- Is the preferred option reversible if early monitoring contradicts the model?",
                "",
            ]
        )

    lines.extend(
        [
            "## Caveats and assumptions",
            "",
            f"- **Evidence type:** {result['evidence']['type']}",
            f"- **Evidence as of:** {result['evidence']['as_of']}",
            f"- **Permitted decision use:** {result['evidence']['decision_use']}",
            f"- **Causal status:** {result['evidence']['causal_claim_status']}",
            f"- **Dependence model:** {correlation['method']} with "
            f"{len(correlation['factors'])} declared shared factor(s); the loading stress is "
            f"×{correlation['stress_multiplier']:.2f}. Copula choice and loadings remain assumptions.",
            f"- **Parameter provenance:** {provenance_coverage['source_coverage_rate']:.0%} source "
            f"coverage and {provenance_coverage['approval_coverage_rate']:.0%} approval coverage "
            f"for the declared decision use. Approval for {result['evidence']['decision_use']} "
            "use is not operational approval.",
            "- **Zero-breach interpretation:** zero simulated events means either no event was "
            "observed in the finite run or the declared bounded input support excludes a breach. "
            "Neither statement establishes zero real-world risk.",
        ]
    )
    lines.extend(f"- {limitation}" for limitation in result["evidence"].get("limitations", []))
    lines.extend(
        f"- **Validation warning:** {warning}"
        for warning in result["metadata"].get("warnings", [])
    )
    lines.extend(
        [
            "",
            "<details>",
            "<summary><strong>Detailed numerical appendix and reproducibility</strong></summary>",
            "",
            "### Ranked alternatives",
            "",
            "| Rank | Alternative | Feasible | Value score | Expected utility | CVaR10 | P(best feasible) | P(best all) | Breach evidence | Feasible Pareto |",
            "|---:|---|:---:|---:|---:|---:|---:|---:|---|:---:|",
        ]
    )
    for rank, alternative_id in enumerate(ranking, start=1):
        summary = alternatives[alternative_id]
        probability_best_text = (
            f"{summary['probability_best']:.1%}"
            if summary["feasible"]
            else "n/a"
        )
        lines.append(
            f"| {rank} | {summary['label']} | {'Yes' if summary['feasible'] else 'No'} | "
            f"{summary['value_score']:.1f} | {summary['expected_utility']:.3f} | "
            f"{summary['cvar10']:.3f} | "
            f"{probability_best_text} | "
            f"{summary['probability_best_unconstrained']:.1%} | "
            f"{_format_breach_estimate(summary)} | "
            f"{'Yes' if summary['pareto_efficient'] else 'No'} |"
        )
    lines.extend(
        [
            "",
            "### Readiness checks",
            "",
            "| Check | Result |",
            "|---|:---:|",
        ]
    )
    for check, passed in decision["readiness_checks"].items():
        lines.append(
            f"| {check.replace('_', ' ').title()} | {'Pass' if passed else 'Fail'} |"
        )
    lines.extend(["", "### Constraint diagnostics", ""])
    if result["constraints"]:
        lines.extend(
            [
                "| Alternative | Constraint | Events | Observed | U95 | Declared support | Mean signed margin | P05–P95 margin |",
                "|---|---|---:|---:|---:|---|---:|---:|",
            ]
        )
        for alternative_id in ranking:
            summary = alternatives[alternative_id]
            for diagnostic in summary["constraint_diagnostics"]:
                lines.append(
                    f"| {summary['label']} | {diagnostic['label']} | "
                    f"{diagnostic['violation_count']:,}/{diagnostic['sample_count']:,} | "
                    f"{diagnostic['violation_rate']:.1%} | "
                    f"{diagnostic['violation_rate_upper_95']:.2%} | "
                    f"{_format_support_range(diagnostic)} | "
                    f"{diagnostic['mean_margin']:.3f} | "
                    f"{diagnostic['margin_p05']:.3f}–{diagnostic['margin_p95']:.3f} |"
                )
    else:
        lines.append("No hard constraints were supplied.")
    lines.extend(["", "### Criterion outcomes", ""])
    for alternative_id in ranking:
        summary = alternatives[alternative_id]
        lines.extend(
            [
                f"#### {summary['label']}",
                "",
                "| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for criterion in result["criteria"]:
            metric = summary["criteria"][criterion["id"]]
            unit = metric["unit"]
            lines.append(
                f"| {metric['label']} | {criterion['normalized_weight']:.1%} | "
                f"{_format_number(metric['mean'], unit)} | "
                f"{_format_number(metric['p05'], unit)}–{_format_number(metric['p95'], unit)} | "
                f"{metric['normalized_score']:.3f} | "
                f"{metric['scale_clipping_rate']:.1%} |"
            )
        lines.append("")
    lines.extend(
        [
            "### Correlation sensitivity",
            "",
            "| Dependence state | Modeled winner | Recommended option P(best) | CVaR10 | Breach U95 |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for label, comparison in (
        ("Independent residuals", correlation["independent_baseline"]),
        ("Declared factor model", correlation["declared_correlation"]),
        (
            f"Loading stress ×{correlation['stress_multiplier']:.2f}",
            correlation["correlation_stress"],
        ),
    ):
        mode_recommendation = comparison["recommendation"]
        mode_label = (
            alternatives[mode_recommendation]["label"]
            if mode_recommendation
            else "No feasible option"
        )
        metric = comparison["alternatives"].get(recommendation_id, {}) if recommendation_id else {}
        lines.append(
            f"| {label} | {mode_label} | "
            f"{metric.get('probability_best', 0.0):.1%} | "
            f"{metric.get('cvar10', float('nan')):.3f} | "
            f"{metric.get('constraint_violation_rate_upper_95', float('nan')):.2%} |"
        )
    lines.extend(
        [
            "",
            "### Parameter provenance and approval",
            "",
            f"Coverage: **{provenance_coverage['parameters_with_resolved_source']}/"
            f"{provenance_coverage['parameters_required']} parameters sourced** and "
            f"**{provenance_coverage['parameters_approved_for_declared_use']}/"
            f"{provenance_coverage['parameters_required']} approved for the declared use**. "
            "Every expanded JSON path is recorded in `decision-results.json` under "
            "`parameter_provenance.records`.",
            "",
            "| Source ID | Source type | Owner | Approved uses | Approval chain |",
            "|---|---|---|---|---|",
        ]
    )
    for source in result["parameter_provenance"]["sources"]:
        chain_text = " → ".join(
            f"{step['sequence']}. {step['role']} ({step['status']})"
            for step in source["approval_chain"]
        )
        lines.append(
            f"| `{source['id']}` | {source['source_type']} | {source['owner']} | "
            f"{', '.join(source['approved_decision_uses'])} | {chain_text} |"
        )
    metadata = result["metadata"]
    lines.extend(
        [
            "### Sources and reproducibility",
            "",
        ]
    )
    lines.extend(f"- {source}" for source in result["evidence"].get("sources", []))
    lines.extend(
        [
            f"- Engine version: `{metadata['engine_version']}`",
            f"- Samples: `{metadata['samples']}`",
            f"- Random seed: `{metadata['seed']}`",
            f"- Sampling design: {metadata['sampling_design']}",
            f"- Case SHA-256: `{metadata['case_hash_sha256'] or 'not supplied'}`",
        ]
    )
    if result.get("decision_notes"):
        lines.extend(["", "### Decision notes", ""])
        lines.extend(f"- {note}" for note in result["decision_notes"])
    lines.extend(
        [
            "",
            "</details>",
            "",
            (
                "> Synthetic test fixture only. This report is not medical, financial, "
                "legal, engineering-safety, or public-policy advice."
                if "synthetic" in str(result["evidence"].get("type", "")).casefold()
                else "> Source-backed exploratory analysis, not an authorization to act. "
                "Domain review and current local evidence remain required."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    case: dict[str, Any],
    result: dict[str, Any],
    output_dir: str | Path,
) -> tuple[Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    result_path = output_path / "decision-results.json"
    report_path = output_path / "decision-report.md"
    figure_paths = generate_visuals(case, result, output_path)
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report_path.write_text(
        render_report(case, result, figure_paths=figure_paths),
        encoding="utf-8",
    )
    return result_path, report_path
