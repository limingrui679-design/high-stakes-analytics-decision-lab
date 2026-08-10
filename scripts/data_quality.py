#!/usr/bin/env python3
"""Data-readiness profiling and controlled preprocessing for uploaded case data."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

from visual_system import (
    BLUE,
    CORAL,
    GRID,
    INK,
    MUTED,
    PAPER,
    TEAL,
    VIOLET,
    rounded_rect,
    svg_document,
    text,
    wrapped_text,
)

DEFAULT_MISSING_TOKENS = {
    "",
    "?",
    "na",
    "n/a",
    "nan",
    "null",
}
SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DATE_NAME_RE = re.compile(r"(^|_)(date|time|timestamp|datetime|year|month|day)($|_)", re.I)
DIRECT_IDENTIFIER_NAME_RE = re.compile(
    r"(^|_)(email|e_mail|phone|mobile|telephone|ssn|passport|ip_address)($|_)",
    re.I,
)
ALLOWED_INTENDED_USES = {
    "descriptive",
    "diagnostic",
    "predictive",
    "prescriptive",
    "mixed",
    "unspecified",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def read_dataset(path: Path) -> tuple[list[dict[str, str]], list[str], dict[str, Any]]:
    """Read CSV, TSV, JSON-array, or JSONL data without external dependencies."""

    suffix = path.suffix.casefold()
    if suffix in {".csv", ".tsv"}:
        with path.open(encoding="utf-8-sig") as sample_handle:
            sample = sample_handle.read(8192)
        dialect: Any
        if suffix == ".tsv":
            dialect = csv.excel_tab
        else:
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle, dialect=dialect)
            try:
                raw_fields = next(reader)
            except StopIteration:
                return [], [], {
                    "format": suffix.lstrip("."),
                    "shape_warnings": ["missing_header"],
                }
            raw_records = list(reader)

        shape_warnings: list[str] = []
        fields: list[str] = []
        used_fields: set[str] = set()
        for index, raw_field in enumerate(raw_fields, 1):
            base = str(raw_field).strip()
            if not base:
                base = f"__unnamed_column_{index}"
                shape_warnings.append("blank_header")
            candidate = base
            duplicate_index = 2
            while candidate in used_fields:
                candidate = f"{base}__duplicate_{duplicate_index}"
                duplicate_index += 1
            if candidate != base:
                shape_warnings.append("duplicate_header")
            fields.append(candidate)
            used_fields.add(candidate)

        maximum_width = max([len(raw_fields), *(len(record) for record in raw_records)])
        if maximum_width > len(fields):
            shape_warnings.append("extra_fields_without_header")
            extra_index = 1
            while len(fields) < maximum_width:
                candidate = f"__extra_column_{extra_index}"
                extra_index += 1
                while candidate in used_fields:
                    candidate = f"__extra_column_{extra_index}"
                    extra_index += 1
                fields.append(candidate)
                used_fields.add(candidate)
        if any(len(record) != len(raw_fields) for record in raw_records):
            shape_warnings.append("ragged_rows")
        rows = [
            {
                field: _stringify(record[index]) if index < len(record) else ""
                for index, field in enumerate(fields)
            }
            for record in raw_records
        ]
        return rows, fields, {
            "format": suffix.lstrip("."),
            "shape_warnings": sorted(set(shape_warnings)),
        }

    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            payload = payload["rows"]
        if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
            raise ValueError("JSON input must be an array of objects or an object with a rows array.")
        raw_rows = payload
    elif suffix in {".jsonl", ".ndjson"}:
        raw_rows = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"JSONL line {line_number} is not an object.")
            raw_rows.append(record)
    else:
        raise ValueError("Supported input formats are CSV, TSV, JSON, JSONL, and NDJSON.")

    json_fields: list[str] = []
    seen: set[str] = set()
    for row in raw_rows:
        for field in row:
            field_name = str(field)
            if field_name not in seen:
                seen.add(field_name)
                json_fields.append(field_name)
    rows = [
        {field: _stringify(row.get(field)) for field in json_fields}
        for row in raw_rows
    ]
    shape_warnings = [
        "mixed_object_shape"
        for row in raw_rows
        if set(map(str, row.keys())) != set(json_fields)
    ]
    return rows, json_fields, {
        "format": suffix.lstrip("."),
        "shape_warnings": sorted(set(shape_warnings)),
    }


def _default_contract(dataset_name: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "contract_source": "inferred_default",
        "dataset_name": dataset_name,
        "intended_use": "unspecified",
        "grain": "not_declared",
        "required_columns": [],
        "primary_key": [],
        "date_columns": [],
        "numeric_columns": [],
        "numeric_ranges": {},
        "categorical_columns": {},
        "target_column": None,
        "feature_columns": [],
        "forbidden_columns": [],
        "direct_identifier_columns": [],
        "sensitive_columns": [],
        "missing_tokens": sorted(DEFAULT_MISSING_TOKENS),
        "missing_tokens_source": "inferred_default",
        "thresholds": {
            "required_column_missing_rate_max": 0.0,
            "primary_key_duplicate_rate_max": 0.0,
            "invalid_type_rate_max": 0.0,
            "future_date_rate_max": 0.0,
            "high_missing_rate": 0.5,
        },
    }


def load_contract(path: Path | None, *, dataset_name: str) -> dict[str, Any]:
    contract = _default_contract(dataset_name)
    if path is None:
        return contract
    supplied = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(supplied, dict):
        raise ValueError("The data contract must be a JSON object.")
    contract.update(supplied)
    contract["contract_source"] = "user_supplied"
    contract["missing_tokens_source"] = (
        "user_supplied" if "missing_tokens" in supplied else "inferred_default"
    )
    for key in (
        "required_columns",
        "primary_key",
        "date_columns",
        "numeric_columns",
        "feature_columns",
        "forbidden_columns",
        "direct_identifier_columns",
        "sensitive_columns",
    ):
        if not isinstance(contract.get(key), list) or not all(
            isinstance(item, str) and item.strip() for item in contract[key]
        ):
            raise ValueError(f"contract.{key} must be an array of non-empty column names.")
        contract[key] = list(dict.fromkeys(item.strip() for item in contract[key]))
    if not isinstance(contract.get("categorical_columns"), dict):
        raise ValueError("contract.categorical_columns must map column names to allowed values.")
    for column, values in contract["categorical_columns"].items():
        if (
            not isinstance(column, str)
            or not column.strip()
            or not isinstance(values, list)
            or not all(isinstance(value, str) for value in values)
        ):
            raise ValueError(
                f"contract.categorical_columns.{column} must be an array of strings."
            )
    if not isinstance(contract.get("numeric_ranges"), dict):
        raise ValueError("contract.numeric_ranges must map column names to range objects.")
    for column, bounds in contract["numeric_ranges"].items():
        if not isinstance(column, str) or not column.strip() or not isinstance(bounds, dict):
            raise ValueError(f"contract.numeric_ranges.{column} must be an object.")
        unknown_bounds = sorted(set(bounds) - {"minimum", "maximum"})
        if unknown_bounds:
            raise ValueError(
                f"contract.numeric_ranges.{column} contains unknown keys: "
                + ", ".join(unknown_bounds)
            )
        for bound_name, bound in bounds.items():
            try:
                numeric_bound = float(bound)
            except (OverflowError, TypeError, ValueError):
                numeric_bound = math.nan
            if isinstance(bound, bool) or not isinstance(bound, (int, float)) or not math.isfinite(numeric_bound):
                raise ValueError(
                    f"contract.numeric_ranges.{column}.{bound_name} must be finite numeric."
                )
        if (
            "minimum" in bounds
            and "maximum" in bounds
            and float(bounds["minimum"]) > float(bounds["maximum"])
        ):
            raise ValueError(
                f"contract.numeric_ranges.{column}.minimum cannot exceed maximum."
            )
    if not isinstance(contract.get("missing_tokens"), list) or not all(
        isinstance(token, str) for token in contract["missing_tokens"]
    ):
        raise ValueError("contract.missing_tokens must be an array of strings.")
    contract["missing_tokens"] = list(dict.fromkeys(contract["missing_tokens"]))
    intended_use = contract.get("intended_use")
    if intended_use not in ALLOWED_INTENDED_USES:
        raise ValueError(
            "contract.intended_use must be descriptive, diagnostic, predictive, "
            "prescriptive, mixed, or unspecified."
        )
    if not isinstance(contract.get("grain"), str) or not contract["grain"].strip():
        raise ValueError("contract.grain must be a non-empty string.")
    if not isinstance(contract.get("dataset_name"), str) or not contract["dataset_name"].strip():
        raise ValueError("contract.dataset_name must be a non-empty string.")
    default_thresholds = _default_contract(dataset_name)["thresholds"]
    supplied_thresholds = contract.get("thresholds", {})
    if not isinstance(supplied_thresholds, dict):
        raise ValueError("contract.thresholds must be an object.")
    unknown_thresholds = sorted(set(supplied_thresholds) - set(default_thresholds))
    if unknown_thresholds:
        raise ValueError(
            "contract.thresholds contains unknown keys: " + ", ".join(unknown_thresholds)
        )
    thresholds = {**default_thresholds, **supplied_thresholds}
    for key, value in thresholds.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"contract.thresholds.{key} must be numeric.")
        try:
            numeric_value = float(value)
        except OverflowError:
            numeric_value = math.nan
        if not math.isfinite(numeric_value) or not 0 <= numeric_value <= 1:
            raise ValueError(f"contract.thresholds.{key} must be between 0 and 1.")
    contract["thresholds"] = thresholds
    if contract.get("target_column") is not None and not isinstance(
        contract["target_column"], str
    ):
        raise ValueError("contract.target_column must be a column name or null.")
    if isinstance(contract.get("target_column"), str):
        contract["target_column"] = contract["target_column"].strip()
        if not contract["target_column"]:
            raise ValueError("contract.target_column must be a non-empty column name or null.")
    typed_groups = {
        "numeric": set(contract["numeric_columns"]) | set(contract["numeric_ranges"]),
        "datetime": set(contract["date_columns"]),
        "categorical": set(contract["categorical_columns"]),
    }
    overlaps = sorted(
        (typed_groups["numeric"] & typed_groups["datetime"])
        | (typed_groups["numeric"] & typed_groups["categorical"])
        | (typed_groups["datetime"] & typed_groups["categorical"])
    )
    if overlaps:
        raise ValueError(
            "Columns cannot have conflicting declared types: " + ", ".join(overlaps)
        )
    return contract


def _missing_tokens(contract: dict[str, Any]) -> set[str]:
    return {str(token).strip().casefold() for token in contract["missing_tokens"]}


def is_missing(value: Any, tokens: set[str]) -> bool:
    return _stringify(value).strip().casefold() in tokens


def _parse_number(value: str) -> float | None:
    normalized = value.strip()
    if not normalized:
        return None
    try:
        result = float(normalized)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def _parse_decimal(value: str) -> Decimal | None:
    normalized = value.strip()
    if not normalized:
        return None
    try:
        result = Decimal(normalized)
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _normalized_column_name(column: str) -> str:
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", column)
    return re.sub(r"[^a-z0-9]+", "_", separated.casefold()).strip("_")


def _parse_date(value: str) -> datetime | None:
    normalized = value.strip()
    if not normalized:
        return None
    for pattern in ("%Y", "%Y-%m", "%Y-%m-%d"):
        try:
            return datetime.strptime(normalized, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = probability * (len(ordered) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def _infer_type(column: str, values: list[str], tokens: set[str]) -> str:
    observed = [value.strip() for value in values if not is_missing(value, tokens)]
    if not observed:
        return "empty"
    lowered = {value.casefold() for value in observed}
    if lowered <= {"true", "false", "yes", "no", "0", "1"}:
        return "boolean"
    if all(_parse_number(value) is not None for value in observed):
        return "numeric"
    if DATE_NAME_RE.search(column) and all(_parse_date(value) is not None for value in observed):
        return "datetime"
    distinct = len(set(observed))
    if distinct <= max(20, int(math.sqrt(len(observed))) + 1):
        return "categorical"
    return "text"


def _finding(
    findings: list[dict[str, Any]],
    *,
    code: str,
    severity: str,
    title: str,
    evidence: str,
    impact: str,
    remediation: str,
    columns: Iterable[str] = (),
    confidence: str = "high",
) -> None:
    findings.append(
        {
            "id": f"dq-{len(findings) + 1:03d}",
            "code": code,
            "severity": severity,
            "confidence": confidence,
            "title": title,
            "columns": list(columns),
            "evidence": evidence,
            "impact": impact,
            "recommended_remediation": remediation,
        }
    )


def _profile_rows(
    rows: list[dict[str, str]],
    fields: list[str],
    *,
    source_name: str,
    source_sha256: str,
    source_format: str,
    shape_warnings: list[str],
    contract: dict[str, Any],
) -> dict[str, Any]:
    tokens = _missing_tokens(contract)
    row_count = len(rows)
    column_count = len(fields)
    findings: list[dict[str, Any]] = []
    thresholds = contract["thresholds"]

    if not fields:
        _finding(
            findings,
            code="schema_missing",
            severity="critical",
            title="No header or fields were detected",
            evidence="The input exposes zero named columns.",
            impact="The dataset cannot be interpreted at a stable grain.",
            remediation="Provide a tabular file with a header or a JSON object array.",
        )
    if not rows:
        _finding(
            findings,
            code="empty_dataset",
            severity="critical",
            title="The dataset contains no records",
            evidence="Row count is zero.",
            impact="No analytical result can be supported.",
            remediation="Provide a non-empty extract and confirm its intended grain.",
        )
    critical_shape_warnings = sorted(
        set(shape_warnings)
        & {"missing_header", "blank_header", "duplicate_header", "extra_fields_without_header"}
    )
    if critical_shape_warnings:
        _finding(
            findings,
            code="ambiguous_schema",
            severity="critical",
            title="The file does not expose one unambiguous header schema",
            evidence=(
                f"{len(critical_shape_warnings)} critical shape condition(s) were detected: "
                + ", ".join(critical_shape_warnings)
                + "."
            ),
            impact="Column identity cannot be trusted without silently renaming or losing values.",
            remediation="Repair the header and row widths in the source, then rerun the gate.",
        )
    noncritical_shape_warnings = sorted(
        set(shape_warnings) - set(critical_shape_warnings)
    )
    if noncritical_shape_warnings:
        _finding(
            findings,
            code="mixed_shape",
            severity="high",
            title="Records do not share one stable schema",
            evidence=(
                f"{len(noncritical_shape_warnings)} shape condition(s) were detected: "
                + ", ".join(noncritical_shape_warnings)
                + "."
            ),
            impact="Missing fields may reflect ingestion shape rather than real missingness.",
            remediation="Normalize records to one declared schema before analysis.",
        )

    missing_schema = sorted(
        column for column in contract["required_columns"] if column not in fields
    )
    if missing_schema:
        _finding(
            findings,
            code="required_columns_absent",
            severity="critical",
            title="Required columns are absent",
            evidence=f"{len(missing_schema)} required columns are missing from the schema.",
            impact="The declared estimand or downstream method cannot be evaluated.",
            remediation="Provide the missing fields or revise the data contract.",
            columns=missing_schema,
        )
    declared_method_columns = set(contract["numeric_columns"])
    declared_method_columns.update(contract["date_columns"])
    declared_method_columns.update(contract["categorical_columns"])
    absent_method_columns = sorted(declared_method_columns - set(fields))
    if absent_method_columns:
        _finding(
            findings,
            code="declared_columns_absent",
            severity="high",
            title="Declared analytical columns are absent",
            evidence=(
                f"{len(absent_method_columns)} typed or categorical contract columns "
                "do not exist in the source."
            ),
            impact="Validity checks and downstream method assumptions cannot be executed.",
            remediation="Correct the contract or provide the declared fields.",
            columns=absent_method_columns,
        )
    feature_columns_absent = sorted(set(contract["feature_columns"]) - set(fields))
    if feature_columns_absent and contract["intended_use"] in {"predictive", "mixed"}:
        _finding(
            findings,
            code="feature_columns_absent",
            severity="critical",
            title="Declared predictive features are absent",
            evidence=f"{len(feature_columns_absent)} model features are missing from the source.",
            impact="The declared predictive design cannot be reproduced.",
            remediation="Provide the missing features or revise the predictive contract.",
            columns=feature_columns_absent,
        )
    target = contract.get("target_column")
    if contract["intended_use"] in {"predictive", "mixed"} and not target:
        _finding(
            findings,
            code="target_unspecified",
            severity="critical",
            title="Predictive use has no declared target",
            evidence="The contract requests predictive analysis but target_column is null.",
            impact="Model labels, validation timing, and leakage boundaries are undefined.",
            remediation="Declare the outcome and when it becomes observable.",
        )
    elif target and target not in fields:
        _finding(
            findings,
            code="target_absent",
            severity="critical",
            title="The declared target column is absent",
            evidence="The outcome named by target_column does not exist in the source.",
            impact="The declared predictive or evaluative analysis cannot be run.",
            remediation="Provide the outcome field or correct the contract.",
            columns=[target],
        )
    if target and target in contract["feature_columns"]:
        _finding(
            findings,
            code="target_feature_overlap",
            severity="critical",
            title="The target is also declared as a model feature",
            evidence="One column appears in both target_column and feature_columns.",
            impact="Validation would contain direct target leakage.",
            remediation="Remove the target from the feature set and rebuild the model design.",
            columns=[target],
        )

    profiles: dict[str, dict[str, Any]] = {}
    total_missing = 0
    trim_affected = 0
    missing_token_affected = 0
    email_columns: list[str] = []
    now = datetime.now(timezone.utc)
    for field in fields:
        values = [row.get(field, "") for row in rows]
        missing_count = sum(is_missing(value, tokens) for value in values)
        total_missing += missing_count
        missing_token_affected += sum(
            value.strip().casefold() in tokens and bool(value.strip()) for value in values
        )
        trim_affected += sum(value != value.strip() for value in values)
        observed = [value.strip() for value in values if not is_missing(value, tokens)]
        distinct_count = len(set(observed))
        inferred_type = _infer_type(field, values, tokens)
        profile: dict[str, Any] = {
            "missing_count": missing_count,
            "missing_rate": missing_count / row_count if row_count else 0.0,
            "non_missing_count": len(observed),
            "distinct_count": distinct_count,
            "unique_rate_non_missing": distinct_count / len(observed) if observed else 0.0,
            "inferred_type": inferred_type,
            "constant_non_missing": bool(observed) and distinct_count == 1,
        }
        if observed:
            counts = Counter(observed)
            profile["largest_category_share"] = max(counts.values()) / len(observed)

        declared_numeric = (
            field in contract["numeric_columns"] or field in contract["numeric_ranges"]
        )
        declared_date = field in contract["date_columns"]
        if declared_numeric or inferred_type == "numeric":
            parsed = [_parse_number(value) for value in observed]
            valid = [value for value in parsed if value is not None]
            invalid = len(parsed) - len(valid)
            profile["numeric"] = {
                "valid_count": len(valid),
                "invalid_count": invalid,
                "invalid_rate": invalid / len(observed) if observed else 0.0,
            }
            if valid:
                q1 = _quantile(valid, 0.25)
                median = _quantile(valid, 0.5)
                q3 = _quantile(valid, 0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = sum(value < lower or value > upper for value in valid)
                profile["numeric"].update(
                    {
                        "minimum": min(valid),
                        "q1": q1,
                        "median": median,
                        "q3": q3,
                        "maximum": max(valid),
                        "iqr_outlier_count": outliers,
                        "iqr_outlier_rate": outliers / len(valid),
                    }
                )
                identifier_like = (
                    field in contract["primary_key"]
                    or field.casefold() == "id"
                    or field.casefold().endswith("_id")
                )
                if outliers and not identifier_like:
                    _finding(
                        findings,
                        code="numeric_outliers",
                        severity="medium",
                        title=f"Robust outlier flags appear in {field}",
                        evidence=(
                            f"{outliers}/{len(valid)} valid numeric values fall outside "
                            "the 1.5×IQR fences."
                        ),
                        impact="Extreme values may dominate summaries or model fitting.",
                        remediation=(
                            "Inspect provenance and influence; do not delete, cap, or impute "
                            "without a declared rule."
                        ),
                        columns=[field],
                    )
                bounds = contract["numeric_ranges"].get(field)
                if bounds:
                    minimum = float(bounds["minimum"]) if "minimum" in bounds else None
                    maximum = float(bounds["maximum"]) if "maximum" in bounds else None
                    outside = sum(
                        (minimum is not None and value < minimum)
                        or (maximum is not None and value > maximum)
                        for value in valid
                    )
                    profile["numeric"]["outside_declared_range_count"] = outside
                    profile["numeric"]["outside_declared_range_rate"] = outside / len(valid)
                    if outside:
                        _finding(
                            findings,
                            code="numeric_range_violation",
                            severity="high",
                            title=f"Values in {field} violate the declared range",
                            evidence=(
                                f"{outside}/{len(valid)} valid numeric values fall outside "
                                "the inclusive contract bounds."
                            ),
                            impact="Domain-invalid values may bias summaries, models, or constraints.",
                            remediation=(
                                "Confirm units and source validity; do not cap or delete values "
                                "without a documented rule."
                            ),
                            columns=[field],
                        )
            invalid_numeric_rate = invalid / len(observed) if observed else 0.0
            if (
                declared_numeric
                and invalid_numeric_rate > thresholds["invalid_type_rate_max"]
            ):
                _finding(
                    findings,
                    code="invalid_numeric",
                    severity="high",
                    title=f"Declared numeric column {field} contains invalid values",
                    evidence=f"{invalid}/{len(observed)} non-missing values do not parse as finite numbers.",
                    impact="Numeric calculations would silently lose or misread records.",
                    remediation="Correct the source values or approve a documented exclusion rule.",
                    columns=[field],
                )

        if declared_date or inferred_type == "datetime":
            parsed_dates = [_parse_date(value) for value in observed]
            valid_dates = [value for value in parsed_dates if value is not None]
            invalid_dates = len(parsed_dates) - len(valid_dates)
            future_dates = sum(value > now for value in valid_dates)
            profile["datetime"] = {
                "valid_count": len(valid_dates),
                "invalid_count": invalid_dates,
                "invalid_rate": invalid_dates / len(observed) if observed else 0.0,
                "future_count": future_dates,
                "future_rate": future_dates / len(valid_dates) if valid_dates else 0.0,
                "minimum": min(valid_dates).isoformat() if valid_dates else None,
                "maximum": max(valid_dates).isoformat() if valid_dates else None,
            }
            if declared_date and invalid_dates:
                _finding(
                    findings,
                    code="invalid_datetime",
                    severity="high",
                    title=f"Declared date column {field} contains unparseable periods",
                    evidence=f"{invalid_dates}/{len(observed)} non-missing values are not reliable ISO-like dates.",
                    impact="Temporal ordering, leakage checks, and out-of-time validation are unreliable.",
                    remediation="Resolve ambiguous dates and declare the timezone before temporal analysis.",
                    columns=[field],
                )
            if (
                valid_dates
                and future_dates / len(valid_dates) > thresholds["future_date_rate_max"]
            ):
                _finding(
                    findings,
                    code="future_dates",
                    severity="high",
                    title=f"Future-dated records appear in {field}",
                    evidence=f"{future_dates}/{len(valid_dates)} parsed dates are after the profiling time.",
                    impact="The extract may contain entry errors or information unavailable at decision time.",
                    remediation="Confirm valid scheduled dates or correct the source before time-based analysis.",
                    columns=[field],
                )

        allowed = contract["categorical_columns"].get(field)
        if allowed is not None:
            allowed_normalized = {value.strip().casefold() for value in allowed}
            invalid_values = sum(
                value.casefold() not in allowed_normalized for value in observed
            )
            profile["categorical_validity"] = {
                "allowed_value_count": len(allowed),
                "invalid_count": invalid_values,
                "invalid_rate": invalid_values / len(observed) if observed else 0.0,
            }
            if invalid_values:
                _finding(
                    findings,
                    code="invalid_category",
                    severity="high",
                    title=f"Unexpected categories appear in {field}",
                    evidence=f"{invalid_values}/{len(observed)} non-missing values fall outside the allowed set.",
                    impact="Segments or model encodings may be inconsistent.",
                    remediation="Confirm a source-backed mapping; do not merge categories by spelling similarity alone.",
                    columns=[field],
                )

        missing_rate = profile["missing_rate"]
        if field in contract["required_columns"] and (
            missing_rate > thresholds["required_column_missing_rate_max"]
        ):
            _finding(
                findings,
                code="required_missingness",
                severity="high",
                title=f"Required column {field} is incomplete",
                evidence=f"{missing_count}/{row_count} rows are missing-coded ({missing_rate:.1%}).",
                impact="The declared analysis would exclude or impute decision-relevant records.",
                remediation="Recover the field or obtain approval for a route-specific missing-data rule.",
                columns=[field],
            )
        elif missing_rate >= 0.9 and row_count:
            _finding(
                findings,
                code="near_empty_column",
                severity="high",
                title=f"Column {field} is almost entirely missing",
                evidence=f"{missing_count}/{row_count} rows are missing-coded ({missing_rate:.1%}).",
                impact="The field cannot support stable segmentation or modeling.",
                remediation="Confirm whether the field is optional, withheld, or broken upstream.",
                columns=[field],
            )
        elif missing_rate > thresholds["high_missing_rate"] and row_count:
            _finding(
                findings,
                code="high_missingness",
                severity="medium",
                title=f"Column {field} has high missingness",
                evidence=f"{missing_count}/{row_count} rows are missing-coded ({missing_rate:.1%}).",
                impact="Complete-case analysis may be selective and imputation may drive results.",
                remediation="Compare missingness by time and segment before selecting a treatment.",
                columns=[field],
            )
        if profile["constant_non_missing"] and observed:
            _finding(
                findings,
                code="constant_column",
                severity="low",
                title=f"Column {field} is constant among observed records",
                evidence=f"All {len(observed)} non-missing values are identical.",
                impact="The field adds no variation for the current extract.",
                remediation="Retain for lineage if needed; exclude from modeling only with documentation.",
                columns=[field],
            )

        email_count = sum(EMAIL_RE.fullmatch(value) is not None for value in observed)
        identifier_declared = field in contract["direct_identifier_columns"]
        identifier_named = (
            DIRECT_IDENTIFIER_NAME_RE.search(_normalized_column_name(field)) is not None
        )
        if email_count or identifier_declared or (identifier_named and observed):
            profile["direct_identifier_signal_count"] = (
                len(observed) if identifier_declared or identifier_named else email_count
            )
            email_columns.append(field)
        profiles[field] = profile

    row_tuples = [tuple(row.get(field, "") for field in fields) for row in rows]
    exact_duplicate_count = len(row_tuples) - len(set(row_tuples))
    normalized_rows = [
        tuple(
            "" if is_missing(row.get(field, ""), tokens) else row.get(field, "").strip().casefold()
            for field in fields
        )
        for row in rows
    ]
    normalized_duplicate_count = len(normalized_rows) - len(set(normalized_rows))
    if exact_duplicate_count:
        _finding(
            findings,
            code="exact_duplicates",
            severity="medium",
            title="Exact duplicate records were detected",
            evidence=f"{exact_duplicate_count}/{row_count} rows duplicate an earlier complete row.",
            impact="Counts and fitted weights may be unintentionally inflated.",
            remediation="Confirm whether repeated rows are legitimate events before approving removal.",
        )
    near_duplicate_excess = max(0, normalized_duplicate_count - exact_duplicate_count)
    if near_duplicate_excess:
        _finding(
            findings,
            code="normalized_duplicates",
            severity="medium",
            title="Whitespace- or case-normalized duplicates were detected",
            evidence=f"{near_duplicate_excess} additional rows collide after normalization.",
            impact="Formatting differences may hide duplicate records.",
            remediation="Review the intended key; do not merge entities based only on normalized text.",
        )

    primary_key = list(contract["primary_key"])
    key_source = "declared"
    if not primary_key:
        candidates = [
            field
            for field in fields
            if field.casefold() == "id" or field.casefold().endswith("_id")
        ]
        for candidate in candidates:
            values = [row.get(candidate, "").strip() for row in rows]
            if values and all(not is_missing(value, tokens) for value in values):
                primary_key = [candidate]
                key_source = "inferred_candidate"
                break
    key_summary: dict[str, Any] = {
        "columns": primary_key,
        "source": key_source if primary_key else "not_available",
        "missing_count": None,
        "duplicate_row_count": None,
        "duplicate_rate": None,
    }
    if primary_key:
        absent_key_columns = [column for column in primary_key if column not in fields]
        if absent_key_columns:
            _finding(
                findings,
                code="primary_key_absent",
                severity="critical",
                title="Primary-key columns are absent",
                evidence=f"{len(absent_key_columns)} declared key columns do not exist.",
                impact="The intended grain cannot be verified.",
                remediation="Correct the contract or provide the missing key columns.",
                columns=absent_key_columns,
            )
        else:
            keys = [tuple(row.get(column, "").strip() for column in primary_key) for row in rows]
            missing_keys = sum(any(is_missing(value, tokens) for value in key) for key in keys)
            complete_keys = [key for key in keys if not any(is_missing(value, tokens) for value in key)]
            duplicate_keys = len(complete_keys) - len(set(complete_keys))
            duplicate_rate = duplicate_keys / row_count if row_count else 0.0
            key_summary.update(
                {
                    "missing_count": missing_keys,
                    "duplicate_row_count": duplicate_keys,
                    "duplicate_rate": duplicate_rate,
                }
            )
            if missing_keys:
                _finding(
                    findings,
                    code="primary_key_missing",
                    severity="critical",
                    title="Primary key contains missing values",
                    evidence=f"{missing_keys}/{row_count} rows lack a complete key.",
                    impact="Record identity and join integrity are not trustworthy.",
                    remediation="Recover key values or redefine the grain before analysis.",
                    columns=primary_key,
                )
            if duplicate_rate > thresholds["primary_key_duplicate_rate_max"]:
                _finding(
                    findings,
                    code="primary_key_duplicates",
                    severity="critical",
                    title="Primary key is not unique at the declared grain",
                    evidence=f"{duplicate_keys}/{row_count} rows repeat an earlier complete key.",
                    impact="Aggregations, joins, and model weights may be invalid.",
                    remediation="Resolve whether the data are duplicated or the grain/key is wrong.",
                    columns=primary_key,
                )

    identifier_columns = sorted(set(email_columns) | set(contract["direct_identifier_columns"]))
    populated_identifier_columns = [
        field
        for field in identifier_columns
        if field in fields and profiles[field]["non_missing_count"] > 0
    ]
    if populated_identifier_columns:
        counts = sum(
            profiles[field].get("direct_identifier_signal_count", profiles[field]["non_missing_count"])
            for field in populated_identifier_columns
        )
        _finding(
            findings,
            code="direct_identifiers_present",
            severity="high",
            title="Direct-identifier signals are present",
            evidence=(
                f"{len(populated_identifier_columns)} columns contain {counts} populated "
                "identifier-like cells; raw values are not reproduced in this report."
            ),
            impact="Public sharing or downstream prompting may expose contact or identity data.",
            remediation="Confirm necessity and approve masking or column removal before persistence.",
            columns=populated_identifier_columns,
        )

    forbidden_present = sorted(
        set(contract["feature_columns"]) & set(contract["forbidden_columns"]) & set(fields)
    )
    if forbidden_present:
        _finding(
            findings,
            code="forbidden_features",
            severity="critical",
            title="Forbidden or post-outcome fields are included as features",
            evidence=f"{len(forbidden_present)} declared feature columns violate the contract.",
            impact="Predictive validation may contain target leakage or information unavailable at decision time.",
            remediation="Remove the fields from the feature set and rebuild all validation results.",
            columns=forbidden_present,
        )

    if contract["intended_use"] == "unspecified":
        _finding(
            findings,
            code="intended_use_unspecified",
            severity="high",
            title="The intended analytical use is not declared",
            evidence="The data contract does not distinguish descriptive, predictive, or prescriptive use.",
            impact="A dataset acceptable for description may be unsafe for prediction or decision support.",
            remediation="Declare the question, target or estimand, decision time, and required grain.",
        )
    if contract["grain"] == "not_declared":
        _finding(
            findings,
            code="grain_unspecified",
            severity="high",
            title="The unit of analysis is not declared",
            evidence="No one-row-per-unit statement is available.",
            impact="Duplicates and aggregation validity cannot be interpreted confidently.",
            remediation="Declare the population, unit, key, and time window.",
        )

    severity_counts = {
        severity: sum(item["severity"] == severity for item in findings)
        for severity in ("critical", "high", "medium", "low")
    }
    if severity_counts["critical"]:
        status = "blocked"
        next_step = "Resolve critical grain, schema, key, or leakage failures before analysis."
    elif severity_counts["high"]:
        status = "needs_user_confirmation"
        next_step = "Review and approve a bounded remediation plan before analysis."
    elif severity_counts["medium"]:
        status = "ready_with_documented_limitations"
        next_step = "Proceed only with the declared limitations and route-specific checks."
    else:
        status = "ready"
        next_step = "Proceed to the analytical route defined in the data contract."

    return {
        "schema_version": "1.0",
        "generated_at": _utc_now(),
        "source": {
            "file_name": source_name,
            "sha256": source_sha256,
            "format": source_format,
        },
        "contract": contract,
        "dataset": {
            "rows": row_count,
            "columns": column_count,
            "column_names": fields,
            "total_cells": row_count * column_count,
            "missing_cells": total_missing,
            "missing_cell_rate": (
                total_missing / (row_count * column_count)
                if row_count and column_count
                else 0.0
            ),
            "exact_duplicate_rows": exact_duplicate_count,
            "normalized_duplicate_rows": normalized_duplicate_count,
            "trim_affected_cells": trim_affected,
            "explicit_missing_token_cells": missing_token_affected,
        },
        "primary_key": key_summary,
        "privacy": {
            "direct_identifier_columns_detected": populated_identifier_columns,
            "sensitive_columns_declared": [
                column for column in contract["sensitive_columns"] if column in fields
            ],
            "raw_values_in_report": False,
        },
        "columns": profiles,
        "findings": sorted(
            findings,
            key=lambda item: (-SEVERITY_ORDER[item["severity"]], item["id"]),
        ),
        "severity_counts": severity_counts,
        "quality_gate": {
            "status": status,
            "may_proceed_without_confirmation": status in {"ready", "ready_with_documented_limitations"},
            "quality_gate_only": True,
            "next_step": next_step,
        },
    }


def profile_dataset(path: Path, contract: dict[str, Any]) -> dict[str, Any]:
    rows, fields, metadata = read_dataset(path)
    return _profile_rows(
        rows,
        fields,
        source_name=path.name,
        source_sha256=sha256_file(path),
        source_format=metadata["format"],
        shape_warnings=metadata["shape_warnings"],
        contract=contract,
    )


def build_cleaning_plan(profile: dict[str, Any]) -> dict[str, Any]:
    """Create a dry-run plan; only reversible semantic normalization is automatic."""

    actions: list[dict[str, Any]] = []

    def add(
        action: str,
        *,
        mode: str,
        reason: str,
        affected: int | None,
        columns: Iterable[str] = (),
        executable: bool = True,
    ) -> None:
        actions.append(
            {
                "id": f"clean-{len(actions) + 1:03d}",
                "action": action,
                "mode": mode,
                "executable": executable,
                "columns": list(columns),
                "estimated_affected_rows_or_cells": affected,
                "reason": reason,
            }
        )

    dataset = profile["dataset"]
    if dataset["trim_affected_cells"]:
        add(
            "trim_whitespace",
            mode="safe_auto",
            reason="Remove surrounding whitespace without changing internal text.",
            affected=dataset["trim_affected_cells"],
        )
    if dataset["explicit_missing_token_cells"]:
        add(
            "normalize_missing_tokens",
            mode=(
                "safe_auto"
                if profile["contract"].get("missing_tokens_source") == "user_supplied"
                else "requires_confirmation"
            ),
            reason=(
                "Represent explicitly declared missing sentinels consistently as empty cells."
                if profile["contract"].get("missing_tokens_source") == "user_supplied"
                else "Confirm that inferred missing sentinels are not legitimate categories."
            ),
            affected=dataset["explicit_missing_token_cells"],
        )
    for column in profile["contract"]["numeric_columns"]:
        details = profile["columns"].get(column, {}).get("numeric")
        if details and details["invalid_count"] == 0:
            add(
                "canonicalize_numeric",
                mode="safe_auto",
                reason="Canonicalize a contract-declared numeric field after complete parsing.",
                affected=details["valid_count"],
                columns=[column],
            )
    for column in profile["contract"]["date_columns"]:
        details = profile["columns"].get(column, {}).get("datetime")
        if details and details["invalid_count"] == 0:
            add(
                "canonicalize_datetime",
                mode="safe_auto",
                reason="Canonicalize a contract-declared date after complete parsing.",
                affected=details["valid_count"],
                columns=[column],
            )
    if dataset["exact_duplicate_rows"]:
        add(
            "remove_exact_duplicates",
            mode="requires_confirmation",
            reason="Repeated rows may be legitimate events; removal changes denominators.",
            affected=dataset["exact_duplicate_rows"],
        )
    identifiers = profile["privacy"]["direct_identifier_columns_detected"]
    if identifiers:
        add(
            "drop_columns",
            mode="requires_confirmation",
            reason="Direct identifiers should not be persisted unless necessary and approved.",
            affected=sum(
                profile["columns"][column]["non_missing_count"] for column in identifiers
            ),
            columns=identifiers,
        )
    for finding in profile["findings"]:
        if finding["code"] in {
            "invalid_numeric",
            "invalid_datetime",
            "invalid_category",
            "required_missingness",
            "near_empty_column",
            "high_missingness",
            "numeric_outliers",
            "primary_key_duplicates",
        }:
            add(
                f"manual_review:{finding['code']}",
                mode="requires_confirmation",
                reason=finding["recommended_remediation"],
                affected=None,
                columns=finding["columns"],
                executable=False,
            )
    return {
        "schema_version": "1.0",
        "generated_at": _utc_now(),
        "source_sha256": profile["source"]["sha256"],
        "quality_gate_before_cleaning": profile["quality_gate"]["status"],
        "policy": {
            "safe_auto": "May run without changing substantive analytical meaning.",
            "requires_confirmation": "Must be explicitly approved by action id.",
            "non_executable": "Requires source correction or a case-specific written rule.",
            "raw_source_immutable": True,
        },
        "actions": actions,
    }


def _format_rate(value: float | None) -> str:
    return "—" if value is None else f"{value:.1%}"


def _markdown_text(value: Any) -> str:
    return (
        html.escape(_stringify(value), quote=False)
        .replace("|", r"\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _markdown_code(value: Any) -> str:
    escaped = (
        html.escape(_stringify(value), quote=False)
        .replace("|", "&#124;")
        .replace("\r", " ")
        .replace("\n", " ")
    )
    return f"<code>{escaped}</code>"


def render_quality_report(
    profile: dict[str, Any],
    plan: dict[str, Any],
    *,
    figure_path: str = "figures/data-quality-overview.svg",
) -> str:
    status = profile["quality_gate"]["status"]
    rows = profile["dataset"]["rows"]
    columns = profile["dataset"]["columns"]
    lines = [
        "# Data Readiness Report",
        "",
        "## Decision",
        "",
        f"**Quality gate: `{status}`.** {profile['quality_gate']['next_step']}",
        "",
        f"![Data quality gate, dataset shape, and issue severity]({figure_path})",
        "",
        "This report evaluates whether the uploaded dataset is trustworthy enough for "
        "the declared analytical use. It does not silently delete records, impute "
        "values, cap outliers, or redefine the grain.",
        "",
        "## Dataset and grain",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Source file | {_markdown_code(profile['source']['file_name'])} |",
        f"| Source SHA-256 | `{profile['source']['sha256']}` |",
        f"| Rows × columns | {rows:,} × {columns:,} |",
        f"| Profiled at | {_markdown_text(profile['generated_at'])} |",
        f"| Declared grain | {_markdown_text(profile['contract']['grain'])} |",
        f"| Intended use | {_markdown_text(profile['contract']['intended_use'])} |",
        f"| Primary key | {_markdown_text(', '.join(profile['primary_key']['columns']) or 'not available')} |",
        f"| Missing-cell rate | {_format_rate(profile['dataset']['missing_cell_rate'])} |",
        f"| Exact duplicate rows | {profile['dataset']['exact_duplicate_rows']:,} |",
        "",
        "## Findings",
        "",
    ]
    if not profile["findings"]:
        lines.append("No material quality finding was detected under the declared contract.")
    else:
        lines.extend(
            [
                "| Severity | Confidence | Finding | Evidence | Analytical risk | Required response |",
                "|---|---|---|---|---|---|",
            ]
        )
        for item in profile["findings"]:
            lines.append(
                f"| **{item['severity'].upper()}** | {_markdown_text(item['confidence'])} | "
                f"{_markdown_text(item['title'])} | {_markdown_text(item['evidence'])} | "
                f"{_markdown_text(item['impact'])} | "
                f"{_markdown_text(item['recommended_remediation'])} |"
            )
    lines.extend(
        [
            "",
            "## Proposed preprocessing",
            "",
            "| Action ID | Mode | Transformation | Scope | Estimated effect | Reason |",
            "|---|---|---|---|---:|---|",
        ]
    )
    if plan["actions"]:
        for item in plan["actions"]:
            scope = ", ".join(item["columns"]) or "dataset"
            affected = item["estimated_affected_rows_or_cells"]
            lines.append(
                f"| `{item['id']}` | {_markdown_text(item['mode'])} | "
                f"{_markdown_code(item['action'])} | {_markdown_text(scope)} | "
                f"{affected if affected is not None else 'manual review'} | "
                f"{_markdown_text(item['reason'])} |"
            )
    else:
        lines.append("| — | — | No preprocessing proposed | — | — | — |")
    lines.extend(
        [
            "",
            "> Safe automatic actions are limited to reversible semantic normalization. "
            "Any row deletion, column removal, imputation, outlier treatment, entity "
            "resolution, unit conversion, or target change requires an explicit action approval.",
            "",
            "<details>",
            "<summary><strong>Column-level profile</strong></summary>",
            "",
            "| Column | Inferred type | Missing | Distinct | Largest share |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for column, item in profile["columns"].items():
        lines.append(
            f"| {_markdown_code(column)} | {_markdown_text(item['inferred_type'])} | "
            f"{item['missing_count']:,} ({item['missing_rate']:.1%}) | "
            f"{item['distinct_count']:,} | "
            f"{_format_rate(item.get('largest_category_share'))} |"
        )
    lines.extend(
        [
            "",
            "</details>",
            "",
            "## Reproducibility",
            "",
            "- Machine-readable profile: `data-quality-report.json`",
            "- Cleaning plan: `cleaning-plan.json`",
            "- Data contract: `data-contract.json`",
            "- Raw values from identifier-like columns are not reproduced in this report.",
            "",
        ]
    )
    return "\n".join(lines)


def render_quality_svg(profile: dict[str, Any]) -> str:
    status = profile["quality_gate"]["status"]
    colors = {
        "ready": TEAL,
        "ready_with_documented_limitations": BLUE,
        "needs_user_confirmation": VIOLET,
        "blocked": CORAL,
    }
    accent = colors[status]
    counts = profile["severity_counts"]
    dataset = profile["dataset"]
    body = [
        rounded_rect(42, 146, 350, 150, fill=PAPER, stroke=GRID),
        text(66, 174, "QUALITY GATE", css="eyebrow"),
        text(66, 216, status.replace("_", " ").upper(), css="value", fill=accent),
        wrapped_text(
            66,
            246,
            profile["quality_gate"]["next_step"],
            chars=43,
            line_height=18,
            css="small",
        ),
        rounded_rect(414, 146, 704, 150, fill=PAPER, stroke=GRID),
        text(438, 174, "DATASET SHAPE", css="eyebrow"),
        text(438, 219, f"{dataset['rows']:,}", css="big"),
        text(438, 245, "rows", css="small"),
        text(640, 219, f"{dataset['columns']:,}", css="big"),
        text(640, 245, "columns", css="small"),
        text(842, 219, f"{dataset['missing_cell_rate']:.1%}", css="big"),
        text(842, 245, "missing cells", css="small"),
        text(1022, 219, f"{dataset['exact_duplicate_rows']:,}", css="big"),
        text(1022, 245, "exact duplicates", css="small"),
        text(42, 334, "ISSUE SEVERITY", css="section"),
    ]
    severity_colors = {
        "critical": CORAL,
        "high": VIOLET,
        "medium": BLUE,
        "low": MUTED,
    }
    labels = ["critical", "high", "medium", "low"]
    for index, label in enumerate(labels):
        x = 42 + index * 272
        body.extend(
            [
                rounded_rect(x, 360, 248, 118, fill=PAPER, stroke=GRID),
                text(x + 22, 389, label.upper(), css="eyebrow", fill=severity_colors[label]),
                text(x + 22, 437, str(counts[label]), css="display", fill=INK),
                text(x + 92, 437, "findings", css="small"),
            ]
        )
    return svg_document(
        "Data readiness before analysis",
        "The gate separates safe normalization, user decisions, and blocking evidence failures",
        "\n".join(body),
        height=548,
        description=(
            f"Data quality status is {status}. The dataset contains {dataset['rows']} rows "
            f"and {dataset['columns']} columns, with {counts['critical']} critical, "
            f"{counts['high']} high, {counts['medium']} medium, and {counts['low']} low findings."
        ),
        accent=accent,
        kicker="DATA READINESS",
        source=f"Source: {profile['source']['file_name']} · SHA-256 recorded in report",
        note="No raw identifier values displayed",
    )


def write_quality_bundle(
    source: Path,
    output_dir: Path,
    *,
    contract: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = output_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    profile = profile_dataset(source, contract)
    plan = build_cleaning_plan(profile)
    (output_dir / "data-quality-report.json").write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "cleaning-plan.json").write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "data-contract.json").write_text(
        json.dumps(contract, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "data-quality-report.md").write_text(
        render_quality_report(profile, plan),
        encoding="utf-8",
    )
    (figures / "data-quality-overview.svg").write_text(
        render_quality_svg(profile),
        encoding="utf-8",
    )
    return profile, plan


def _canonical_number(value: str) -> str:
    number = _parse_decimal(value)
    if number is None:
        return value
    normalized = format(number, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    if normalized in {"-0", "+0", ""}:
        return "0"
    return normalized


def _canonical_date(value: str) -> str:
    normalized = value.strip()
    if re.fullmatch(r"\d{4}(?:-\d{2})?(?:-\d{2})?", normalized):
        return normalized
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return value
    return parsed.isoformat()


def apply_cleaning_plan(
    source: Path,
    report: dict[str, Any],
    plan: dict[str, Any],
    output_dir: Path,
    *,
    approvals: Iterable[str] = (),
) -> dict[str, Any]:
    """Apply safe actions plus explicitly approved executable actions to a copy."""

    actual_hash = sha256_file(source)
    if report["source"]["sha256"] != actual_hash or plan["source_sha256"] != actual_hash:
        raise ValueError("Source SHA-256 no longer matches the reviewed data-quality bundle.")
    expected_actions = build_cleaning_plan(report)["actions"]
    if plan.get("actions") != expected_actions:
        raise ValueError(
            "Cleaning plan actions no longer match the reviewed quality report; "
            "regenerate the bundle before applying transformations."
        )
    approval_set = set(approvals)
    known_ids = {item["id"] for item in plan["actions"]}
    unknown = sorted(approval_set - known_ids)
    if unknown:
        raise ValueError("Unknown cleaning action ids: " + ", ".join(unknown))
    non_executable_approved = sorted(
        item["id"]
        for item in plan["actions"]
        if item["id"] in approval_set and not item["executable"]
    )
    if non_executable_approved:
        raise ValueError(
            "These actions require a case-specific source correction and cannot be "
            "executed generically: " + ", ".join(non_executable_approved)
        )
    unnecessary_approvals = sorted(
        item["id"]
        for item in plan["actions"]
        if item["id"] in approval_set and item["mode"] != "requires_confirmation"
    )
    if unnecessary_approvals:
        raise ValueError(
            "Only requires_confirmation actions may be approved explicitly: "
            + ", ".join(unnecessary_approvals)
        )

    rows, fields, _ = read_dataset(source)
    before_rows = len(rows)
    before_columns = len(fields)
    contract = report["contract"]
    tokens = _missing_tokens(contract)
    selected = [
        item
        for item in plan["actions"]
        if item["executable"]
        and (item["mode"] == "safe_auto" or item["id"] in approval_set)
    ]
    log_entries: list[dict[str, Any]] = []

    for item in selected:
        action = item["action"]
        changed = 0
        if action == "trim_whitespace":
            for row in rows:
                for field in fields:
                    value = row.get(field, "")
                    normalized = value.strip()
                    if normalized != value:
                        row[field] = normalized
                        changed += 1
        elif action == "normalize_missing_tokens":
            for row in rows:
                for field in fields:
                    value = row.get(field, "")
                    if value and is_missing(value, tokens):
                        row[field] = ""
                        changed += 1
        elif action == "canonicalize_numeric":
            for column in item["columns"]:
                for row in rows:
                    value = row.get(column, "")
                    if value and not is_missing(value, tokens):
                        normalized = _canonical_number(value)
                        if normalized != value:
                            row[column] = normalized
                            changed += 1
        elif action == "canonicalize_datetime":
            for column in item["columns"]:
                for row in rows:
                    value = row.get(column, "")
                    if value and not is_missing(value, tokens):
                        normalized = _canonical_date(value)
                        if normalized != value:
                            row[column] = normalized
                            changed += 1
        elif action == "remove_exact_duplicates":
            seen: set[tuple[str, ...]] = set()
            retained: list[dict[str, str]] = []
            for row in rows:
                key = tuple(row.get(field, "") for field in fields)
                if key in seen:
                    changed += 1
                    continue
                seen.add(key)
                retained.append(row)
            rows = retained
        elif action == "drop_columns":
            drop = set(item["columns"])
            fields = [field for field in fields if field not in drop]
            for row in rows:
                for field in drop:
                    if field in row:
                        row.pop(field)
                        changed += 1
        else:
            raise ValueError(f"Unsupported executable cleaning action: {action}")
        log_entries.append(
            {
                "action_id": item["id"],
                "action": action,
                "mode": item["mode"],
                "explicitly_approved": item["id"] in approval_set,
                "changed_rows_or_cells": changed,
                "columns": item["columns"],
            }
        )

    processed_dir = output_dir / "processed"
    processed = processed_dir / "analysis.csv"
    if processed.resolve() == source.resolve():
        raise ValueError(
            "The processed output resolves to the raw source path; choose a different output directory."
        )
    processed_dir.mkdir(parents=True, exist_ok=True)
    with processed.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)

    post_dir = output_dir / "post-cleaning"
    post_profile, _ = write_quality_bundle(processed, post_dir, contract=contract)
    transformation_log = {
        "schema_version": "1.0",
        "generated_at": _utc_now(),
        "raw_source": {
            "file_name": source.name,
            "sha256": actual_hash,
            "modified": False,
        },
        "processed_output": {
            "path": "processed/analysis.csv",
            "sha256": sha256_file(processed),
        },
        "before": {"rows": before_rows, "columns": before_columns},
        "after": {"rows": len(rows), "columns": len(fields)},
        "quality_gate_before": report["quality_gate"]["status"],
        "quality_gate_after": post_profile["quality_gate"]["status"],
        "applied_actions": log_entries,
        "skipped_confirmation_actions": [
            item["id"]
            for item in plan["actions"]
            if item["mode"] == "requires_confirmation" and item["id"] not in approval_set
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "transformation-log.json").write_text(
        json.dumps(transformation_log, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return transformation_log
