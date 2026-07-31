#!/usr/bin/env python3
"""Real-data project runtime for High-Stakes Analytics & Decision Lab.

The module intentionally uses only Python's standard library. Project entry
points are thin wrappers around the functions here so CI can run fully offline
against the committed, hash-locked source snapshots.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import shutil
import statistics
import tempfile
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable, Iterable


PALETTE = {
    "ink": "#0B1324",
    "ink_soft": "#263449",
    "muted": "#617084",
    "quiet": "#8B98A9",
    "grid": "#D9E2EC",
    "grid_dark": "#B9C6D5",
    "canvas": "#F3F6FA",
    "navy": "#0B1F3A",
    "navy_2": "#13345B",
    "blue": "#246BFD",
    "blue_dark": "#174EA6",
    "blue_light": "#E8F0FF",
    "teal": "#008C82",
    "teal_light": "#DDF5F2",
    "gold": "#C69214",
    "gold_light": "#FFF2C7",
    "orange": "#D85B43",
    "orange_light": "#FCE7E2",
    "pink": "#B9487C",
    "pink_light": "#F9E6EF",
    "olive": "#4E7D32",
    "olive_light": "#E8F2DF",
    "violet": "#7257D9",
    "violet_light": "#EEEAFE",
    "paper": "#FFFFFF",
}
PROJECTS_WITH_CASES = {
    "population-health-survival",
    "behavioral-reading-experiment",
    "bike-demand-operations",
    "treasury-risk-engineering",
    "regime-aware-multi-asset-portfolio",
    "commercial-real-estate-risk",
    "spatial-equity-planning",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_raw_files(project_root: Path) -> list[dict[str, Any]]:
    manifest = load_json(project_root / "source-manifest.json")
    records = []
    for item in manifest["raw_files"]:
        path = project_root / item["path"]
        if not path.exists():
            raise FileNotFoundError(f"Missing source snapshot: {path}")
        observed = sha256(path)
        if observed != item["sha256"]:
            raise ValueError(
                f"Source version/hash changed for {path.name}: "
                f"expected {item['sha256']}, observed {observed}"
            )
        records.append(
            {
                "path": item["path"],
                "sha256": observed,
                "bytes": path.stat().st_size,
            }
        )
    return records


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "High-Stakes-Analytics-Decision-Lab/7.0 "
                "research portfolio contact: github.com/limingrui679-design"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        with destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)


def _refresh_generic(project_root: Path, manifest: dict[str, Any]) -> None:
    raw_item = manifest["raw_files"][0]
    target = project_root / raw_item["path"]
    with tempfile.TemporaryDirectory(prefix="hsdl-download-") as directory:
        temporary = Path(directory) / target.name
        _download(manifest["download_url"], temporary)
        observed = sha256(temporary)
        if observed != raw_item["sha256"]:
            raise ValueError(
                "Downloaded source differs from the reviewed version. "
                f"Expected {raw_item['sha256']}; observed {observed}. "
                "Review the new version before updating the manifest."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary.replace(target)


def _refresh_treasury(project_root: Path, manifest: dict[str, Any]) -> None:
    expected = {Path(item["path"]).name: item for item in manifest["raw_files"]}
    with tempfile.TemporaryDirectory(prefix="hsdl-treasury-") as directory:
        temporary_root = Path(directory)
        for year in range(2020, 2026):
            name = f"treasury-{year}.csv"
            target = temporary_root / name
            _download(manifest["download_url_template"].format(year=year), target)
            observed = sha256(target)
            if observed != expected[name]["sha256"]:
                raise ValueError(
                    f"Treasury source version changed for {year}: "
                    f"expected {expected[name]['sha256']}, observed {observed}."
                )
        for name in expected:
            shutil.copy2(temporary_root / name, project_root / "data" / "raw" / name)


def _stream_filter_census(url: str, target: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "High-Stakes-Analytics-Decision-Lab/7.0 research portfolio"
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        text_stream = io.TextIOWrapper(response, encoding="utf-8")
        with target.open("w", encoding="utf-8", newline="") as handle:
            for index, line in enumerate(text_stream):
                if index == 0 or line.startswith("1400000US25"):
                    handle.write(line)


def _refresh_spatial(project_root: Path, manifest: dict[str, Any]) -> None:
    expected = {Path(item["path"]).name: item for item in manifest["raw_files"]}
    tables = ("b01003", "b17001", "b19013", "b08301", "b25064")
    with tempfile.TemporaryDirectory(prefix="hsdl-census-") as directory:
        temporary_root = Path(directory)
        for table in tables:
            name = f"acs-{table}-ma.dat"
            _stream_filter_census(
                manifest["download_url_template"].format(table=table),
                temporary_root / name,
            )
        _download(
            manifest["geography_url"],
            temporary_root / "2023_Gaz_tracts_national.zip",
        )
        for name, item in expected.items():
            observed = sha256(temporary_root / name)
            if observed != item["sha256"]:
                raise ValueError(
                    f"Census source version changed for {name}: "
                    f"expected {item['sha256']}, observed {observed}."
                )
        for name in expected:
            shutil.copy2(temporary_root / name, project_root / "data" / "raw" / name)


CFPB_SAFE_FIELDS = [
    "complaint_id",
    "date_received",
    "date_sent_to_company",
    "sub_product",
    "issue",
    "sub_issue",
    "state",
    "submitted_via",
    "company_response",
    "timely",
]


def _privacy_minimize_cfpb(source: Path, target: Path) -> int:
    """Create the reviewed CFPB field subset before repository storage."""
    source_rows = read_csv(source)
    rows = []
    for row in source_rows:
        received = row["Date received"]
        if not ("2022-01-01" <= received[:10] < "2023-01-01"):
            continue
        rows.append(
            {
                "complaint_id": row["Complaint ID"],
                "date_received": received,
                "date_sent_to_company": row["Date sent to company"],
                "sub_product": row["Sub-product"],
                "issue": row["Issue"],
                "sub_issue": row["Sub-issue"],
                "state": row["State"],
                "submitted_via": row["Submitted via"],
                "company_response": row["Company response to consumer"],
                "timely": row["Timely response?"],
            }
        )
    rows.sort(key=lambda row: (row["date_received"], int(row["complaint_id"])))
    write_csv(target, rows, CFPB_SAFE_FIELDS)
    return len(rows)


def _refresh_cfpb(project_root: Path, manifest: dict[str, Any]) -> None:
    raw_item = manifest["raw_files"][0]
    target = project_root / raw_item["path"]
    with tempfile.TemporaryDirectory(prefix="hsdl-cfpb-") as directory:
        temporary_root = Path(directory)
        export_path = temporary_root / "official-export.csv"
        minimized_path = temporary_root / target.name
        _download(manifest["download_url"], export_path)
        observed_rows = _privacy_minimize_cfpb(export_path, minimized_path)
        if observed_rows != manifest["expected_rows"]:
            raise ValueError(
                "CFPB privacy-minimized row count changed: "
                f"expected {manifest['expected_rows']}, observed {observed_rows}."
            )
        observed = sha256(minimized_path)
        if observed != raw_item["sha256"]:
            raise ValueError(
                "CFPB reviewed extract changed. "
                f"Expected {raw_item['sha256']}; observed {observed}. "
                "Review source revisions before updating the snapshot."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(minimized_path, target)


def _refresh_multi_asset_snapshot(
    project_root: Path,
    manifest: dict[str, Any],
) -> None:
    raw_item = manifest["raw_files"][0]
    target = project_root / raw_item["path"]
    reviewed: dict[str, Any] = {
        "source": manifest["source_id"],
        "requested_period": manifest["requested_period"],
        "symbols": {},
    }
    with tempfile.TemporaryDirectory(prefix="hsdl-multi-asset-") as directory:
        temporary_root = Path(directory)
        for item in manifest["download_urls"]:
            symbol = item["symbol"]
            response_path = temporary_root / f"{symbol}.json"
            _download(item["url"], response_path)
            payload = load_json(response_path)
            result = payload.get("chart", {}).get("result")
            if not result:
                raise ValueError(f"Market-data response missing result for {symbol}.")
            chart = result[0]
            timestamps = chart.get("timestamp", [])
            adjusted_groups = chart.get("indicators", {}).get("adjclose", [])
            if not adjusted_groups:
                raise ValueError(f"Adjusted close missing for {symbol}.")
            adjusted = adjusted_groups[0].get("adjclose", [])
            if len(timestamps) != len(adjusted):
                raise ValueError(
                    f"Market-data timestamp/price mismatch for {symbol}."
                )
            reviewed["symbols"][symbol] = {
                "timestamp": timestamps,
                "adjusted_close": adjusted,
            }
        combined = temporary_root / target.name
        write_json(combined, reviewed)
        observed = sha256(combined)
        if observed != raw_item["sha256"]:
            raise ValueError(
                "Multi-asset source snapshot changed. "
                f"Expected {raw_item['sha256']}; observed {observed}. "
                "Review corrections and the changed end point before updating "
                "the manifest."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(combined, target)


def download_project(project_root: Path, *, refresh: bool = False) -> dict[str, Any]:
    manifest = load_json(project_root / "source-manifest.json")
    if refresh:
        if manifest["project_id"] == "treasury-risk-engineering":
            _refresh_treasury(project_root, manifest)
        elif manifest["project_id"] == "spatial-equity-planning":
            _refresh_spatial(project_root, manifest)
        elif manifest["project_id"] == "cfpb-fintech-complaint-operations":
            _refresh_cfpb(project_root, manifest)
        elif manifest["project_id"] == "regime-aware-multi-asset-portfolio":
            _refresh_multi_asset_snapshot(project_root, manifest)
        else:
            _refresh_generic(project_root, manifest)
    records = verify_raw_files(project_root)
    receipt = {
        "project_id": manifest["project_id"],
        "source_id": manifest["source_id"],
        "verified_at": datetime.now().astimezone().isoformat(),
        "refresh_requested": refresh,
        "status": "verified",
        "files": records,
    }
    write_json(project_root / "data" / "download-receipt.json", receipt)
    return receipt


def read_csv(path: Path, *, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


MISSING_TEXT_TOKENS = frozenset({"", "?", "n/a", "na"})
MISSING_VALUE_POLICY = {
    "normalization": "trim surrounding whitespace and compare text case-insensitively",
    "treated_as_missing": ["null", "empty string", "?", "N/A", "NA"],
    "not_treated_as_missing": ["Not Applicable"],
}


def is_missing_value(value: Any) -> bool:
    """Apply the repository-wide missing-value rule."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().casefold() in MISSING_TEXT_TOKENS
    return False


def _quality(
    rows: list[dict[str, Any]],
    key: str | list[str] | None = None,
) -> dict[str, Any]:
    columns = list(rows[0]) if rows else []
    missing = {
        column: sum(is_missing_value(row.get(column)) for row in rows)
        for column in columns
    }
    duplicate_count = 0
    if key:
        key_fields = [key] if isinstance(key, str) else key
        values = [tuple(row.get(field) for field in key_fields) for row in rows]
        duplicate_count = len(values) - len(set(values))
    return {
        "rows": len(rows),
        "columns": len(columns),
        "column_names": columns,
        "missing_count_by_column": missing,
        "duplicate_key_count": duplicate_count,
        "quality_status": "usable_with_documented_limitations",
    }


def _zip_text(path: Path, member: str, encoding: str = "utf-8") -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read(member).decode(encoding, errors="replace")


ADULT_FIELDS = [
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education_num",
    "marital_status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
    "native_country",
    "income",
    "source_split",
]


def _prepare_population(project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw = _zip_text(
        project_root / "data/raw/uci-heart-failure.zip",
        "heart_failure_clinical_records_dataset.csv",
    )
    rows = list(csv.DictReader(io.StringIO(raw)))
    write_csv(project_root / "data/processed/analysis.csv", rows, list(rows[0]))
    dictionary = {
        "grain": "patient follow-up",
        "primary_key": None,
        "fields": {
            "age": "age in years",
            "ejection_fraction": "percentage of blood leaving the heart per contraction",
            "serum_creatinine": "serum creatinine, mg/dL",
            "time": "follow-up time in days",
            "DEATH_EVENT": "death observed during follow-up (1/0)",
            "sex": "binary coding supplied by the source; interpretation limited",
        },
    }
    return rows, dictionary


def _prepare_behavioral(project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = read_csv(
        project_root / "data/raw/pseudoword-passage-reading.tsv",
        delimiter="\t",
    )
    for row in rows:
        row["subnum"] = row["subnum"].strip().strip('"')
    fields = list(rows[0])
    write_csv(project_root / "data/processed/analysis.csv", rows, fields)
    dictionary = {
        "grain": "participant with repeated meaningful and pseudoword measures",
        "primary_key": "subnum",
        "fields": {
            "subnum": "opaque participant pairing identifier",
            "group": "1 control; 2 dyslexic",
            "Vd": "pseudoword-passage fixation duration (source codebook)",
            "Td": "meaningful-text-passage fixation duration (source codebook)",
            "p_avg_f": "average fixation count on target pseudowords",
            "m_avg_f": "average fixation count on target meaningful words",
        },
    }
    return rows, dictionary


def _prepare_adult(project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    zip_path = project_root / "data/raw/uci-adult.zip"
    rows: list[dict[str, Any]] = []
    for member, split in (("adult.data", "train"), ("adult.test", "test")):
        text = _zip_text(zip_path, member)
        for line in text.splitlines():
            if not line.strip() or line.startswith("|"):
                continue
            values = [value.strip() for value in line.rstrip(".").split(",")]
            if len(values) != 15:
                continue
            rows.append(dict(zip(ADULT_FIELDS, values + [split])))
    write_csv(project_root / "data/processed/analysis.csv", rows, ADULT_FIELDS)
    dictionary = {
        "grain": "Census-derived person record",
        "primary_key": None,
        "target": "income",
        "train_test_contract": "Use source-provided adult.data for training and adult.test for final evaluation.",
        "fields": {field: field.replace("_", " ") for field in ADULT_FIELDS},
    }
    return rows, dictionary


def _prepare_bike(project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw = _zip_text(project_root / "data/raw/uci-bike-sharing.zip", "hour.csv")
    rows = list(csv.DictReader(io.StringIO(raw)))
    write_csv(project_root / "data/processed/analysis.csv", rows, list(rows[0]))
    dictionary = {
        "grain": "observed system-hour",
        "primary_key": "instant",
        "fields": {
            "dteday": "calendar date",
            "hr": "hour, 0-23",
            "workingday": "1 when neither weekend nor holiday",
            "weathersit": "weather severity category, 1-4",
            "casual": "casual rental count",
            "registered": "registered rental count",
            "cnt": "total rentals",
        },
    }
    return rows, dictionary


def _prepare_treasury(project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for year in range(2020, 2026):
        source = read_csv(project_root / f"data/raw/treasury-{year}.csv")
        for row in source:
            date = datetime.strptime(row["Date"], "%m/%d/%Y").date().isoformat()
            cleaned = {"date": date}
            for key, value in row.items():
                if key != "Date":
                    cleaned[key] = value
            rows.append(cleaned)
    rows.sort(key=lambda row: row["date"])
    fields = ["date"] + [field for field in rows[0] if field != "date"]
    write_csv(project_root / "data/processed/analysis.csv", rows, fields)
    dictionary = {
        "grain": "official business-day par yield curve",
        "primary_key": "date",
        "units": "annualized percentage yield",
        "fields": {field: f"Treasury par yield at {field} maturity" for field in fields[1:]},
    }
    dictionary["fields"]["date"] = "observation date, ISO 8601"
    return rows, dictionary


def _read_pipe_table(path: Path) -> dict[str, dict[str, str]]:
    rows = read_csv(path, delimiter="|")
    return {row["GEO_ID"]: row for row in rows}


def _safe_number(value: str | None) -> float | None:
    if value in (None, "", "N/A", "NA", "-666666666", "-999999999"):
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _prepare_spatial(project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tables = {
        name: _read_pipe_table(project_root / f"data/raw/acs-{name}-ma.dat")
        for name in ("b01003", "b17001", "b19013", "b08301", "b25064")
    }
    centroids: dict[str, tuple[str, str]] = {}
    with zipfile.ZipFile(
        project_root / "data/raw/2023_Gaz_tracts_national.zip"
    ) as archive:
        member = archive.namelist()[0]
        with archive.open(member) as source:
            reader = csv.DictReader(
                io.TextIOWrapper(source, encoding="utf-8"),
                delimiter="\t",
            )
            for row in reader:
                row = {key.strip(): value.strip() for key, value in row.items()}
                if row["USPS"] == "MA":
                    centroids[row["GEOID"]] = (row["INTPTLAT"], row["INTPTLONG"])
    rows: list[dict[str, Any]] = []
    for geo_id, population_row in tables["b01003"].items():
        geoid = geo_id.replace("1400000US", "")
        if geoid not in centroids:
            continue
        poverty = tables["b17001"].get(geo_id, {})
        income = tables["b19013"].get(geo_id, {})
        commute = tables["b08301"].get(geo_id, {})
        rent = tables["b25064"].get(geo_id, {})
        population = _safe_number(population_row.get("B01003_E001"))
        poverty_total = _safe_number(poverty.get("B17001_E001"))
        poverty_count = _safe_number(poverty.get("B17001_E002"))
        workers = _safe_number(commute.get("B08301_E001"))
        transit = _safe_number(commute.get("B08301_E010"))
        median_income = _safe_number(income.get("B19013_E001"))
        median_rent = _safe_number(rent.get("B25064_E001"))
        rows.append(
            {
                "geoid": geoid,
                "latitude": centroids[geoid][0],
                "longitude": centroids[geoid][1],
                "population": "" if population is None else int(population),
                "population_moe": population_row.get("B01003_M001", ""),
                "poverty_population": "" if poverty_total is None else int(poverty_total),
                "poverty_count": "" if poverty_count is None else int(poverty_count),
                "poverty_count_moe": poverty.get("B17001_M002", ""),
                "median_household_income": "" if median_income is None else median_income,
                "median_income_moe": income.get("B19013_M001", ""),
                "workers": "" if workers is None else int(workers),
                "public_transit_workers": "" if transit is None else int(transit),
                "median_gross_rent": "" if median_rent is None else median_rent,
                "median_rent_moe": rent.get("B25064_M001", ""),
            }
        )
    fields = list(rows[0])
    write_csv(project_root / "data/processed/analysis.csv", rows, fields)
    dictionary = {
        "grain": "Massachusetts census tract",
        "primary_key": "geoid",
        "coordinate_reference_system": "EPSG:4326 (Gazetteer internal points)",
        "estimate_period": "2019-2023 ACS 5-year",
        "fields": {
            "population": "B01003 estimate",
            "poverty_count": "B17001 population below poverty level",
            "median_household_income": "B19013 median household income",
            "public_transit_workers": "B08301 public transportation workers",
            "median_gross_rent": "B25064 median gross rent",
            "latitude": "Census Gazetteer internal point latitude",
            "longitude": "Census Gazetteer internal point longitude",
        },
    }
    return rows, dictionary


def _prepare_bank_marketing(
    project_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    outer_path = project_root / "data/raw/uci-bank-marketing.zip"
    with zipfile.ZipFile(outer_path) as outer:
        nested_bytes = outer.read("bank-additional.zip")
    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as nested:
        text = nested.read(
            "bank-additional/bank-additional-full.csv"
        ).decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(text), delimiter=";"))
    for index, row in enumerate(rows):
        row["source_order"] = index + 1
    fields = ["source_order", *[field for field in rows[0] if field != "source_order"]]
    write_csv(project_root / "data/processed/analysis.csv", rows, fields)
    dictionary = {
        "grain": "one direct-marketing contact outcome",
        "primary_key": "source_order",
        "target": "y",
        "temporal_contract": (
            "The source states bank-additional-full.csv is ordered by date. "
            "Source order is retained as an imperfect time proxy because a full "
            "calendar date is not supplied."
        ),
        "leakage_exclusion": {
            "duration": (
                "Last contact duration is known only after contact and is excluded "
                "from every pre-contact prediction and targeting calculation."
            )
        },
        "fields": {
            "source_order": "1-based source row order",
            "age": "client age in years",
            "job": "job category",
            "contact": "contact communication type",
            "campaign": "contacts in the current campaign",
            "pdays": "days since prior contact; 999 means not previously contacted",
            "previous": "contacts before the current campaign",
            "poutcome": "previous campaign outcome",
            "y": "whether the client subscribed to a term deposit",
        },
    }
    return rows, dictionary


def _prepare_cfpb(
    project_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_path = (
        project_root
        / "data/raw/cfpb-digital-payments-2022-sanitized.csv"
    )
    rows = read_csv(raw_path)
    if list(rows[0]) != CFPB_SAFE_FIELDS:
        raise ValueError("CFPB snapshot contains an unexpected field set.")
    rows.sort(key=lambda row: (row["date_received"], int(row["complaint_id"])))
    write_csv(
        project_root / "data/processed/analysis.csv",
        rows,
        CFPB_SAFE_FIELDS,
    )
    write_json(
        project_root / "data/privacy-receipt.json",
        {
            "project_id": "cfpb-fintech-complaint-operations",
            "review_status": "approved_for_public_aggregate_analysis",
            "stored_fields": CFPB_SAFE_FIELDS,
            "excluded_before_storage": [
                "consumer complaint narrative",
                "company",
                "ZIP code",
                "tags",
                "company public response",
            ],
            "record_count": len(rows),
            "direct_identifiers_stored": False,
        },
    )
    dictionary = {
        "grain": "one published digital-payment complaint received in 2022",
        "primary_key": "complaint_id",
        "target": "timely",
        "fields": {
            "complaint_id": "CFPB public complaint identifier",
            "date_received": "timestamp when CFPB received the complaint",
            "date_sent_to_company": "timestamp when CFPB sent the complaint",
            "sub_product": "consumer-identified sub-product",
            "issue": "consumer-identified issue category",
            "sub_issue": "consumer-identified sub-issue category",
            "state": "two-letter state code when reported",
            "submitted_via": "complaint submission channel",
            "company_response": "company response disposition",
            "timely": "CFPB timely-response indicator",
        },
        "interpretation_boundary": (
            "The timely flag does not measure complaint merit, consumer harm, "
            "resolution quality, or regulatory compliance."
        ),
    }
    return rows, dictionary


PREPARERS: dict[str, Callable[[Path], tuple[list[dict[str, Any]], dict[str, Any]]]] = {
    "population-health-survival": _prepare_population,
    "behavioral-reading-experiment": _prepare_behavioral,
    "census-income-ai": _prepare_adult,
    "bike-demand-operations": _prepare_bike,
    "treasury-risk-engineering": _prepare_treasury,
    "spatial-equity-planning": _prepare_spatial,
    "bank-marketing-response": _prepare_bank_marketing,
    "cfpb-fintech-complaint-operations": _prepare_cfpb,
}


def prepare_project(project_root: Path) -> dict[str, Any]:
    manifest = load_json(project_root / "source-manifest.json")
    verify_raw_files(project_root)
    rows, dictionary = PREPARERS[manifest["project_id"]](project_root)
    quality = _quality(rows, dictionary.get("primary_key"))
    if dictionary.get("missing_value_policy"):
        quality["missing_value_policy"] = dictionary["missing_value_policy"]
    quality["expected_rows"] = manifest["expected_rows"]
    quality["row_count_matches_manifest"] = len(rows) == manifest["expected_rows"]
    quality["privacy_review"] = manifest["privacy_review"]
    if not quality["row_count_matches_manifest"]:
        raise ValueError(
            f"Prepared row count {len(rows)} does not match manifest "
            f"{manifest['expected_rows']}."
        )
    write_json(project_root / "data" / "data-dictionary.json", dictionary)
    write_json(project_root / "data" / "quality-report.json", quality)
    return quality


def mean(values: Iterable[float]) -> float:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else float("nan")


def quantile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    index = (len(ordered) - 1) * probability
    low, high = math.floor(index), math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] * (high - index) + ordered[high] * (index - low)


def sd(values: Iterable[float]) -> float:
    materialized = list(values)
    return statistics.stdev(materialized) if len(materialized) > 1 else 0.0


def bootstrap_statistic(
    values: list[Any],
    statistic: Callable[[list[Any]], float],
    *,
    samples: int = 1000,
    seed: int = 20260727,
) -> list[float]:
    rng = random.Random(seed)
    return [
        statistic([values[rng.randrange(len(values))] for _ in values])
        for _ in range(samples)
    ]


def _visual_theme(title: str, source: str) -> tuple[str, str]:
    """Return a domain-aware accent and tint without changing chart semantics."""
    value = f"{title} {source}".casefold()
    rules = (
        (("health", "survival", "hazard", "clinical", "patient"), ("teal", "teal_light")),
        (("treasury", "finance", "margin", "revenue", "cash", "yield", "var"), ("violet", "violet_light")),
        (("marketing", "campaign", "response", "capacity"), ("pink", "pink_light")),
        (("governance", "disclosure", "inventory", "assurance"), ("gold", "gold_light")),
        (("spatial", "tract", "hub", "poverty", "coverage"), ("orange", "orange_light")),
        (("bike", "allocation", "operations", "demand"), ("olive", "olive_light")),
        (("model", "calibration", "auc", "census", "prediction"), ("blue", "blue_light")),
    )
    for tokens, keys in rules:
        if any(token in value for token in tokens):
            return PALETTE[keys[0]], PALETTE[keys[1]]
    return PALETTE["blue"], PALETTE["blue_light"]


def _svg_shell(title: str, subtitle: str, body: str, source: str, height: int = 540) -> str:
    escaped_title = escape(title)
    escaped_subtitle = escape(subtitle)
    escaped_source = escape(source)
    accent, tint = _visual_theme(title, source)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc">
<title id="title">{escaped_title}</title>
<desc id="desc">{escaped_subtitle}. Source: {escaped_source}</desc>
<defs>
  <pattern id="microGrid" width="22" height="22" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r=".85" fill="#FFFFFF" opacity=".12"/>
  </pattern>
</defs>
<rect width="1000" height="{height}" fill="{PALETTE['canvas']}"/>
<rect width="1000" height="102" fill="{PALETTE['navy']}"/>
<rect width="1000" height="102" fill="url(#microGrid)"/>
<rect width="8" height="102" fill="{accent}"/>
<circle cx="925" cy="50" r="30" fill="none" stroke="{accent}" stroke-width="2" opacity=".9"/>
<circle cx="925" cy="50" r="9" fill="{accent}"/>
<circle cx="925" cy="50" r="52" fill="none" stroke="#49627F" stroke-width="1" opacity=".55"/>
<line x1="860" y1="50" x2="990" y2="50" stroke="#49627F" stroke-width="1"/>
<line x1="925" y1="4" x2="925" y2="96" stroke="#49627F" stroke-width="1"/>
<text x="42" y="24" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif" font-size="9.5" font-weight="800" letter-spacing="1.6" fill="{accent}">EDITORIAL EVIDENCE · ANALYTICAL REPORT</text>
<text x="42" y="55" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif" font-size="25" font-weight="760" fill="{PALETTE['paper']}">{escaped_title}</text>
<text x="42" y="82" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif" font-size="13.5" fill="#C7D4E4">{escaped_subtitle}</text>
<rect x="36" y="110" width="928" height="348" rx="18" fill="#07152A" opacity=".07"/>
<rect x="32" y="104" width="936" height="350" rx="18" fill="{PALETTE['paper']}" stroke="{PALETTE['grid']}"/>
<rect x="32" y="104" width="5" height="350" rx="2.5" fill="{accent}"/>
<rect x="45" y="112" width="74" height="8" rx="4" fill="{tint}"/>
{body}
<line x1="42" y1="{height-55}" x2="958" y2="{height-55}" stroke="{PALETTE['grid_dark']}"/>
<text x="42" y="{height-30}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif" font-size="10.5" fill="{PALETTE['muted']}">Source: {escaped_source}</text>
<text x="958" y="{height-30}" text-anchor="end" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif" font-size="9.5" font-weight="750" letter-spacing=".8" fill="{accent}">SOURCE-TRACEABLE · CLAIM-BOUNDED</text>
</svg>
"""


def svg_bar(
    path: Path,
    title: str,
    subtitle: str,
    items: list[tuple[str, float]],
    source: str,
    *,
    percent: bool = False,
    benchmark: float | None = None,
) -> None:
    maximum = max([value for _, value in items] + ([benchmark] if benchmark is not None else [0]))
    maximum = maximum or 1.0
    accent, tint = _visual_theme(title, source)
    body = []
    top, row_height = 120, min(62, 310 / max(1, len(items)))
    for index, (label, value) in enumerate(items):
        y = top + index * row_height
        # Keep a stable right-hand gutter for the value label, including when
        # the largest bar reaches the chart maximum.
        width = 560 * value / maximum
        body.append(
            f'<rect x="48" y="{y-7:.1f}" width="900" height="{min(45, row_height-4):.1f}" '
            f'rx="9" fill="{"#F8FAFC" if index % 2 else PALETTE["paper"]}"/>'
            f'<circle cx="64" cy="{y+12:.1f}" r="11" fill="{tint}"/>'
            f'<text x="64" y="{y+16:.1f}" text-anchor="middle" '
            f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace" '
            f'font-size="9.5" font-weight="800" fill="{accent}">{index+1:02d}</text>'
            f'<text x="84" y="{y+18:.1f}" font-family="-apple-system,BlinkMacSystemFont,'
            f'&quot;Segoe UI&quot;,Arial,sans-serif" font-size="13.5" '
            f'font-weight="650" fill="{PALETTE["ink"]}">{escape(label)}</text>'
        )
        body.append(
            f'<rect x="300" y="{y+1:.1f}" width="540" height="20" rx="10" '
            f'fill="{PALETTE["grid"]}" opacity=".52"/>'
        )
        body.append(
            f'<rect x="300" y="{y+1:.1f}" width="{max(1, 540 * value / maximum):.1f}" '
            f'height="20" rx="10" fill="{accent}" opacity="{1 if index == 0 else .78}"/>'
        )
        rendered = f"{value:.1%}" if percent else f"{value:,.2f}"
        body.append(
            f'<rect x="856" y="{y-2:.1f}" width="78" height="26" rx="13" '
            f'fill="{tint}" stroke="{accent}" stroke-opacity=".28"/>'
            f'<text x="895" y="{y+16:.1f}" text-anchor="middle" '
            f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace" '
            f'font-size="11.5" font-weight="800" fill="{PALETTE["ink"]}">{rendered}</text>'
        )
    if benchmark is not None:
        x = 300 + 540 * benchmark / maximum
        body.append(
            f'<line x1="{x:.1f}" y1="112" x2="{x:.1f}" y2="438" '
            f'stroke="{PALETTE["gold"]}" stroke-width="2" stroke-dasharray="5 5"/>'
            f'<rect x="{x-40:.1f}" y="108" width="80" height="20" rx="10" '
            f'fill="{PALETTE["gold_light"]}"/>'
            f'<text x="{x:.1f}" y="122" text-anchor="middle" '
            f'font-family="-apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,Arial,sans-serif" '
            f'font-size="8.5" font-weight="800" letter-spacing=".8" '
            f'fill="{PALETTE["gold"]}">REFERENCE</text>'
        )
    path.write_text(_svg_shell(title, subtitle, "".join(body), source), encoding="utf-8")


def svg_line(
    path: Path,
    title: str,
    subtitle: str,
    series: list[tuple[str, list[tuple[float, float]]]],
    source: str,
    *,
    y_percent: bool = False,
) -> None:
    all_x = [x for _, points in series for x, _ in points]
    all_y = [y for _, points in series for _, y in points]
    xmin, xmax = min(all_x), max(all_x)
    ymin, ymax = min(all_y), max(all_y)
    if math.isclose(ymin, ymax):
        ymin, ymax = ymin - 1, ymax + 1
    accent, tint = _visual_theme(title, source)
    colors = [accent, PALETTE["gold"], PALETTE["pink"], PALETTE["olive"]]
    body = [
        f'<rect x="66" y="119" width="874" height="317" rx="13" fill="#FBFCFE" '
        f'stroke="{PALETTE["grid"]}"/>',
        f'<rect x="90" y="126" width="106" height="24" rx="12" fill="{tint}"/>',
        f'<text x="143" y="142" text-anchor="middle" '
        f'font-family="-apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,Arial,sans-serif" '
        f'font-size="9" font-weight="800" letter-spacing=".8" fill="{accent}">'
        f'{sum(len(points) for _, points in series)} OBSERVATIONS</text>',
        f'<line x1="90" y1="430" x2="930" y2="430" stroke="{PALETTE["ink_soft"]}" stroke-width="1.4"/>',
        f'<line x1="90" y1="110" x2="90" y2="430" stroke="{PALETTE["ink_soft"]}" stroke-width="1.4"/>',
    ]
    x_is_share = xmin >= 0 and xmax <= 1
    x_is_integer_scale = (
        float(xmin).is_integer() and float(xmax).is_integer() and xmax >= 10
    )
    for grid_index in range(5):
        x = 90 + grid_index * 210
        value = xmin + grid_index * (xmax - xmin) / 4
        if x_is_share:
            rendered = f"{value:.0%}"
        elif x_is_integer_scale:
            rendered = f"{value:.0f}"
        else:
            rendered = f"{value:.2f}"
        body.append(
            f'<line x1="{x}" y1="430" x2="{x}" y2="436" '
            f'stroke="{PALETTE["ink"]}"/>'
            f'<text x="{x}" y="451" text-anchor="middle" font-family="Arial" '
            f'font-size="12" fill="{PALETTE["muted"]}">{rendered}</text>'
        )
    for grid_index in range(5):
        y = 110 + grid_index * 80
        value = ymax - grid_index * (ymax - ymin) / 4
        rendered = f"{value:.0%}" if y_percent else f"{value:.2f}"
        body.append(
            f'<line x1="90" y1="{y}" x2="930" y2="{y}" '
            f'stroke="{PALETTE["grid"]}" stroke-dasharray="2 5"/>'
            f'<text x="82" y="{y+4}" text-anchor="end" font-family="Arial" '
            f'font-size="12" fill="{PALETTE["muted"]}">{rendered}</text>'
        )
    for index, (label, points) in enumerate(series):
        coordinates = []
        for x, y in points:
            px = 90 + 840 * (x - xmin) / (xmax - xmin or 1)
            py = 430 - 320 * (y - ymin) / (ymax - ymin)
            coordinates.append(f"{px:.1f},{py:.1f}")
        color = colors[index % len(colors)]
        dash = ' stroke-dasharray="7 5"' if index % 2 else ""
        body.append(
            f'<polyline points="{" ".join(coordinates)}" fill="none" '
            f'stroke="{color}" stroke-width="{4 if index == 0 else 3}" '
            f'stroke-linejoin="round" stroke-linecap="round"{dash}/>'
        )
        last_x, last_y = coordinates[-1].split(",")
        body.append(
            f'<circle cx="{last_x}" cy="{last_y}" r="{6 if index == 0 else 4.5}" '
            f'fill="{PALETTE["paper"]}" stroke="{color}" stroke-width="3"/>'
        )
        if len(points) <= 12:
            for coordinate in coordinates[:-1]:
                px, py = coordinate.split(",")
                body.append(
                    f'<circle cx="{px}" cy="{py}" r="2.7" fill="{PALETTE["paper"]}" '
                    f'stroke="{color}" stroke-width="1.6"/>'
                )
        body.append(
            f'<line x1="{110+index*190}" y1="96" x2="{140+index*190}" y2="96" '
            f'stroke="{color}" stroke-width="4" stroke-linecap="round"{dash}/>'
            f'<text x="{146+index*190}" y="100" font-family="-apple-system,'
            f'BlinkMacSystemFont,&quot;Segoe UI&quot;,Arial,sans-serif" '
            f'font-size="12.5" font-weight="650" '
            f'fill="#C7D4E4">{escape(label)}</text>'
        )
    path.write_text(_svg_shell(title, subtitle, "".join(body), source), encoding="utf-8")


def svg_interval(
    path: Path,
    title: str,
    subtitle: str,
    items: list[tuple[str, float, float, float]],
    source: str,
) -> None:
    low = min(item[2] for item in items)
    high = max(item[3] for item in items)
    padding = (high - low) * 0.12 or 1
    low, high = low - padding, high + padding
    accent, tint = _visual_theme(title, source)
    body = []
    if low <= 0 <= high:
        zero_x = 300 + 610 * (0 - low) / (high - low)
        body.append(
            f'<line x1="{zero_x:.1f}" y1="116" x2="{zero_x:.1f}" y2="430" '
            f'stroke="{PALETTE["gold"]}" stroke-width="2" stroke-dasharray="5 5"/>'
            f'<text x="{zero_x:.1f}" y="111" text-anchor="middle" '
            f'font-family="-apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,Arial,sans-serif" '
            f'font-size="9" font-weight="800" fill="{PALETTE["gold"]}">NULL</text>'
        )
    row_gap = min(62.0, 280.0 / max(1, len(items) - 1))
    for index, (label, point, left, right) in enumerate(items):
        y = 142 + index * row_gap
        x1 = 300 + 610 * (left - low) / (high - low)
        x2 = 300 + 610 * (right - low) / (high - low)
        xp = 300 + 610 * (point - low) / (high - low)
        body.append(
            f'<rect x="48" y="{y-27}" width="900" height="54" rx="10" '
            f'fill="{"#F8FAFC" if index % 2 else PALETTE["paper"]}"/>'
            f'<text x="66" y="{y+5}" font-family="-apple-system,BlinkMacSystemFont,'
            f'&quot;Segoe UI&quot;,Arial,sans-serif" font-size="13.5" '
            f'font-weight="650" fill="{PALETTE["ink"]}">{escape(label)}</text>'
            f'<line x1="{x1:.1f}" y1="{y}" x2="{x2:.1f}" y2="{y}" '
            f'stroke="{accent}" stroke-width="5" stroke-linecap="round"/>'
            f'<circle cx="{xp:.1f}" cy="{y}" r="8" fill="{PALETTE["paper"]}" '
            f'stroke="{accent}" stroke-width="3"/>'
            f'<circle cx="{xp:.1f}" cy="{y}" r="3" fill="{accent}"/>'
            f'<rect x="770" y="{y-14}" width="164" height="28" rx="14" fill="{tint}"/>'
            f'<text x="852" y="{y+5}" text-anchor="middle" '
            f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace" '
            f'font-size="10.5" font-weight="750" fill="{PALETTE["ink"]}">'
            f'{point:.2f} [{left:.2f}, {right:.2f}]</text>'
        )
    path.write_text(_svg_shell(title, subtitle, "".join(body), source), encoding="utf-8")


def svg_heatmap(
    path: Path,
    title: str,
    subtitle: str,
    rows: list[str],
    columns: list[str],
    values: list[list[float]],
    source: str,
) -> None:
    accent, _ = _visual_theme(title, source)
    body = []
    cell_w = min(120, 660 / max(1, len(columns)))
    cell_h = min(52, 300 / max(1, len(rows)))
    x0, y0 = 270, 130
    for column_index, column in enumerate(columns):
        body.append(
            f'<text x="{x0+(column_index+.5)*cell_w:.1f}" y="112" '
            f'text-anchor="middle" font-family="Arial" font-size="11" '
            f'fill="{PALETTE["ink"]}">{escape(column)}</text>'
        )
    for row_index, label in enumerate(rows):
        body.append(
            f'<text x="258" y="{y0+(row_index+.62)*cell_h:.1f}" '
            f'text-anchor="end" font-family="Arial" font-size="12" '
            f'fill="{PALETTE["ink"]}">{escape(label)}</text>'
        )
        for column_index, value in enumerate(values[row_index]):
            opacity = 0.12 + 0.78 * min(1, max(0, value))
            text_fill = PALETTE["paper"] if opacity >= 0.62 else PALETTE["ink"]
            body.append(
                f'<rect x="{x0+column_index*cell_w:.1f}" '
                f'y="{y0+row_index*cell_h:.1f}" width="{cell_w-3:.1f}" '
                f'height="{cell_h-3:.1f}" rx="7" fill="{accent}" '
                f'fill-opacity="{opacity:.2f}" stroke="{PALETTE["paper"]}" stroke-width="2"/>'
                f'<text x="{x0+(column_index+.5)*cell_w:.1f}" '
                f'y="{y0+(row_index+.62)*cell_h:.1f}" text-anchor="middle" '
                f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace" '
                f'font-size="10.5" font-weight="750" fill="{text_fill}">'
                f'{value:.0%}</text>'
            )
    body.append(
        f'<text x="270" y="448" font-family="-apple-system,BlinkMacSystemFont,'
        f'&quot;Segoe UI&quot;,Arial,sans-serif" font-size="9.5" '
        f'font-weight="800" letter-spacing=".8" fill="{PALETTE["muted"]}">'
        f'LOWER COMPLETENESS</text>'
        f'<rect x="395" y="439" width="150" height="10" rx="5" fill="{accent}" opacity=".22"/>'
        f'<rect x="545" y="439" width="150" height="10" rx="5" fill="{accent}" opacity=".82"/>'
        f'<text x="708" y="448" font-family="-apple-system,BlinkMacSystemFont,'
        f'&quot;Segoe UI&quot;,Arial,sans-serif" font-size="9.5" '
        f'font-weight="800" letter-spacing=".8" fill="{PALETTE["muted"]}">'
        f'HIGHER COMPLETENESS</text>'
    )
    path.write_text(_svg_shell(title, subtitle, "".join(body), source), encoding="utf-8")


def _km(rows: list[dict[str, str]]) -> list[tuple[float, float]]:
    by_time: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        by_time[int(float(row["time"]))].append(int(float(row["DEATH_EVENT"])))
    at_risk = len(rows)
    survival = 1.0
    points = [(0.0, 1.0)]
    for time in sorted(by_time):
        events = sum(by_time[time])
        count = len(by_time[time])
        if at_risk and events:
            survival *= 1 - events / at_risk
        points.append((float(time), survival))
        at_risk -= count
    return points


def _km_at(points: list[tuple[float, float]], day: int) -> float:
    value = 1.0
    for time, survival in points:
        if time > day:
            break
        value = survival
    return value


def _solve_linear_system(
    matrix: list[list[float]],
    vector: list[float],
) -> list[float]:
    size = len(vector)
    augmented = [
        [float(value) for value in row] + [float(vector[index])]
        for index, row in enumerate(matrix)
    ]
    for column in range(size):
        pivot = max(
            range(column, size),
            key=lambda row: abs(augmented[row][column]),
        )
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("Singular linear system.")
        augmented[column], augmented[pivot] = (
            augmented[pivot],
            augmented[column],
        )
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                left - factor * right
                for left, right in zip(augmented[row], augmented[column])
            ]
    return [augmented[index][-1] for index in range(size)]


def _inverse_matrix(matrix: list[list[float]]) -> list[list[float]]:
    size = len(matrix)
    columns = []
    for column in range(size):
        unit = [1.0 if row == column else 0.0 for row in range(size)]
        columns.append(_solve_linear_system(matrix, unit))
    return [
        [columns[column][row] for column in range(size)]
        for row in range(size)
    ]


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 3:
        return None
    left_center, right_center = mean(left), mean(right)
    numerator = sum(
        (x - left_center) * (y - right_center)
        for x, y in zip(left, right)
    )
    denominator = math.sqrt(
        sum((x - left_center) ** 2 for x in left)
        * sum((y - right_center) ** 2 for y in right)
    )
    return numerator / denominator if denominator else None


def _cox_ph(
    rows: list[dict[str, str]],
    features: list[str],
    *,
    ridge: float = 1e-5,
    iterations: int = 40,
) -> dict[str, Any]:
    centers = {
        field: mean(float(row[field]) for row in rows) for field in features
    }
    spreads = {
        field: sd(float(row[field]) for row in rows) or 1.0
        for field in features
    }
    x = [
        [
            (float(row[field]) - centers[field]) / spreads[field]
            for field in features
        ]
        for row in rows
    ]
    times = [float(row["time"]) for row in rows]
    events = [int(float(row["DEATH_EVENT"])) for row in rows]
    event_times = sorted({time for time, event in zip(times, events) if event})
    beta = [0.0] * len(features)
    information: list[list[float]] = []
    score: list[float] = []
    log_likelihood = float("nan")
    residuals = {field: [] for field in features}
    residual_times: list[float] = []
    for iteration in range(iterations):
        score = [0.0] * len(features)
        information = [
            [0.0] * len(features) for _ in features
        ]
        log_likelihood = 0.0
        iteration_residuals = {field: [] for field in features}
        iteration_times = []
        linear = [
            max(-35.0, min(35.0, sum(value * coefficient for value, coefficient in zip(row, beta))))
            for row in x
        ]
        risk = [math.exp(value) for value in linear]
        for time in event_times:
            event_indices = [
                index
                for index, (observed_time, event) in enumerate(zip(times, events))
                if observed_time == time and event
            ]
            risk_indices = [
                index for index, observed_time in enumerate(times)
                if observed_time >= time
            ]
            denominator = sum(risk[index] for index in risk_indices)
            weighted_mean = [
                sum(risk[index] * x[index][column] for index in risk_indices)
                / denominator
                for column in range(len(features))
            ]
            second = [
                [
                    sum(
                        risk[index]
                        * x[index][left]
                        * x[index][right]
                        for index in risk_indices
                    )
                    / denominator
                    for right in range(len(features))
                ]
                for left in range(len(features))
            ]
            deaths = len(event_indices)
            for column in range(len(features)):
                score[column] += (
                    sum(x[index][column] for index in event_indices)
                    - deaths * weighted_mean[column]
                )
                for right in range(len(features)):
                    information[column][right] += deaths * (
                        second[column][right]
                        - weighted_mean[column] * weighted_mean[right]
                    )
            log_likelihood += (
                sum(linear[index] for index in event_indices)
                - deaths * math.log(denominator)
            )
            for event_index in event_indices:
                iteration_times.append(math.log(max(time, 1.0)))
                for column, field in enumerate(features):
                    iteration_residuals[field].append(
                        x[event_index][column] - weighted_mean[column]
                    )
        for index in range(len(features)):
            score[index] -= ridge * beta[index]
            information[index][index] += ridge
        delta = _solve_linear_system(information, score)
        beta = [value + change for value, change in zip(beta, delta)]
        residuals = iteration_residuals
        residual_times = iteration_times
        if max(abs(value) for value in delta) < 1e-7:
            break
    covariance = _inverse_matrix(information)
    linear_predictor = [
        sum(value * coefficient for value, coefficient in zip(row, beta))
        for row in x
    ]
    comparable = concordant = tied = 0
    for left in range(len(rows)):
        if not events[left]:
            continue
        for right in range(len(rows)):
            if times[left] >= times[right]:
                continue
            comparable += 1
            if linear_predictor[left] > linear_predictor[right]:
                concordant += 1
            elif math.isclose(
                linear_predictor[left],
                linear_predictor[right],
                abs_tol=1e-12,
            ):
                tied += 1
    c_index = (
        (concordant + 0.5 * tied) / comparable if comparable else None
    )
    baseline_hazard = 0.0
    for time in event_times:
        if time > 180:
            break
        deaths = sum(
            observed_time == time and event
            for observed_time, event in zip(times, events)
        )
        denominator = sum(
            math.exp(max(-35.0, min(35.0, linear_predictor[index])))
            for index, observed_time in enumerate(times)
            if observed_time >= time
        )
        baseline_hazard += deaths / denominator
    predicted_risk_180 = [
        1
        - math.exp(
            -baseline_hazard
            * math.exp(max(-35.0, min(35.0, predictor)))
        )
        for predictor in linear_predictor
    ]
    known_180 = [
        index
        for index, row in enumerate(rows)
        if events[index] and times[index] <= 180 or times[index] >= 180
    ]
    calibration = []
    ranked = sorted(known_180, key=lambda index: predicted_risk_180[index])
    for group in range(5):
        group_indices = ranked[
            group * len(ranked) // 5 : (group + 1) * len(ranked) // 5
        ]
        if not group_indices:
            continue
        calibration.append(
            {
                "risk_group": group + 1,
                "n": len(group_indices),
                "mean_predicted_180d_risk": mean(
                    predicted_risk_180[index] for index in group_indices
                ),
                "observed_180d_event_rate": mean(
                    events[index] and times[index] <= 180
                    for index in group_indices
                ),
            }
        )
    coefficients = {}
    for index, field in enumerate(features):
        standard_error = math.sqrt(max(0.0, covariance[index][index]))
        coefficients[field] = {
            "coefficient_per_sd": beta[index],
            "hazard_ratio_per_sd": math.exp(beta[index]),
            "ci95": [
                math.exp(beta[index] - 1.96 * standard_error),
                math.exp(beta[index] + 1.96 * standard_error),
            ],
            "standardization_center": centers[field],
            "standardization_sd": spreads[field],
            "schoenfeld_time_correlation": _pearson(
                residual_times,
                residuals[field],
            ),
        }
    return {
        "features": features,
        "coefficients": coefficients,
        "iterations": iteration + 1,
        "partial_log_likelihood": log_likelihood,
        "ridge": ridge,
        "harrell_c_index_apparent": c_index,
        "baseline_cumulative_hazard_180d": baseline_hazard,
        "calibration_180d_known_outcomes": calibration,
        "known_180d_outcomes": len(known_180),
        "interpretation": (
            "Hazard ratios are associational, per one sample standard deviation; "
            "calibration and discrimination are apparent, not external validation."
        ),
    }


def _protocol_bootstrap(
    rows: list[dict[str, str]], rule: Callable[[dict[str, str]], bool], seed: int
) -> dict[str, Any]:
    def metrics(sample: list[dict[str, str]]) -> tuple[float, float, float]:
        selected = [row for row in sample if rule(row)]
        deaths = [row for row in sample if int(float(row["DEATH_EVENT"])) == 1]
        captured = [
            row
            for row in deaths
            if rule(row)
        ]
        sensitivity = len(captured) / len(deaths) if deaths else 0.0
        workload = len(selected) / len(sample) if sample else 0.0
        sex_rates = []
        for sex in ("0", "1"):
            group = [row for row in sample if row["sex"].strip() == sex]
            sex_rates.append(sum(rule(row) for row in group) / len(group) if group else 0)
        return sensitivity, workload, abs(sex_rates[0] - sex_rates[1])

    rng = random.Random(seed)
    samples = []
    for _ in range(400):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        samples.append(metrics(sample))
    point = metrics(rows)
    return {
        "high_risk_capture": point[0],
        "workload_share": point[1],
        "sex_selection_gap": point[2],
        "bootstrap": {
            "high_risk_capture": [round(item[0], 6) for item in samples],
            "workload_share": [round(item[1], 6) for item in samples],
            "sex_selection_gap": [round(item[2], 6) for item in samples],
        },
    }

__all__ = [name for name in globals() if not name.startswith("__")]
