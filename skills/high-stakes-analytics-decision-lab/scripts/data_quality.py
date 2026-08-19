#!/usr/bin/env python3
"""Data-readiness profiling and controlled preprocessing for uploaded case data."""

from __future__ import annotations

import csv
import hashlib
import html
import ipaddress
import itertools
import json
import math
import re
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, overload

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
SSN_RE = re.compile(r"^(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}$")
SSN_COMPACT_RE = re.compile(
    r"^(?!000|666|9\d\d)\d{3}(?!00)\d{2}(?!0000)\d{4}$"
)
PHONE_RE = re.compile(r"^\+?[0-9][0-9() .-]{5,20}[0-9]$")
CHINESE_ID_RE = re.compile(r"^\d{6}(?:19|20)\d{6}\d{3}[0-9Xx]$")
ADDRESS_RE = re.compile(
    r"(?:^|\s)\d{1,6}\s+[\w.'-]+(?:\s+[\w.'-]+){0,5}\s+"
    r"(?:street|st|road|rd|avenue|ave|boulevard|blvd|lane|ln|drive|dr|way)\b"
    r"|(?:路|街|道|巷).{0,20}号",
    re.I,
)
HEALTH_VALUE_RE = re.compile(
    r"\b(?:allerg(?:y|ies)|asthma|blood pressure|cancer|chronic|clinical condition|"
    r"diabetes|diagnosis|disability|heart failure|hiv|hypertension|insulin|"
    r"medication|mental health|mortality|pregnan(?:cy|t)|prescription|surgery|"
    r"symptom|treatment)\b|(?:过敏|哮喘|血压|癌症|慢性病|糖尿病|诊断|残疾|"
    r"心衰|艾滋|高血压|胰岛素|用药|心理健康|死亡|妊娠|处方|手术|症状|治疗)",
    re.I,
)
DATE_NAME_RE = re.compile(r"(^|_)(date|time|timestamp|datetime|year|month|day)($|_)", re.I)
DIRECT_IDENTIFIER_NAME_RE = re.compile(
    r"(^|_)(address|contact|driver_license|email|"
    r"e_mail|full_name|identity|identity_token|medical_record|mobile|name|"
    r"national_id|passport|patient_id|phone|postal_address|ssn|street_address|"
    r"telephone|ip_address)($|_)",
    re.I,
)
SENSITIVE_NAME_RE = re.compile(
    r"(^|_)(birth|birth_date|blood_pressure|bmi|clinical|condition|date_of_birth|"
    r"diagnosis|disability|disease|dob|ethnicity|gender|genetic|glucose|hba1c|"
    r"health|heart_rate|income|insurance|medical|medication|mortality|patient|"
    r"pregnancy|prescription|procedure|race|religion|sex|sexual_orientation|"
    r"symptom|treatment|vital)($|_)",
    re.I,
)
QUASI_IDENTIFIER_NAME_RE = re.compile(
    r"(^|_)(age|city|county|geography|location|occupation|postal_code|postcode|"
    r"state|tract|zip|zip_code)($|_)",
    re.I,
)
MAX_INPUT_FILE_BYTES = 128 * 1024 * 1024
MAX_IN_MEMORY_JSON_BYTES = 16 * 1024 * 1024
MAX_DATASET_ROWS = 500_000
MAX_DATASET_COLUMNS = 256
MAX_CELL_CHARACTERS = 65_536
MAX_JSON_DEPTH = 24
SMALL_SAMPLE_PRIVACY_ROWS = 50
ALLOWED_INTENDED_USES = {
    "descriptive",
    "diagnostic",
    "predictive",
    "prescriptive",
    "mixed",
    "unspecified",
}


class ReiterableRows(Sequence[dict[str, str]]):
    """A bounded, re-openable row source for streaming tabular inputs."""

    def __init__(
        self,
        row_count: int,
        iterator_factory: Callable[[], Iterator[dict[str, str]]],
    ) -> None:
        self._row_count = row_count
        self._iterator_factory = iterator_factory

    def __len__(self) -> int:
        return self._row_count

    def __iter__(self) -> Iterator[dict[str, str]]:
        return self._iterator_factory()

    @overload
    def __getitem__(self, index: int) -> dict[str, str]: ...

    @overload
    def __getitem__(self, index: slice) -> list[dict[str, str]]: ...

    def __getitem__(self, index: int | slice) -> dict[str, str] | list[dict[str, str]]:
        if isinstance(index, slice):
            start, stop, step = index.indices(self._row_count)
            if step != 1:
                return list(self)[index]
            return list(itertools.islice(self, start, stop))
        normalized = index + self._row_count if index < 0 else index
        if normalized < 0 or normalized >= self._row_count:
            raise IndexError(index)
        try:
            return next(itertools.islice(self, normalized, normalized + 1))
        except StopIteration as error:
            raise IndexError(index) from error


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


def _validate_input_path(path: Path) -> int:
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    if size > MAX_INPUT_FILE_BYTES:
        raise ValueError(
            f"Input file is {size} bytes; limit is {MAX_INPUT_FILE_BYTES}. "
            "Create a traceable bounded extract or use a database-backed workflow."
        )
    return size


def _validate_cell(value: Any, *, location: str) -> str:
    rendered = _stringify(value)
    if len(rendered) > MAX_CELL_CHARACTERS:
        raise ValueError(
            f"Cell at {location} contains {len(rendered)} characters; "
            f"limit is {MAX_CELL_CHARACTERS}."
        )
    return rendered


def _json_depth(value: Any) -> int:
    maximum = 1
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        maximum = max(maximum, depth)
        if maximum > MAX_JSON_DEPTH:
            return maximum
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
    return maximum


def _validate_json_depth(value: Any, *, location: str) -> None:
    depth = _json_depth(value)
    if depth > MAX_JSON_DEPTH:
        raise ValueError(
            f"JSON at {location} has nesting depth {depth}; limit is {MAX_JSON_DEPTH}."
        )


def _normalized_fields(
    raw_fields: list[str],
    maximum_width: int,
) -> tuple[list[str], list[str]]:
    if maximum_width > MAX_DATASET_COLUMNS:
        raise ValueError(
            f"Dataset has {maximum_width} columns; limit is {MAX_DATASET_COLUMNS}."
        )
    shape_warnings: list[str] = []
    fields: list[str] = []
    used_fields: set[str] = set()
    for index, raw_field in enumerate(raw_fields, 1):
        base = _validate_cell(raw_field, location=f"header column {index}").strip()
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
    return fields, shape_warnings


def _csv_parameters(path: Path, suffix: str) -> dict[str, Any]:
    if suffix == ".tsv":
        return {"dialect": csv.excel_tab}
    with path.open(encoding="utf-8-sig") as sample_handle:
        sample = sample_handle.read(8192)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    return {"dialect": dialect}


def _read_csv_rows(
    path: Path,
    parameters: dict[str, Any],
    fields: list[str],
) -> Iterator[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle, **parameters)
        next(reader, None)
        for row_number, record in enumerate(reader, 2):
            yield {
                field: (
                    _validate_cell(record[index], location=f"row {row_number}, column {index + 1}")
                    if index < len(record)
                    else ""
                )
                for index, field in enumerate(fields)
            }


def _scan_csv(
    path: Path,
    suffix: str,
) -> tuple[ReiterableRows, list[str], list[str]]:
    parameters = _csv_parameters(path, suffix)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle, **parameters)
        try:
            raw_fields = next(reader)
        except StopIteration:
            empty = ReiterableRows(0, lambda: iter(()))
            return empty, [], ["missing_header"]
        maximum_width = len(raw_fields)
        row_count = 0
        ragged = False
        for row_number, record in enumerate(reader, 2):
            row_count += 1
            if row_count > MAX_DATASET_ROWS:
                raise ValueError(
                    f"Dataset exceeds {MAX_DATASET_ROWS} rows at source row {row_number}."
                )
            maximum_width = max(maximum_width, len(record))
            if maximum_width > MAX_DATASET_COLUMNS:
                raise ValueError(
                    f"Dataset exceeds {MAX_DATASET_COLUMNS} columns at source row {row_number}."
                )
            ragged = ragged or len(record) != len(raw_fields)
            for column_index, value in enumerate(record, 1):
                _validate_cell(value, location=f"row {row_number}, column {column_index}")
    fields, shape_warnings = _normalized_fields(raw_fields, maximum_width)
    if ragged:
        shape_warnings.append("ragged_rows")
    rows = ReiterableRows(
        row_count,
        lambda: _read_csv_rows(path, parameters, fields),
    )
    return rows, fields, sorted(set(shape_warnings))


def _iter_jsonl(path: Path, fields: list[str]) -> Iterator[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            if len(line) > MAX_CELL_CHARACTERS * MAX_DATASET_COLUMNS:
                raise ValueError(f"JSONL line {line_number} exceeds the bounded line limit.")
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"JSONL line {line_number} is not an object.")
            _validate_json_depth(record, location=f"line {line_number}")
            yield {
                field: _validate_cell(
                    record.get(field),
                    location=f"line {line_number}, field {field}",
                )
                for field in fields
            }


def _scan_jsonl(path: Path) -> tuple[ReiterableRows, list[str], list[str]]:
    fields: list[str] = []
    seen: set[str] = set()
    shapes: set[frozenset[str]] = set()
    row_count = 0
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row_count += 1
            if row_count > MAX_DATASET_ROWS:
                raise ValueError(
                    f"Dataset exceeds {MAX_DATASET_ROWS} rows at JSONL line {line_number}."
                )
            if len(line) > MAX_CELL_CHARACTERS * MAX_DATASET_COLUMNS:
                raise ValueError(f"JSONL line {line_number} exceeds the bounded line limit.")
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"JSONL line {line_number} is not an object.")
            _validate_json_depth(record, location=f"line {line_number}")
            names = [str(field) for field in record]
            shapes.add(frozenset(names))
            for field in names:
                _validate_cell(field, location=f"line {line_number} field name")
                if field not in seen:
                    seen.add(field)
                    fields.append(field)
                    if len(fields) > MAX_DATASET_COLUMNS:
                        raise ValueError(
                            f"Dataset exceeds {MAX_DATASET_COLUMNS} distinct columns."
                        )
            for field, value in record.items():
                _validate_cell(value, location=f"line {line_number}, field {field}")
    warnings = ["mixed_object_shape"] if len(shapes) > 1 else []
    return ReiterableRows(row_count, lambda: _iter_jsonl(path, fields)), fields, warnings


def read_dataset(
    path: Path,
) -> tuple[Sequence[dict[str, str]], list[str], dict[str, Any]]:
    """Read bounded tabular inputs; stream row-oriented formats on every pass."""

    file_bytes = _validate_input_path(path)
    suffix = path.suffix.casefold()
    if suffix in {".csv", ".tsv"}:
        csv_rows, csv_fields, csv_warnings = _scan_csv(path, suffix)
        return csv_rows, csv_fields, {
            "format": suffix.lstrip("."),
            "shape_warnings": csv_warnings,
            "file_bytes": file_bytes,
            "streaming_input": True,
        }
    if suffix in {".jsonl", ".ndjson"}:
        jsonl_rows, jsonl_fields, jsonl_warnings = _scan_jsonl(path)
        return jsonl_rows, jsonl_fields, {
            "format": suffix.lstrip("."),
            "shape_warnings": jsonl_warnings,
            "file_bytes": file_bytes,
            "streaming_input": True,
        }
    if suffix != ".json":
        raise ValueError("Supported input formats are CSV, TSV, JSON, JSONL, and NDJSON.")
    if file_bytes > MAX_IN_MEMORY_JSON_BYTES:
        raise ValueError(
            f"JSON array input exceeds {MAX_IN_MEMORY_JSON_BYTES} bytes. "
            "Convert it to JSONL for bounded streaming analysis."
        )
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    _validate_json_depth(payload, location="document")
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        payload = payload["rows"]
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise ValueError("JSON input must be an array of objects or an object with a rows array.")
    if len(payload) > MAX_DATASET_ROWS:
        raise ValueError(f"Dataset has {len(payload)} rows; limit is {MAX_DATASET_ROWS}.")
    json_fields: list[str] = []
    seen: set[str] = set()
    for row_number, row in enumerate(payload, 1):
        for raw_field, value in row.items():
            field = _validate_cell(raw_field, location=f"row {row_number} field name")
            if field not in seen:
                seen.add(field)
                json_fields.append(field)
                if len(json_fields) > MAX_DATASET_COLUMNS:
                    raise ValueError(
                        f"Dataset exceeds {MAX_DATASET_COLUMNS} distinct columns."
                    )
            _validate_cell(value, location=f"row {row_number}, field {field}")
    json_rows = [
        {
            field: _validate_cell(
                row.get(field),
                location=f"row {row_number}, field {field}",
            )
            for field in json_fields
        }
        for row_number, row in enumerate(payload, 1)
    ]
    shapes = {frozenset(map(str, row.keys())) for row in payload}
    return json_rows, json_fields, {
        "format": "json",
        "shape_warnings": ["mixed_object_shape"] if len(shapes) > 1 else [],
        "file_bytes": file_bytes,
        "streaming_input": False,
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


def _looks_like_phone(value: str) -> bool:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    if not PHONE_RE.fullmatch(value):
        return False
    digits = re.sub(r"\D", "", value)
    return 7 <= len(digits) <= 15 and (
        not value.isdigit() or len(digits) in {10, 11}
    )


def _looks_like_ip_address(value: str) -> bool:
    if "." not in value and ":" not in value:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def _direct_identifier_value_signals(value: str) -> set[str]:
    signals: set[str] = set()
    if EMAIL_RE.fullmatch(value):
        signals.add("email")
    if SSN_RE.fullmatch(value) or SSN_COMPACT_RE.fullmatch(value):
        signals.add("ssn")
    if CHINESE_ID_RE.fullmatch(value):
        signals.add("national_id")
    if _looks_like_phone(value):
        signals.add("phone")
    if _looks_like_ip_address(value):
        signals.add("ip_address")
    if ADDRESS_RE.search(value):
        signals.add("postal_address")
    return signals


def _sensitive_value_signals(value: str) -> set[str]:
    signals: set[str] = set()
    if HEALTH_VALUE_RE.search(value):
        signals.add("health_information")
    return signals


def _looks_like_birth_date(value: str, *, now: datetime) -> bool:
    """Flag common full-date formats that can encode an adult birth date."""

    normalized = value.strip()
    parsed = None
    for pattern in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%Y%m%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y年%m月%d日",
    ):
        try:
            parsed = datetime.strptime(normalized, pattern)
            break
        except ValueError:
            pass
    if parsed is None:
        return False
    years_old = (now.date() - parsed.date()).days / 365.2425
    return 13 <= years_old <= 120


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


def _row_digest(values: Iterable[str]) -> bytes:
    """Hash length-framed values so duplicate tracking stays memory bounded."""

    digest = hashlib.sha256()
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.digest()


def _suppress_privacy_bearing_statistics(profile: dict[str, Any]) -> None:
    """Remove extrema and quantiles that can reproduce sensitive cell values."""

    suppressed: list[str] = []
    for section_name, statistic_names in (
        ("numeric", ("minimum", "q1", "median", "q3", "maximum")),
        ("datetime", ("minimum", "maximum")),
    ):
        section = profile.get(section_name)
        if not isinstance(section, dict):
            continue
        for statistic_name in statistic_names:
            if statistic_name in section:
                del section[statistic_name]
                suppressed.append(f"{section_name}.{statistic_name}")
    if suppressed:
        profile["privacy_suppressed_statistics"] = suppressed


def _profile_rows(
    rows: Sequence[dict[str, str]],
    fields: list[str],
    *,
    source_name: str,
    source_sha256: str,
    source_format: str,
    source_file_bytes: int,
    streaming_input: bool,
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
    direct_identifier_columns: set[str] = set()
    sensitive_columns_detected: set[str] = set()
    privacy_signal_counts: dict[str, dict[str, dict[str, int]]] = {}
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

        direct_signals: Counter[str] = Counter()
        sensitive_signals: Counter[str] = Counter()
        for value in observed:
            direct_signals.update(_direct_identifier_value_signals(value))
            sensitive_signals.update(_sensitive_value_signals(value))
        identifier_declared = field in contract["direct_identifier_columns"]
        sensitive_declared = field in contract["sensitive_columns"]
        normalized_name = _normalized_column_name(field)
        identifier_named = DIRECT_IDENTIFIER_NAME_RE.search(normalized_name) is not None
        sensitive_named = SENSITIVE_NAME_RE.search(normalized_name) is not None
        quasi_identifier_named = (
            QUASI_IDENTIFIER_NAME_RE.search(normalized_name) is not None
        )
        birth_date_count = sum(
            _looks_like_birth_date(value, now=now) for value in observed
        )
        if observed and birth_date_count / len(observed) >= 0.8:
            sensitive_signals["possible_birth_date"] = birth_date_count
        if identifier_declared:
            direct_signals["contract_declared"] = len(observed)
        if identifier_named and observed:
            direct_signals["identifier_column_name"] = len(observed)
        if sensitive_declared:
            sensitive_signals["contract_declared"] = len(observed)
        if sensitive_named and observed:
            sensitive_signals["sensitive_column_name"] = len(observed)
        if quasi_identifier_named and observed:
            sensitive_signals["quasi_identifier_column_name"] = len(observed)
        if direct_signals:
            direct_identifier_columns.add(field)
            profile["direct_identifier_signal_count"] = max(direct_signals.values())
        if sensitive_signals:
            sensitive_columns_detected.add(field)
            profile["sensitive_signal_count"] = max(sensitive_signals.values())
        if direct_signals or sensitive_signals:
            _suppress_privacy_bearing_statistics(profile)
        if direct_signals or sensitive_signals:
            privacy_signal_counts[field] = {
                "direct_identifier": dict(sorted(direct_signals.items())),
                "sensitive_or_quasi_identifier": dict(
                    sorted(sensitive_signals.items())
                ),
            }
        profiles[field] = profile

    exact_seen: set[bytes] = set()
    normalized_seen: set[bytes] = set()
    exact_duplicate_count = 0
    normalized_duplicate_count = 0
    for row in rows:
        exact = _row_digest(row.get(field, "") for field in fields)
        normalized = _row_digest(
            "" if is_missing(row.get(field, ""), tokens) else row.get(field, "").strip().casefold()
            for field in fields
        )
        exact_duplicate_count += int(exact in exact_seen)
        normalized_duplicate_count += int(normalized in normalized_seen)
        exact_seen.add(exact)
        normalized_seen.add(normalized)
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
            candidate_values = (row.get(candidate, "").strip() for row in rows)
            if row_count and all(
                not is_missing(value, tokens) for value in candidate_values
            ):
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
            missing_keys = 0
            duplicate_keys = 0
            complete_seen: set[bytes] = set()
            for row in rows:
                key = tuple(row.get(column, "").strip() for column in primary_key)
                if any(is_missing(value, tokens) for value in key):
                    missing_keys += 1
                    continue
                key_digest = _row_digest(key)
                duplicate_keys += int(key_digest in complete_seen)
                complete_seen.add(key_digest)
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

    identifier_columns = sorted(
        direct_identifier_columns | set(contract["direct_identifier_columns"])
    )
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

    populated_sensitive_columns = sorted(
        field
        for field in sensitive_columns_detected | set(contract["sensitive_columns"])
        if field in fields and profiles[field]["non_missing_count"] > 0
    )
    if populated_sensitive_columns:
        _finding(
            findings,
            code="sensitive_fields_present",
            severity="high",
            title="Sensitive or quasi-identifying fields are present",
            evidence=(
                f"{len(populated_sensitive_columns)} columns contain declared, named, "
                "or value-level sensitive-data signals; raw values are not reproduced."
            ),
            impact=(
                "Health, demographic, financial, or birth-related fields may enable "
                "harmful inference or re-identification when combined."
            ),
            remediation=(
                "Confirm necessity, purpose, access controls, aggregation, and retention "
                "before persistence or downstream prompting."
            ),
            columns=populated_sensitive_columns,
        )
    privacy_columns = sorted(
        set(populated_identifier_columns) | set(populated_sensitive_columns)
    )
    if privacy_columns and row_count < SMALL_SAMPLE_PRIVACY_ROWS:
        _finding(
            findings,
            code="small_sample_reidentification_risk",
            severity="high",
            title="Sensitive data appear in a small sample",
            evidence=(
                f"The dataset has {row_count} rows and {len(privacy_columns)} "
                "identifier or sensitive columns."
            ),
            impact=(
                "Rare combinations and small cells may identify people even after direct "
                "identifiers are removed."
            ),
            remediation=(
                "Require privacy review, minimum-cell rules, aggregation, and a documented "
                "release boundary before analysis or sharing."
            ),
            columns=privacy_columns,
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
            "file_bytes": source_file_bytes,
            "streaming_input": streaming_input,
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
            "sensitive_columns_detected": populated_sensitive_columns,
            "sensitive_columns_declared": sorted(
                column for column in contract["sensitive_columns"] if column in fields
            ),
            "small_sample_threshold_rows": SMALL_SAMPLE_PRIVACY_ROWS,
            "signal_counts_by_column": privacy_signal_counts,
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
    _validate_input_path(path)
    source_sha256 = sha256_file(path)
    rows, fields, metadata = read_dataset(path)
    profile = _profile_rows(
        rows,
        fields,
        source_name=path.name,
        source_sha256=source_sha256,
        source_format=metadata["format"],
        source_file_bytes=metadata["file_bytes"],
        streaming_input=metadata["streaming_input"],
        shape_warnings=metadata["shape_warnings"],
        contract=contract,
    )
    if sha256_file(path) != source_sha256:
        raise ValueError("Input file changed while it was being profiled; rerun the gate.")
    return profile


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
            "sensitive_fields_present",
            "small_sample_reidentification_risk",
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

    row_source, fields, _ = read_dataset(source)
    rows = [dict(row) for row in row_source]
    if sha256_file(source) != actual_hash:
        raise ValueError("Input file changed while the cleaning copy was being prepared.")
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
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
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
