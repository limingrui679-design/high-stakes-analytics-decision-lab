#!/usr/bin/env python3
"""Build reviewed source snapshots for the one-program/one-case portfolio.

The public project runtime is standard-library only.  This source builder is a
separate, review-time utility: it downloads official files, minimizes them to
the fields needed by each study, and records no outcome that was not observed
in the source.  The Yale ISPS path requires an explicit terms flag and writes
only non-identifying aggregates; participant-level rows are never copied into
the repository.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import heapq
import io
import json
import math
import sys
import tempfile
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "examples" / "real-data-cases" / "projects"
SHARED = PROJECTS / "_shared"
sys.path.insert(0, str(SHARED))

from safe_external_io import (  # noqa: E402
    ZipLimits,
    download_https_with_curl,
    open_safe_zip,
    open_zip_member,
    read_https_bytes_with_curl,
    read_zip_member,
    validate_zip_archive,
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 High-Stakes-Analytics-Decision-Lab/1.1.0"
)
MAX_XLSX_FILE_BYTES = 50 * 1024 * 1024
MAX_XLSX_MEMBER_COUNT = 2_048
MAX_XLSX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_XLSX_TOTAL_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
MAX_GZIP_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
SOCRATA_QUERY_LIMIT = 50_000
SOURCE_ZIP_LIMITS = ZipLimits(
    maximum_archive_bytes=1024 * 1024 * 1024,
    maximum_members=20_000,
    maximum_member_bytes=1024 * 1024 * 1024,
    maximum_total_uncompressed_bytes=4 * 1024 * 1024 * 1024,
    maximum_expansion_ratio=500.0,
    label="source ZIP",
)
XLSX_LIMITS = ZipLimits(
    maximum_archive_bytes=MAX_XLSX_FILE_BYTES,
    maximum_members=MAX_XLSX_MEMBER_COUNT,
    maximum_member_bytes=MAX_XLSX_MEMBER_BYTES,
    maximum_total_uncompressed_bytes=MAX_XLSX_TOTAL_UNCOMPRESSED_BYTES,
    maximum_expansion_ratio=500.0,
    label="XLSX",
)


def _request(url: str, *, timeout: int = 180) -> bytes:
    return read_https_bytes_with_curl(
        url,
        timeout=timeout,
        maximum_bytes=128 * 1024 * 1024,
        user_agent=USER_AGENT,
    )


def _download(url: str, destination: Path) -> None:
    download_https_with_curl(
        url,
        destination,
        timeout=900,
        maximum_bytes=512 * 1024 * 1024,
        user_agent=USER_AGENT,
    )


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_bike() -> None:
    target = (
        PROJECTS
        / "bike-demand-operations/data/raw/citibike-jc-2021-station-hour.csv"
    )
    aggregate: dict[tuple[str, int, str, str, str, str], list[int]] = defaultdict(
        lambda: [0, 0]
    )
    source_hashes = []
    with tempfile.TemporaryDirectory(prefix="citibike-source-") as directory:
        temp_root = Path(directory)
        for month in range(1, 13):
            name = f"JC-2021{month:02d}-citibike-tripdata.csv.zip"
            url = f"https://s3.amazonaws.com/tripdata/{name}"
            archive_path = temp_root / name
            _download(url, archive_path)
            source_hashes.append(
                {
                    "name": name,
                    "url": url,
                    "sha256": _sha256(archive_path),
                    "bytes": archive_path.stat().st_size,
                }
            )
            with open_safe_zip(archive_path, limits=SOURCE_ZIP_LIMITS) as archive:
                members = [
                    item.filename
                    for item in archive.infolist()
                    if not item.is_dir()
                    and item.filename.endswith(".csv")
                    and not item.filename.startswith("__MACOSX/")
                ]
                if len(members) != 1:
                    raise ValueError(f"Unexpected Citi Bike archive members: {members}")
                with open_zip_member(archive, members[0]) as source:
                    reader = csv.DictReader(io.TextIOWrapper(source, encoding="utf-8-sig"))
                    for row in reader:
                        for side, index in (("start", 0), ("end", 1)):
                            timestamp = row.get(f"{side}ed_at", "")
                            station_id = row.get(f"{side}_station_id", "").strip()
                            if not timestamp or not station_id:
                                continue
                            observed = datetime.fromisoformat(timestamp)
                            key = (
                                observed.date().isoformat(),
                                observed.hour,
                                station_id,
                                row.get(f"{side}_station_name", "").strip(),
                                row.get(f"{side}_lat", "").strip(),
                                row.get(f"{side}_lng", "").strip(),
                            )
                            aggregate[key][index] += 1
    rows = [
        {
            "date": key[0],
            "hour": key[1],
            "station_id": key[2],
            "station_name": key[3],
            "latitude": key[4],
            "longitude": key[5],
            "pickups": values[0],
            "returns": values[1],
        }
        for key, values in sorted(aggregate.items())
    ]
    _write_csv(
        target,
        rows,
        [
            "date",
            "hour",
            "station_id",
            "station_name",
            "latitude",
            "longitude",
            "pickups",
            "returns",
        ],
    )
    _write_json(target.with_suffix(".source-lock.json"), {"files": source_hashes})
    print(json.dumps({"case": "bike-demand-operations", "rows": len(rows)}))


def _socrata_daily(
    city: str,
    year: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if city == "Chicago":
        base = "https://data.cityofchicago.org/resource/v6vf-nfxy.csv"
        category = "sr_type"
    else:
        base = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"
        category = "complaint_type"
    rows: list[dict[str, Any]] = []
    source_lock: list[dict[str, Any]] = []
    for quarter_start in (1, 4, 7, 10):
        start = f"{year}-{quarter_start:02d}-01T00:00:00"
        if quarter_start == 10:
            end = f"{year + 1}-01-01T00:00:00"
        else:
            end = f"{year}-{quarter_start + 3:02d}-01T00:00:00"
        query = {
            "$select": (
                "date_trunc_ymd(created_date) as date,"
                f"{category} as category,count(*) as requests"
            ),
            "$where": f"created_date >= '{start}' and created_date < '{end}'",
            "$group": f"date,{category}",
            "$order": f"date,{category}",
            "$limit": str(SOCRATA_QUERY_LIMIT),
        }
        url = base + "?" + urllib.parse.urlencode(query)
        payload = _request(url, timeout=300)
        quarter_rows: list[dict[str, Any]] = []
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        for row in reader:
            quarter_rows.append(
                {
                    "city": city,
                    "date": row["date"][:10],
                    "category": row["category"],
                    "requests": int(row["requests"]),
                }
            )
        if len(quarter_rows) >= SOCRATA_QUERY_LIMIT:
            raise ValueError(
                f"{city} {year} Q{((quarter_start - 1) // 3) + 1} Socrata "
                f"response reached the {SOCRATA_QUERY_LIMIT}-row query limit; "
                "paginate before treating the snapshot as complete."
            )
        rows.extend(quarter_rows)
        source_lock.append(
            {
                "publisher": f"{city} open-data portal",
                "version": f"{year} Q{((quarter_start - 1) // 3) + 1} query snapshot",
                "url": url,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "records": len(quarter_rows),
                "output_fields": ["city", "date", "category", "requests"],
            }
        )
    return rows, source_lock


def build_311() -> None:
    target = PROJECTS / "cross-city-311-shift/data/raw/cross-city-311-daily.csv"
    rows = []
    source_lock: list[dict[str, Any]] = []
    for city in ("Chicago", "New York City"):
        for year in (2022, 2023):
            city_rows, city_lock = _socrata_daily(city, year)
            rows.extend(city_rows)
            source_lock.extend(city_lock)
    rows.sort(key=lambda row: (row["city"], row["date"], row["category"]))
    _write_csv(target, rows, ["city", "date", "category", "requests"])
    _write_json(
        target.with_suffix(".source-lock.json"),
        {"requests": source_lock},
    )
    print(json.dumps({"case": "cross-city-311-shift", "rows": len(rows)}))


def build_acs_pums() -> None:
    raw = PROJECTS / "census-income-ai/data/raw"
    for year in (2019, 2023):
        name = f"acs{year}-ri-person-pums.zip"
        _download(
            f"https://www2.census.gov/programs-surveys/acs/data/pums/"
            f"{year}/1-Year/csv_pri.zip",
            raw / name,
        )
    print(json.dumps({"case": "census-income-ai", "files": 2}))


def build_fire() -> None:
    target = (
        PROJECTS
        / "wildfire-mitigation-under-uncertainty/data/raw/calfire-fire-perimeters-2000-2025.csv"
    )
    base = (
        "https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/"
        "California_Historic_Fire_Perimeters/FeatureServer/0/query"
    )
    records: list[dict[str, Any]] = []
    offset = 0
    fields = [
        "OBJECTID",
        "YEAR_",
        "AGENCY",
        "UNIT_ID",
        "FIRE_NAME",
        "CAUSE",
        "C_METHOD",
        "OBJECTIVE",
        "GIS_ACRES",
        "GlobalID",
    ]
    while True:
        query = {
            "where": "YEAR_ >= 2000 AND YEAR_ <= 2025",
            "outFields": ",".join(fields),
            "returnGeometry": "false",
            "resultOffset": str(offset),
            "resultRecordCount": "500",
            "orderByFields": "OBJECTID",
            "f": "json",
        }
        payload = json.loads(
            _request(base + "?" + urllib.parse.urlencode(query), timeout=300)
        )
        features = payload.get("features", [])
        records.extend(item["attributes"] for item in features)
        if len(features) < 500:
            break
        offset += len(features)
    _write_csv(target, records, fields)
    print(json.dumps({"case": "wildfire-mitigation-under-uncertainty", "rows": len(records)}))


def _float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def build_nport(source_zip: Path) -> None:
    target = (
        PROJECTS
        / "sec-nport-filing-review/data/raw/sec-nport-2025q4-fund-risk.csv"
    )
    with open_safe_zip(source_zip, limits=SOURCE_ZIP_LIMITS) as archive:
        def table(name: str):
            with open_zip_member(archive, name) as source:
                with io.TextIOWrapper(source, encoding="utf-8-sig") as text_source:
                    yield from csv.DictReader(text_source, delimiter="\t")

        submissions = {row["ACCESSION_NUMBER"]: row for row in table("SUBMISSION.tsv")}
        registrants = {row["ACCESSION_NUMBER"]: row for row in table("REGISTRANT.tsv")}
        funds = {row["ACCESSION_NUMBER"]: row for row in table("FUND_REPORTED_INFO.tsv")}
        counts: Counter[str] = Counter()
        aggregates: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "holding_count": 0,
                "holding_value": 0.0,
                "restricted_value": 0.0,
                "level3_value": 0.0,
                "cash_like_value": 0.0,
                "top_values": [],
            }
        )
        for row in table("FUND_REPORTED_HOLDING.tsv"):
            accession = row["ACCESSION_NUMBER"]
            value = max(0.0, _float(row.get("CURRENCY_VALUE")))
            item = aggregates[accession]
            item["holding_count"] += 1
            item["holding_value"] += value
            if row.get("IS_RESTRICTED_SECURITY") == "Y":
                item["restricted_value"] += value
            if row.get("FAIR_VALUE_LEVEL") == "3":
                item["level3_value"] += value
            if row.get("ASSET_CAT") in {"STIV", "CASH"}:
                item["cash_like_value"] += value
            heap = item["top_values"]
            if len(heap) < 10:
                heapq.heappush(heap, value)
            elif value > heap[0]:
                heapq.heapreplace(heap, value)
            security = (row.get("ISSUER_CUSIP") or "").strip()
            if security:
                counts[security] += 1
        crowded_value: defaultdict[str, float] = defaultdict(float)
        for row in table("FUND_REPORTED_HOLDING.tsv"):
            security = (row.get("ISSUER_CUSIP") or "").strip()
            if security and counts[security] >= 20:
                crowded_value[row["ACCESSION_NUMBER"]] += max(
                    0.0, _float(row.get("CURRENCY_VALUE"))
                )
    rows = []
    for accession, fund in funds.items():
        metrics = aggregates.get(accession)
        if not metrics or metrics["holding_count"] < 10:
            continue
        net_assets = _float(fund.get("NET_ASSETS"))
        if net_assets <= 1_000_000:
            continue
        redemptions = sum(
            _float(fund.get(f"REDEMPTION_FLOW_MON{month}"))
            for month in (1, 2, 3)
        )
        denominator = max(metrics["holding_value"], 1.0)
        submission = submissions.get(accession, {})
        registrant = registrants.get(accession, {})
        rows.append(
            {
                "accession_number": accession,
                "report_date": submission.get("REPORT_DATE", ""),
                "series_id": fund.get("SERIES_ID", ""),
                "series_name": fund.get("SERIES_NAME", ""),
                "registrant_name": registrant.get("REGISTRANT_NAME", ""),
                "net_assets": f"{net_assets:.2f}",
                "holding_count": metrics["holding_count"],
                "top10_concentration": f"{sum(metrics['top_values']) / denominator:.10f}",
                "restricted_share": f"{metrics['restricted_value'] / denominator:.10f}",
                "fair_value_level3_share": f"{metrics['level3_value'] / denominator:.10f}",
                "cash_like_share": f"{metrics['cash_like_value'] / denominator:.10f}",
                "crowded_security_share": f"{crowded_value[accession] / denominator:.10f}",
                "three_month_redemption_share": f"{redemptions / net_assets:.10f}",
            }
        )
    rows.sort(key=lambda row: row["accession_number"])
    fields = list(rows[0])
    _write_csv(target, rows, fields)
    _write_json(
        target.with_suffix(".source-lock.json"),
        {
            "source_file": source_zip.name,
            "sha256": _sha256(source_zip),
            "bytes": source_zip.stat().st_size,
            "download_url": (
                "https://www.sec.gov/files/dera/data/form-n-port-data-sets/"
                "2025q4_nport.zip"
            ),
        },
    )
    print(json.dumps({"case": "sec-nport-filing-review", "rows": len(rows)}))


def build_social(source_csv: Path, *, accepted_terms: bool) -> None:
    if not accepted_terms:
        raise SystemExit("Pass --accept-isps-terms after reviewing the Yale ISPS terms.")
    target = (
        PROJECTS
        / "social-norm-field-experiment/data/raw/terms-compliant-treatment-aggregate.csv"
    )
    cells: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"individuals": 0, "voters": 0, "households": set()}
    )
    observations: dict[str, list[tuple[str, int]]] = defaultdict(list)
    source_records = 0
    with source_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            source_records += 1
            treatment = row["treatment"].strip()
            prior = "prior_primary_voter" if row.get("p2004", "").strip().lower() == "yes" else "not_prior_primary_voter"
            voted = int(row.get("voted", "").strip().lower() == "yes")
            cell = cells[(treatment, prior)]
            cell["individuals"] += 1
            cell["voters"] += voted
            cell["households"].add(row["hh_id"])
            observations[treatment].append((row["hh_id"], voted))
    rows = []
    for (treatment, prior), cell in sorted(cells.items()):
        rows.append(
            {
                "treatment": treatment,
                "prior_turnout_stratum": prior,
                "individuals": cell["individuals"],
                "households": len(cell["households"]),
                "voters": cell["voters"],
                "turnout_rate": f"{cell['voters'] / cell['individuals']:.10f}",
            }
        )
    _write_csv(
        target,
        rows,
        [
            "treatment",
            "prior_turnout_stratum",
            "individuals",
            "households",
            "voters",
            "turnout_rate",
        ],
    )
    control = observations["Control"]
    control_mean = sum(value for _, value in control) / len(control)
    effects = []
    for treatment in sorted(name for name in observations if name != "Control"):
        treated = observations[treatment]
        treated_mean = sum(value for _, value in treated) / len(treated)
        n0, n1 = len(control), len(treated)
        household_scores: dict[tuple[str, str], list[float]] = defaultdict(
            lambda: [0.0, 0.0]
        )
        for household, value in control:
            household_scores[("Control", household)][0] += value - control_mean
        for household, value in treated:
            residual = value - treated_mean
            household_scores[(treatment, household)][0] += residual
            household_scores[(treatment, household)][1] += residual
        meat = [[0.0, 0.0], [0.0, 0.0]]
        for score0, score1 in household_scores.values():
            meat[0][0] += score0 * score0
            meat[0][1] += score0 * score1
            meat[1][0] += score1 * score0
            meat[1][1] += score1 * score1
        bread = [
            [1 / n0, -1 / n0],
            [-1 / n0, 1 / n0 + 1 / n1],
        ]
        middle = [
            [
                sum(bread[row][k] * meat[k][column] for k in range(2))
                for column in range(2)
            ]
            for row in range(2)
        ]
        variance = sum(middle[1][k] * bread[1][k] for k in range(2))
        clusters = len(household_scores)
        correction = (clusters / (clusters - 1)) * ((n0 + n1 - 1) / (n0 + n1 - 2))
        standard_error = math.sqrt(max(0.0, variance * correction))
        difference = treated_mean - control_mean
        effects.append(
            {
                "treatment": treatment,
                "control": "Control",
                "treated_individuals": n1,
                "control_individuals": n0,
                "household_clusters": clusters,
                "treated_turnout_rate": treated_mean,
                "control_turnout_rate": control_mean,
                "intent_to_treat_difference": difference,
                "household_cluster_robust_standard_error": standard_error,
                "confidence_interval_95": [
                    difference - 1.96 * standard_error,
                    difference + 1.96 * standard_error,
                ],
            }
        )
    _write_json(
        target.parent / "cluster-robust-itt.json",
        {
            "estimand": "individual-level intent-to-treat difference in turnout",
            "variance_estimator": "OLS sandwich variance clustered by household",
            "source_rows_used": sum(len(group) for group in observations.values()),
            "effects": effects,
        },
    )
    _write_json(
        target.parent / "external-source-lock.json",
        {
            "dataset": "Yale ISPS D001 individual-level replication file",
            "source_records": source_records,
            "file_sha256": _sha256(source_csv),
            "file_bytes": source_csv.stat().st_size,
            "raw_redistribution": "not_redistributed_by_repository",
            "repository_storage": "non_identifying_aggregate_only",
            "landing_page": "https://doi.org/10.60600/YU/CGMWNW",
            "download_url": (
                "https://isps-yard-aws-s3-bucket.s3.us-east-2.amazonaws.com/"
                "published/15d48af8-e38e-4dd0-ace9-62f90826963a/"
                "GerberGreenLarimer_APSR_2008_social_pressure.csv"
            ),
            "terms_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        },
    )
    print(json.dumps({"case": "social-norm-field-experiment", "rows": len(rows)}))


def _nhis_mortality(path: Path) -> dict[str, dict[str, str]]:
    result = {}
    with path.open("r", encoding="ascii") as handle:
        for line in handle:
            result[line[0:14]] = {
                "eligstat": line[14:15].strip(),
                "mortstat": line[15:16].strip(),
                "ucod_leading": line[16:19].strip(),
                "dodyear": line[22:26].strip(),
            }
    return result


def build_nhis() -> None:
    target = (
        PROJECTS
        / "population-health-survival/data/raw/nhis-2016-2017-linked-mortality-extract.csv"
    )
    rows = []
    source_lock: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="nhis-source-") as directory:
        temp_root = Path(directory)
        for year in (2016, 2017):
            survey = temp_root / f"samadult{year}.zip"
            mortality = temp_root / f"mort{year}.dat"
            survey_url = (
                "https://ftp.cdc.gov/pub/health_statistics/nchs/datasets/NHIS/"
                f"{year}/samadultcsv.zip"
            )
            mortality_url = (
                "https://ftp.cdc.gov/pub/health_statistics/NCHS/datalinkage/"
                f"linked_mortality/NHIS_{year}_MORT_2019_PUBLIC.dat"
            )
            _download(survey_url, survey)
            _download(mortality_url, mortality)
            source_lock.extend(
                {
                    "name": path.name,
                    "url": url,
                    "sha256": _sha256(path),
                    "bytes": path.stat().st_size,
                }
                for path, url in ((survey, survey_url), (mortality, mortality_url))
            )
            linked = _nhis_mortality(mortality)
            with open_safe_zip(survey, limits=SOURCE_ZIP_LIMITS) as archive:
                members = [
                    item.filename for item in archive.infolist() if not item.is_dir()
                ]
                if len(members) != 1:
                    raise ValueError(
                        f"NHIS survey ZIP must contain exactly one data member: {survey.name}"
                    )
                with open_zip_member(archive, members[0]) as source:
                    reader = csv.DictReader(io.TextIOWrapper(source, encoding="utf-8-sig"))
                    for row in reader:
                        publicid = (
                            str(row["SRVY_YR"]).zfill(4)
                            + str(row["HHX"]).zfill(6)
                            + str(row["FMX"]).zfill(2)
                            + str(row["FPX"]).zfill(2)
                        )
                        mort = linked.get(publicid)
                        if not mort or mort["eligstat"] != "1":
                            continue
                        died_within_two_years = int(
                            mort["mortstat"] == "1"
                            and mort["dodyear"].isdigit()
                            and int(mort["dodyear"]) <= year + 2
                        )
                        rows.append(
                            {
                                "publicid": publicid,
                                "cohort_year": year,
                                "age": row.get("AGE_P", ""),
                                "sex": row.get("SEX", ""),
                                "race": row.get("RACERPI2", ""),
                                "survey_weight": row.get("WTFA_SA", row.get("WTIA_SA", "")),
                                "hypertension": row.get("HYPEV", ""),
                                "diabetes": row.get("DIBEV1", ""),
                                "ever_smoked": row.get("SMKEV", ""),
                                "current_smoking": (
                                    row.get("SMKNOW", "")
                                    or (
                                        "not_applicable_never_smoked"
                                        if row.get("SMKEV") == "2"
                                        else "missing"
                                    )
                                ),
                                "death_within_two_years": died_within_two_years,
                            }
                        )
    rows.sort(key=lambda row: (row["cohort_year"], row["publicid"]))
    _write_csv(target, rows, list(rows[0]))
    _write_json(target.with_suffix(".source-lock.json"), {"files": source_lock})
    print(json.dumps({"case": "population-health-survival", "rows": len(rows)}))


def _acs_tract(year: int) -> tuple[dict[str, dict[str, str]], list[dict[str, Any]]]:
    """Read official table-based files without relying on an API key.

    The 2018-2020 releases live in the Census prototype directory.  Only
    Massachusetts tract rows are retained in memory; national files are
    downloaded to a temporary directory solely to compute a source hash and
    create the minimized tract panel.
    """

    tables = ("b01003", "b17001", "b19013", "b25064", "b23025")
    combined: dict[str, dict[str, str]] = defaultdict(dict)
    source_lock: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix=f"acs-{year}-") as directory:
        temp_root = Path(directory)
        for table in tables:
            url = (
                "https://www2.census.gov/programs-surveys/acs/summary_file/"
                f"{year}/prototype/5YRData/acsdt5y{year}-{table}.dat"
            )
            source = temp_root / f"acsdt5y{year}-{table}.dat"
            _download(url, source)
            source_lock.append(
                {
                    "name": source.name,
                    "url": url,
                    "sha256": _sha256(source),
                    "bytes": source.stat().st_size,
                }
            )
            with source.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle, delimiter="|"):
                    geography = row.get("GEO_ID") or row.get("#GEO_ID", "")
                    if geography.startswith("1400000US25"):
                        combined[geography.removeprefix("1400000US")].update(row)
    return dict(combined), source_lock


def _acs_value(row: dict[str, str], table: str, line: str) -> str:
    """Normalize the 2018 prototype and 2019 table-based column conventions."""

    return row.get(f"{table}_E{line}", row.get(f"{table}_{line}E", ""))


ACS_SPECIAL_VALUE_MEANINGS = {
    "-222222222": "margin_of_error_insufficient_sample",
    "-333333333": "margin_of_error_open_ended_median",
    "-555555555": "margin_of_error_not_applicable_controlled_estimate",
    "-666666666": "estimate_not_computed",
    "-888888888": "estimate_not_applicable_or_unavailable",
    "-999999999": "estimate_not_displayable_insufficient_cases",
}


def _normalized_acs_estimate(
    row: dict[str, str],
    table: str,
    line: str,
) -> tuple[str, str]:
    """Return an analytical value plus an explicit source-special-value code."""

    value = _acs_value(row, table, line).strip()
    if value in ACS_SPECIAL_VALUE_MEANINGS:
        return "", value
    if not value:
        return "", "source_null"
    try:
        number = float(value)
    except ValueError as error:
        raise ValueError(
            f"ACS {table} line {line} returned a non-numeric estimate: {value!r}"
        ) from error
    if not math.isfinite(number):
        return "", "source_non_finite"
    return value, ""


def _lodes_jobs(year: int) -> tuple[dict[str, int], dict[str, Any]]:
    url = (
        "https://lehd.ces.census.gov/data/lodes/LODES8/ma/wac/"
        f"ma_wac_S000_JT00_{year}.csv.gz"
    )
    compressed = _request(url, timeout=300)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as archive:
        decompressed = archive.read(MAX_GZIP_UNCOMPRESSED_BYTES + 1)
    if len(decompressed) > MAX_GZIP_UNCOMPRESSED_BYTES:
        raise ValueError(
            "LODES gzip content exceeds "
            f"{MAX_GZIP_UNCOMPRESSED_BYTES} decompressed bytes."
        )
    payload = decompressed.decode("utf-8")
    totals: Counter[str] = Counter()
    for row in csv.DictReader(io.StringIO(payload)):
        totals[row["w_geocode"][:11]] += int(row["C000"])
    return dict(totals), {
        "publisher": "U.S. Census Bureau LEHD",
        "version": f"LODES8 Massachusetts WAC S000 JT00 {year}",
        "name": f"ma_wac_S000_JT00_{year}.csv.gz",
        "url": url,
        "sha256": hashlib.sha256(compressed).hexdigest(),
        "bytes": len(compressed),
        "decompressed_sha256": hashlib.sha256(decompressed).hexdigest(),
        "decompressed_bytes": len(decompressed),
        "output_fields": ["geoid", "year", "workplace_jobs"],
    }


def _validate_xlsx_archive(archive: Any) -> None:
    validate_zip_archive(archive, limits=XLSX_LIMITS)


def _read_xlsx_member(
    archive: Any,
    name: str,
    *,
    max_bytes: int = MAX_XLSX_MEMBER_BYTES,
) -> bytes:
    return read_zip_member(archive, name, maximum_bytes=max_bytes)


def _safe_xml_root(payload: bytes) -> Any:
    try:
        from defusedxml import ElementTree as safe_element_tree
    except ImportError as error:
        raise SystemExit(
            "defusedxml is required for maintenance-only XLSX source builds; "
            "install requirements-maintenance.txt."
        ) from error
    return safe_element_tree.fromstring(
        payload,
        forbid_dtd=True,
        forbid_entities=True,
        forbid_external=True,
    )


def _xlsx_first_sheet(path: Path) -> list[list[str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    namespace = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with open_safe_zip(path, limits=XLSX_LIMITS) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = _safe_xml_root(
                _read_xlsx_member(archive, "xl/sharedStrings.xml")
            )
            for item in root.findall("m:si", namespace):
                strings.append(
                    "".join(
                        node.text or ""
                        for node in item.iter()
                        if node.tag.endswith("}t")
                    )
                )
        sheet = _safe_xml_root(
            _read_xlsx_member(archive, "xl/worksheets/sheet1.xml")
        )
    rows = []
    for row in sheet.findall(".//m:sheetData/m:row", namespace):
        cells = []
        for cell in row.findall("m:c", namespace):
            value = cell.find("m:v", namespace)
            text = "" if value is None else value.text or ""
            if cell.attrib.get("t") == "s" and text:
                text = strings[int(text)]
            cells.append(text)
        rows.append(cells)
    return rows


def build_opportunity_zone() -> None:
    target = (
        PROJECTS
        / "opportunity-zone-policy-evaluation/data/raw/massachusetts-qoz-tract-panel.csv"
    )
    workbook_url = (
        "https://www.cdfifund.gov/sites/cdfi/files/documents/"
        "designated-qozs.12.14.18.xlsx"
    )
    with tempfile.TemporaryDirectory(prefix="qoz-source-") as directory:
        workbook = Path(directory) / "designated-qozs.xlsx"
        _download(workbook_url, workbook)
        table = _xlsx_first_sheet(workbook)
        header_index = next(
            index
            for index, row in enumerate(table)
            if any("Census Tract" in value for value in row)
        )
        header = table[header_index]
        qozs = set()
        for row in table[header_index + 1 :]:
            values = dict(zip(header, row, strict=False))
            state = next(
                (
                    value
                    for key, value in values.items()
                    if key.strip().endswith("State") or key.strip() == "State/Territory"
                ),
                "",
            )
            tract = next(
                (
                    value
                    for key, value in values.items()
                    if "Census Tract" in key
                ),
                "",
            )
            digits = "".join(character for character in tract if character.isdigit())
            if state in {"Massachusetts", "MA"} and digits:
                qozs.add(digits.zfill(11))
        acs_with_lock = {year: _acs_tract(year) for year in (2018, 2019)}
        acs = {year: payload[0] for year, payload in acs_with_lock.items()}
        acs_source_lock = [
            source
            for payload in acs_with_lock.values()
            for source in payload[1]
        ]
        jobs_with_lock = {year: _lodes_jobs(year) for year in (2018, 2019)}
        jobs = {year: payload[0] for year, payload in jobs_with_lock.items()}
        lodes_source_lock = [
            payload[1] for _, payload in sorted(jobs_with_lock.items())
        ]
        geoids = sorted(set(acs[2018]) & set(acs[2019]))
        rows = []
        acs_special_value_counts: Counter[tuple[str, str]] = Counter()
        acs_variables = {
            "population": ("B01003", "001"),
            "poverty_universe": ("B17001", "001"),
            "poverty_count": ("B17001", "002"),
            "median_household_income": ("B19013", "001"),
            "median_gross_rent": ("B25064", "001"),
            "civilian_labor_force": ("B23025", "003"),
            "unemployed": ("B23025", "005"),
        }
        for geoid in geoids:
            for year in (2018, 2019):
                acs_row = acs[year][geoid]
                output: dict[str, Any] = {
                    "geoid": geoid,
                    "year": year,
                    "qoz_2018": int(geoid in qozs),
                }
                for field, (table_id, line) in acs_variables.items():
                    value, source_code = _normalized_acs_estimate(
                        acs_row,
                        table_id,
                        line,
                    )
                    output[field] = value
                    output[f"{field}_source_code"] = source_code
                    if source_code:
                        acs_special_value_counts[(field, source_code)] += 1
                output["workplace_jobs"] = jobs[year].get(geoid, 0)
                rows.append(output)
        _write_csv(target, rows, list(rows[0]))
        _write_json(
            target.with_suffix(".source-lock.json"),
            {
                "qoz_workbook": {
                    "url": workbook_url,
                    "sha256": _sha256(workbook),
                    "bytes": workbook.stat().st_size,
                },
                "acs_years": [2018, 2019],
                "acs_files": acs_source_lock,
                "acs_special_value_policy": {
                    "status": "normalized_to_missing_before_analysis",
                    "official_reference": (
                        "https://www.census.gov/data/developers/data-sets/"
                        "acs-1year/notes-on-acs-estimate-and-annotation-values.html"
                    ),
                    "code_meanings": ACS_SPECIAL_VALUE_MEANINGS,
                    "counts": [
                        {"field": field, "source_code": code, "count": count}
                        for (field, code), count in sorted(
                            acs_special_value_counts.items()
                        )
                    ],
                },
                "lodes_years": [2018, 2019],
                "lodes_files": lodes_source_lock,
            },
        )
    print(json.dumps({"case": "opportunity-zone-policy-evaluation", "rows": len(rows)}))


def _nhanes_mortality(path: Path) -> dict[int, dict[str, Any]]:
    result = {}
    with path.open("r", encoding="ascii") as handle:
        for line in handle:
            seqn = line[0:6].strip()
            if not seqn:
                continue
            result[int(seqn)] = {
                "eligstat": line[14:15].strip(),
                "mortstat": line[15:16].strip(),
                "permth_int": line[42:45].strip(),
            }
    return result


def _normalized_sas_numeric(value: Any) -> tuple[float | str, str]:
    """Normalize XPORT missing values and decoder subnormal zero artifacts."""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return "", "missing_or_non_numeric"
    if not math.isfinite(number):
        return "", "missing_or_non_finite"
    if 0 < abs(number) < 1e-70:
        return 0.0, "xport_subnormal_normalized_to_zero"
    return number, ""


def build_nhanes() -> None:
    try:
        import pandas as pd
    except ImportError as error:
        raise SystemExit("pandas is required only for the NHANES XPT source build") from error
    target = (
        PROJECTS
        / "nhanes-population-transportability/data/raw/nhanes-36-month-mortality-cohorts.csv"
    )
    specifications = [
        (
            "2011-2012",
            "2011",
            "DEMO_G",
            "NHANES_2011_2012_MORT_2019_PUBLIC.dat",
        ),
        (
            "2015-2016",
            "2015",
            "DEMO_I",
            "NHANES_2015_2016_MORT_2019_PUBLIC.dat",
        ),
    ]
    rows = []
    source_lock: list[dict[str, Any]] = []
    normalization_counts: Counter[tuple[str, str]] = Counter()
    with tempfile.TemporaryDirectory(prefix="nhanes-source-") as directory:
        temp_root = Path(directory)
        for cohort, public_year, stem, mortality_name in specifications:
            xpt_url = (
                "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/"
                f"{public_year}/DataFiles/{stem}.xpt"
            )
            mortality_url = (
                "https://ftp.cdc.gov/pub/health_statistics/NCHS/datalinkage/"
                f"linked_mortality/{mortality_name}"
            )
            xpt = temp_root / f"{stem}.XPT"
            mortality_path = temp_root / mortality_name
            _download(xpt_url, xpt)
            _download(mortality_url, mortality_path)
            source_lock.extend(
                {
                    "name": path.name,
                    "url": url,
                    "sha256": _sha256(path),
                    "bytes": path.stat().st_size,
                }
                for path, url in ((xpt, xpt_url), (mortality_path, mortality_url))
            )
            mortality = _nhanes_mortality(mortality_path)
            frame = pd.read_sas(xpt, format="xport", encoding="utf-8")
            for record in frame.to_dict(orient="records"):
                seqn = int(record["SEQN"])
                mort = mortality.get(seqn)
                age = _float(record.get("RIDAGEYR"))
                if not mort or mort["eligstat"] != "1" or age < 18:
                    continue
                followup = int(mort["permth_int"]) if mort["permth_int"].isdigit() else 0
                if mort["mortstat"] == "0" and followup < 36:
                    continue
                event = int(mort["mortstat"] == "1" and 0 < followup <= 36)
                normalized_values = {}
                for output_field, source_field in (
                    ("poverty_income_ratio", "INDFMPIR"),
                    ("interview_weight", "WTINT2YR"),
                    ("exam_weight", "WTMEC2YR"),
                ):
                    value, normalization = _normalized_sas_numeric(
                        record.get(source_field)
                    )
                    normalized_values[output_field] = value
                    if normalization:
                        normalization_counts[(output_field, normalization)] += 1
                rows.append(
                    {
                        "seqn": seqn,
                        "cohort": cohort,
                        "age": int(age),
                        "sex": int(_float(record.get("RIAGENDR"))),
                        "race_ethnicity": int(_float(record.get("RIDRETH3"))),
                        **normalized_values,
                        "stratum": int(_float(record.get("SDMVSTRA"))),
                        "psu": int(_float(record.get("SDMVPSU"))),
                        "followup_months": followup,
                        "death_within_36_months": event,
                    }
                )
    rows.sort(key=lambda row: (row["cohort"], row["seqn"]))
    _write_csv(target, rows, list(rows[0]))
    _write_json(
        target.with_suffix(".source-lock.json"),
        {
            "files": source_lock,
            "sas_numeric_normalization": {
                "policy": (
                    "Non-finite values become explicit missing values; positive or "
                    "negative XPORT decoder subnormals below 1e-70 become zero."
                ),
                "counts": [
                    {"field": field, "normalization": reason, "count": count}
                    for (field, reason), count in sorted(normalization_counts.items())
                ],
            },
        },
    )
    print(json.dumps({"case": "nhanes-population-transportability", "rows": len(rows)}))


def build_mbta() -> None:
    target = PROJECTS / "spatial-equity-planning/data/raw/mbta-rapid-transit-stops.json"
    query = urllib.parse.urlencode({"filter[route_type]": "0,1"})
    payload = json.loads(_request(f"https://api-v3.mbta.com/stops?{query}"))
    minimized = {
        "source": "MBTA V3 API",
        "retrieved_at": datetime.now().astimezone().isoformat(),
        "data": [
            {
                "id": item["id"],
                "name": item["attributes"].get("name"),
                "latitude": item["attributes"].get("latitude"),
                "longitude": item["attributes"].get("longitude"),
                "location_type": item["attributes"].get("location_type"),
            }
            for item in payload.get("data", [])
            if item["attributes"].get("latitude") is not None
        ],
    }
    _write_json(target, minimized)
    print(json.dumps({"case": "spatial-equity-planning", "stops": len(minimized["data"])}))


BUILDERS = {
    "bike": lambda args: build_bike(),
    "311": lambda args: build_311(),
    "acs": lambda args: build_acs_pums(),
    "fire": lambda args: build_fire(),
    "nport": lambda args: build_nport(
        _required_input(args.nport_zip, "--nport-zip")
    ),
    "social": lambda args: build_social(
        _required_input(args.social_csv, "--social-csv"),
        accepted_terms=args.accept_isps_terms,
    ),
    "nhis": lambda args: build_nhis(),
    "qoz": lambda args: build_opportunity_zone(),
    "nhanes": lambda args: build_nhanes(),
    "mbta": lambda args: build_mbta(),
}


def _required_input(value: Path | None, option: str) -> Path:
    if value is None:
        raise SystemExit(f"{option} is required for this source build.")
    resolved = value.expanduser().resolve()
    if not resolved.is_file():
        raise SystemExit(f"{option} must point to an existing file: {resolved}")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=sorted(BUILDERS))
    parser.add_argument(
        "--nport-zip",
        type=Path,
    )
    parser.add_argument(
        "--social-csv",
        type=Path,
    )
    parser.add_argument("--accept-isps-terms", action="store_true")
    args = parser.parse_args()
    BUILDERS[args.case](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
