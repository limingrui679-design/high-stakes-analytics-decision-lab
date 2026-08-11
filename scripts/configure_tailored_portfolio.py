#!/usr/bin/env python3
"""Materialize the public, school-neutral fifteen-case portfolio metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "examples/real-data-cases/projects"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _output_fields(root: Path) -> list[str]:
    dictionary_path = root / "data/data-dictionary.json"
    if not dictionary_path.exists():
        return []
    dictionary = json.loads(dictionary_path.read_text(encoding="utf-8"))
    fields = dictionary.get("fields", {})
    return list(fields) if isinstance(fields, dict) else []


def _upstream_artifact(item: dict) -> dict:
    artifact = {
        key: item[key]
        for key in (
            "name",
            "path",
            "url",
            "sha256",
            "bytes",
            "decompressed_sha256",
            "decompressed_bytes",
            "records",
        )
        if key in item
    }
    artifact["hash_algorithm"] = "sha256"
    return artifact


def _source_record(
    *,
    source_id: str,
    publisher: str,
    version: str,
    license_name: str,
    license_url: str,
    url: str,
    artifacts: list[dict],
    output_fields: list[str],
) -> dict:
    if not artifacts:
        raise ValueError(f"Structured source {source_id} has no hash-locked artifact.")
    return {
        "source_id": source_id,
        "publisher": publisher,
        "version": version,
        "license": license_name,
        "license_url": license_url,
        "url": url,
        "artifacts": [_upstream_artifact(item) for item in artifacts],
        "output_fields": output_fields,
    }


def _structured_sources(root: Path, manifest: dict) -> list[dict]:
    """Describe each upstream source and the output fields it supports."""

    project_id = manifest["project_id"]
    output_fields = _output_fields(root)
    raw_files = manifest["raw_files"]
    lock_paths = [
        root / item["path"]
        for item in raw_files
        if item["path"].endswith(".source-lock.json")
    ]
    locks = [json.loads(path.read_text(encoding="utf-8")) for path in lock_paths]

    if project_id == "cross-city-311-shift":
        requests = locks[0].get("requests", []) if locks else []
        chicago = [item for item in requests if "Chicago" in item.get("publisher", "")]
        new_york = [item for item in requests if "New York" in item.get("publisher", "")]
        return [
            _source_record(
                source_id="chicago-311-api-2022-2023",
                publisher="City of Chicago",
                version="Quarterly API query snapshots for 2022-2023",
                license_name="Chicago Data Portal terms",
                license_url="https://www.chicago.gov/city/en/narr/foia/data_disclaimer.html",
                url=manifest["landing_page"],
                artifacts=chicago,
                output_fields=output_fields,
            ),
            _source_record(
                source_id="nyc-311-api-2022-2023",
                publisher="City of New York",
                version="Quarterly API query snapshots for 2022-2023",
                license_name="NYC Open Data terms of use",
                license_url="https://opendata.cityofnewyork.us/overview/#termsofuse",
                url=manifest["additional_sources"][0],
                artifacts=new_york,
                output_fields=output_fields,
            ),
        ]

    if project_id == "opportunity-zone-policy-evaluation":
        lock = locks[0] if locks else {}
        return [
            _source_record(
                source_id="cdfi-designated-qoz-2018",
                publisher="U.S. Department of the Treasury CDFI Fund",
                version="Designated Qualified Opportunity Zones, 2018-12-14",
                license_name="U.S. Government public data",
                license_url=manifest["license_url"],
                url=manifest["landing_page"],
                artifacts=[lock["qoz_workbook"]] if lock.get("qoz_workbook") else [],
                output_fields=["geoid", "qoz_2018"],
            ),
            _source_record(
                source_id="census-acs-5year-2018-2019",
                publisher="U.S. Census Bureau",
                version="2018 and 2019 ACS five-year table-based files",
                license_name="U.S. Government public data",
                license_url="https://www.census.gov/about/policies/open-gov/open-data.html",
                url="https://www.census.gov/programs-surveys/acs/data/summary-file.html",
                artifacts=lock.get("acs_files", []),
                output_fields=[
                    "geoid",
                    "year",
                    "population",
                    "population_source_code",
                    "poverty_universe",
                    "poverty_universe_source_code",
                    "poverty_count",
                    "poverty_count_source_code",
                    "median_household_income",
                    "median_household_income_source_code",
                    "median_gross_rent",
                    "median_gross_rent_source_code",
                    "civilian_labor_force",
                    "civilian_labor_force_source_code",
                    "unemployed",
                    "unemployed_source_code",
                ],
            ),
            _source_record(
                source_id="census-lodes8-ma-wac-2018-2019",
                publisher="U.S. Census Bureau LEHD",
                version="LODES8 Massachusetts WAC S000 JT00, 2018-2019",
                license_name="U.S. Government public data",
                license_url="https://www.census.gov/about/policies/open-gov/open-data.html",
                url="https://lehd.ces.census.gov/data/",
                artifacts=lock.get("lodes_files", []),
                output_fields=["geoid", "year", "workplace_jobs"],
            ),
        ]

    if project_id in {
        "population-health-survival",
        "nhanes-population-transportability",
    }:
        files = locks[0].get("files", []) if locks else []
        mortality = [item for item in files if "MORT" in item.get("name", "").upper()]
        survey = [item for item in files if item not in mortality]
        identifier = "nhis" if project_id.startswith("population") else "nhanes"
        survey_fields = [field for field in output_fields if not field.startswith("death_") and field != "followup_months"]
        mortality_fields = [
            field
            for field in output_fields
            if field.startswith("death_") or field == "followup_months"
        ]
        return [
            _source_record(
                source_id=f"cdc-{identifier}-survey-files",
                publisher="U.S. CDC National Center for Health Statistics",
                version=manifest["version"],
                license_name=manifest["license"],
                license_url=manifest["license_url"],
                url=manifest["landing_page"],
                artifacts=survey,
                output_fields=survey_fields,
            ),
            _source_record(
                source_id=f"cdc-{identifier}-linked-mortality-files",
                publisher="U.S. CDC National Center for Health Statistics",
                version="2019 public-use linked mortality release",
                license_name=manifest["license"],
                license_url=manifest["license_url"],
                url="https://www.cdc.gov/nchs/data-linkage/mortality-public.htm",
                artifacts=mortality,
                output_fields=mortality_fields,
            ),
        ]

    if project_id == "spatial-equity-planning":
        census = [item for item in raw_files if "mbta" not in item["path"]]
        mbta = [item for item in raw_files if "mbta" in item["path"]]
        return [
            _source_record(
                source_id="census-acs-gazetteer-ma-2023",
                publisher="U.S. Census Bureau",
                version="2023 ACS five-year tables and tract Gazetteer",
                license_name="U.S. Government open data",
                license_url=manifest["license_url"],
                url=manifest["landing_page"],
                artifacts=census,
                output_fields=output_fields,
            ),
            _source_record(
                source_id="mbta-v3-rapid-transit-stops",
                publisher="Massachusetts Bay Transportation Authority",
                version="MBTA V3 rapid-transit stop snapshot",
                license_name="MBTA open data",
                license_url="https://www.mbta.com/policies/developers-terms",
                url=manifest["additional_sources"][0],
                artifacts=mbta,
                output_fields=[
                    "mbta_stops",
                    "population_weighted_nearest_stop_km",
                    "high_poverty_weighted_nearest_stop_km",
                ],
            ),
        ]

    return [
        _source_record(
            source_id=manifest["source_id"],
            publisher=manifest["publisher"],
            version=manifest["version"],
            license_name=manifest["license"],
            license_url=manifest["license_url"],
            url=manifest["landing_page"],
            artifacts=raw_files,
            output_fields=output_fields,
        )
    ]


def upgrade_source_manifests() -> None:
    for path in sorted(PROJECTS.glob("*/source-manifest.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["schema_version"] = "1.1"
        manifest["sources"] = _structured_sources(path.parent, manifest)
        write_json(path, manifest)


def parameters(project_id: str, values: dict, boundary: str) -> dict:
    return {
        "project_id": project_id,
        "analysis_seed": 20260810,
        "parameters": values,
        "parameter_register": [
            {
                "parameter": "/".join(values),
                "source_id": "case-specific-analysis-protocol",
                "status": "pre-specified exploratory design",
                "approved_by": "repository author self-review",
                "boundary": boundary,
            }
        ],
    }


SPECS = {
    "population-health-survival": {
        "title": "Population Health Risk Transport Across NHIS Cohorts",
        "source_id": "cdc-nhis-2016-2017-linked-mortality",
        "publisher": "U.S. Centers for Disease Control and Prevention, National Center for Health Statistics",
        "landing_page": "https://www.cdc.gov/nchs/data-linkage/mortality-public.htm",
        "version": "NHIS 2016 and 2017 Sample Adult files linked to 2019 public-use mortality",
        "license": "U.S. Government public-use data",
        "license_url": "https://www.cdc.gov/nchs/data-linkage/mortality-public.htm",
        "redistribution": "Public-use minimized extract; NCHS linkage and disclosure rules remain controlling.",
        "expected_rows": 58754,
        "grain": "one NHIS sampled adult linked to mortality status",
        "raw": ["nhis-2016-2017-linked-mortality-extract.csv", "nhis-2016-2017-linked-mortality-extract.source-lock.json"],
        "question": "Do simple population-risk cells developed in NHIS 2016 retain discrimination and calibration in the 2017 linked-mortality cohort?",
        "boundary": "Population-risk validation only; no individual diagnosis, treatment, or clinical deployment.",
        "result": "The 2017 temporal test yields an AUC of 0.846 and weighted two-year mortality of 2.32% across 58,754 linked adults.",
        "methods": "Survey weighting, temporal validation, AUC, Brier score, calibration, and bounded review protocols.",
        "config": {"development_cohort": 2016, "validation_cohort": 2017, "review_shares": [0.1, 0.2, 0.3]},
    },
    "bike-demand-operations": {
        "title": "Jersey City Bike Demand and Rebalancing Evidence",
        "source_id": "citibike-jc-2021-derived-station-hour",
        "publisher": "Citi Bike",
        "landing_page": "https://citibikenyc.com/system-data",
        "version": "Jersey City trip history, January-December 2021; derived station-hour aggregate",
        "license": "Citi Bike Data Sharing Policy",
        "license_url": "https://citibikenyc.com/data-sharing-policy",
        "redistribution": "Only the derived station-hour aggregate is stored; source trip archives are not redistributed.",
        "expected_rows": 17906,
        "grain": "one station-hour-month aggregate",
        "raw": ["citibike-jc-2021-station-hour.csv", "citibike-jc-2021-station-hour.source-lock.json"],
        "question": "Can station-hour history improve held-out pickup forecasts, and which fixed-budget rebalancing scenario deserves a bounded operations pilot?",
        "boundary": "Rebalancing outcomes are modeled; no stockout, routing, labor, or achieved-service claim.",
        "result": "Held-out station-hour MAE is 0.69 pickups/day, a 33.1% improvement over the hour-only baseline.",
        "methods": "Temporal holdout, weighted MAE, observed pickup-return imbalance, and fixed-budget scenario comparison.",
        "config": {"development_end": "2021-09", "test_start": "2021-10", "modeled_daily_rebalancing_units": 250, "review_station_hour_counts": [0, 10, 25]},
    },
    "census-income-ai": {
        "title": "ACS Employment AI Temporal Transport and Audit",
        "source_id": "census-acs-pums-ri-2019-2023",
        "publisher": "U.S. Census Bureau",
        "landing_page": "https://www.census.gov/programs-surveys/acs/microdata.html",
        "version": "Rhode Island ACS 1-year PUMS person files, 2019 and 2023",
        "license": "U.S. Government open data",
        "license_url": "https://www.census.gov/about/policies/open-gov/open-data.html",
        "redistribution": "Public Census microdata; repository stores official state ZIP files.",
        "expected_rows": 12469,
        "grain": "one working-age ACS PUMS person record",
        "raw": ["acs2019-ri-person-pums.zip", "acs2023-ri-person-pums.zip"],
        "question": "How well does a protected-attribute-excluded employment model developed on 2019 PUMS transport to 2023?",
        "boundary": "No eligibility, hiring, credit, benefits, or other consequential action.",
        "result": "The untouched 2023 temporal test yields an AUC of 0.640 and a weighted Brier score of 0.158.",
        "methods": "Survey-weighted grouped-rate model, temporal AUC/Brier/calibration, and protected-attribute audit slices.",
        "config": {"development_year": 2019, "test_year": 2023, "model_fields": ["age_band", "education_band", "worker_class", "puma"], "audit_only_fields": ["sex", "race", "hispanic_origin"]},
    },
    "sec-nport-filing-review": {
        "title": "SEC N-PORT Liquidity and Crowding Filing Review",
        "source_id": "sec-nport-2025q4-minimized-fund-risk",
        "publisher": "U.S. Securities and Exchange Commission",
        "landing_page": "https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets",
        "version": "Form N-PORT Data Set 2025 Q4, minimized to fund-level review indicators",
        "license": "U.S. Government public data",
        "license_url": "https://www.sec.gov/os/accessing-edgar-data",
        "redistribution": "Public filing data; minimized derived fund-level table is stored with source hash.",
        "expected_rows": 11747,
        "grain": "one fund filing snapshot",
        "raw": ["sec-nport-2025q4-fund-risk.csv", "sec-nport-2025q4-fund-risk.source-lock.json"],
        "question": "Which transparent concentration, liquidity, and redemption indicators should trigger targeted filing review?",
        "boundary": "Filing review only; no expected-return, suitability, fund-quality, or investment recommendation.",
        "result": "Across 11,747 reviewed filings, median top-10 holding concentration is 34.5% and the 90th-percentile Level-3 share is 0.2%.",
        "methods": "Filing extraction, percentile indicators, transparent composite score, and review-capacity trade-offs.",
        "config": {"review_shares": [0.05, 0.1, 0.2], "high_risk_reference_share": 0.1, "score_rule": "equal_weight_percentile_mean"},
    },
    "cross-city-311-shift": {
        "title": "Cross-City 311 Distribution Shift and Transfer Gate",
        "source_id": "chicago-nyc-311-2022-2023",
        "publisher": "City of Chicago and City of New York",
        "landing_page": "https://data.cityofchicago.org/Service-Requests/311-Service-Requests-Request-and-Response-Times/v6vf-nfxy",
        "additional_sources": ["https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9"],
        "version": "Daily source-category aggregates, 2022-2023",
        "license": "Municipal open-data terms",
        "license_url": "https://www.chicago.gov/city/en/narr/foia/data_disclaimer.html",
        "redistribution": "Official API aggregates; local source definitions remain controlling.",
        "expected_rows": 8760,
        "grain": "one city-day-audited service-family aggregate",
        "raw": ["cross-city-311-daily.csv", "cross-city-311-daily.source-lock.json"],
        "question": "Are city service-request distributions sufficiently comparable to transfer an analytical rule between Chicago and New York?",
        "boundary": "Administrative shift audit only; requests are not latent need or service quality.",
        "result": "The 2023 cross-city total-variation distance is 58.1%, and the transfer gate is refused.",
        "methods": "Audited ontology, unmatched-category retention, total variation, Jensen-Shannon divergence, and transfer gating.",
        "config": {"baseline_year": 2022, "comparison_year": 2023, "maximum_transfer_total_variation": 0.2},
    },
    "wildfire-mitigation-under-uncertainty": {
        "title": "Wildfire Mitigation Evidence Allocation Under Uncertainty",
        "source_id": "calfire-historic-fire-perimeters-2000-2025",
        "publisher": "California Department of Forestry and Fire Protection",
        "landing_page": "https://www.arcgis.com/home/item.html?id=c3c10388e3b24cec8a954ba10458039d",
        "version": "California Historic Fire Perimeters feature service, filtered to 2000-2025",
        "license": "California open data / public information",
        "license_url": "https://www.fire.ca.gov/what-we-do/fire-resource-assessment-program/gis-mapping-and-data-analytics",
        "redistribution": "Official feature attributes; agency metadata and known completeness limits remain controlling.",
        "expected_rows": 8892,
        "grain": "one fire-perimeter record",
        "raw": ["calfire-fire-perimeters-2000-2025.csv"],
        "question": "Which exposure-weighted evidence-collection allocation is least fragile across historical, recent, and tail-fire scenarios?",
        "boundary": "No fires-prevented or acres-prevented estimate; mitigation action blocked pending effectiveness and feasibility evidence.",
        "result": "Across 8,892 valid mapped perimeters, recent observed acres is the lowest-regret proxy allocation under the tested scenarios.",
        "methods": "Observed exposure scenarios, allocation alignment, minimax regret, and evidence-request terminal gate.",
        "config": {"history_start": 2000, "recent_start": 2020, "recent_end": 2024, "tail_quantile": 0.9},
    },
    "social-norm-field-experiment": {
        "title": "Social-Norm Field Experiment with Household-Clustered Inference",
        "source_id": "yale-isps-d001-terms-compliant-aggregate",
        "publisher": "Yale Institution for Social and Policy Studies",
        "landing_page": "https://doi.org/10.60600/YU/CGMWNW",
        "additional_sources": [
            "https://isps.yale.edu/resource/social-pressure-and-voter-turnout-evidence-from-a-large-scale-field-experiment"
        ],
        "version": "Gerber-Green-Larimer 2008 replication file; non-identifying aggregate and locally computed clustered inference",
        "license": "CC0 1.0 (Yale Dataverse dataset)",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "redistribution": "Participant rows are not redistributed; only non-identifying aggregates and clustered statistics are stored.",
        "expected_rows": 10,
        "grain": "one treatment by prior-turnout aggregate",
        "raw": ["terms-compliant-treatment-aggregate.csv", "cluster-robust-itt.json", "external-source-lock.json"],
        "question": "What were the intent-to-treat turnout effects of randomized social-pressure mailings after household clustering?",
        "boundary": "Causal scope is the historical randomized experiment; no new campaign authorization.",
        "result": "The Neighbors arm has the largest observed intent-to-treat effect at 8.1%, with a household-clustered 95% interval of 7.5% to 8.8%.",
        "methods": "Randomized-arm rates, household-clustered sandwich variance, 95% intervals, and descriptive strata contrasts.",
        "source_rebuild": (
            "After reviewing the Yale ISPS terms, provide the participant-level "
            "replication file explicitly. The builder writes only the non-identifying "
            "aggregate, clustered estimates, and external-source lock:\n\n"
            "```bash\n"
            "python3 scripts/build_tailored_source_snapshots.py social "
            "--social-csv /absolute/path/to/reviewed-file.csv --accept-isps-terms\n"
            "```\n\n"
            "Run this command from the repository root. Participant rows are never "
            "stored in the repository."
        ),
        "config": {"confidence_level": 0.95, "cluster_unit": "household", "primary_outcome": "voted"},
    },
    "opportunity-zone-policy-evaluation": {
        "title": "Opportunity Zone One-Year Policy Evidence Screen",
        "source_id": "cdfi-acs-lodes-ma-qoz-2018-2019",
        "publisher": "CDFI Fund and U.S. Census Bureau",
        "landing_page": "https://www.cdfifund.gov/opportunity-zones",
        "version": "2018 designated QOZ list with 2018-2019 ACS and LODES Massachusetts tract panel",
        "license": "U.S. Government public data",
        "license_url": "https://www.cdfifund.gov/opportunity-zones",
        "redistribution": "Public federal data; source workbook and national tables are minimized to a tract panel.",
        "expected_rows": 2956,
        "grain": "one Massachusetts tract-year row",
        "raw": ["massachusetts-qoz-tract-panel.csv", "massachusetts-qoz-tract-panel.source-lock.json"],
        "question": "How did selected tract outcomes change immediately after QOZ designation relative to observed-covariate matches?",
        "boundary": "Associational one-year screen; no causal effect because parallel trends are unavailable.",
        "result": "The matched one-year screen contains 1,460 complete tract panels, including 138 designated QOZ tracts and 121 unique matched controls.",
        "methods": "Panel linkage, ACS special-value normalization, complete-case screening, nearest-neighbor matching, change contrasts, reuse-aware wild-cluster intervals, and support diagnostics.",
        "config": {"pre_year": 2018, "post_year": 2019, "bootstrap_samples": 500, "matching_fields": ["poverty", "income", "jobs", "unemployment"]},
    },
    "nhanes-population-transportability": {
        "title": "NHANES Mortality Transportability and Population Inequality",
        "source_id": "cdc-nhanes-2011-2016-linked-mortality",
        "publisher": "U.S. Centers for Disease Control and Prevention, National Center for Health Statistics",
        "landing_page": "https://www.cdc.gov/nchs/data-linkage/mortality-public.htm",
        "version": "NHANES 2011-2012 and 2015-2016 demographics linked to 2019 mortality",
        "license": "U.S. Government public-use data",
        "license_url": "https://www.cdc.gov/nchs/data-linkage/mortality-public.htm",
        "redistribution": "Public-use minimized cohort extract; NCHS linkage rules remain controlling.",
        "expected_rows": 11820,
        "grain": "one NHANES adult linked to 36-month mortality",
        "raw": ["nhanes-36-month-mortality-cohorts.csv", "nhanes-36-month-mortality-cohorts.source-lock.json"],
        "question": "Do population mortality risk patterns transport between NHANES cohorts, and what inequality gradient remains visible?",
        "boundary": "Population research only; no individual diagnosis or treatment.",
        "result": "The external-cohort check yields an AUC of 0.804 and a Brier score of 0.022 across 11,820 linked adults.",
        "methods": "Survey-weighted rates, cross-cohort AUC/Brier/calibration, and poverty-income-ratio gradients.",
        "config": {"development_cohort": "2011-2012", "validation_cohort": "2015-2016", "mortality_horizon_months": 36},
    },
    "spatial-equity-planning": {
        "title": "Spatial Equity Planning with Transit and Site-Evidence Gates",
        "source_id": "census-acs-2023-ma-tracts-mbta-stops",
        "publisher": "U.S. Census Bureau and Massachusetts Bay Transportation Authority",
        "landing_page": "https://www.census.gov/data/developers/data-sets/acs-5year/2023.html",
        "additional_sources": ["https://api-v3.mbta.com/"],
        "version": "2019-2023 ACS tract estimates, 2023 Gazetteer, and MBTA rapid-transit stops accessed 2026-08-10",
        "license": "U.S. Government open data and MBTA open data",
        "license_url": "https://www.census.gov/topics/research/research-transparency-public-access/open-data.html",
        "redistribution": "Public aggregate and transit-stop data.",
        "expected_rows": 1620,
        "grain": "one Massachusetts census tract",
        "raw": ["acs-b01003-ma.dat", "acs-b17001-ma.dat", "acs-b19013-ma.dat", "acs-b08301-ma.dat", "acs-b25064-ma.dat", "2023_Gaz_tracts_national.zip", "mbta-rapid-transit-stops.json"],
        "question": "Which tract-level service-hub priorities merit local review after observed rapid-transit proximity is added?",
        "boundary": "No site recommendation until parcel, zoning, network, cost, and community evidence is supplied.",
        "result": "Across 1,597 analyzed tracts and 265 rapid-transit stop records, the high-poverty weighted nearest-stop distance is 40.65 km.",
        "methods": "ACS need indicators, Moran's I, heuristic location allocation, bootstrap sensitivity, and nearest-MBTA-stop distance.",
        "config": None,
        "extra_manifest": {
            "download_url_template": "https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/acsdt5y2023-{table}.dat",
            "geography_url": "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_tracts_national.zip",
        },
    },
}


NEW_PROJECTS = {
    "cross-city-311-shift",
    "wildfire-mitigation-under-uncertainty",
    "social-norm-field-experiment",
    "opportunity-zone-policy-evaluation",
    "nhanes-population-transportability",
}


WRAPPER = """#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
from portfolio_runtime import project_main

raise SystemExit(project_main("{action}", __file__))
"""


def configure_project(project_id: str, spec: dict) -> None:
    root = PROJECTS / project_id
    root.mkdir(parents=True, exist_ok=True)
    raw_files = []
    for name in spec["raw"]:
        path = root / "data/raw" / name
        if not path.exists():
            raise FileNotFoundError(path)
        raw_files.append({"path": f"data/raw/{name}", "sha256": digest(path)})
    manifest = {
        "schema_version": "1.0",
        "project_id": project_id,
        "source_id": spec["source_id"],
        "title": spec["title"],
        "project_title": spec["title"],
        "publisher": spec["publisher"],
        "landing_page": spec["landing_page"],
        "version": spec["version"],
        "accessed_at": "2026-08-10",
        "license": spec["license"],
        "license_url": spec["license_url"],
        "redistribution": spec["redistribution"],
        "expected_rows": spec["expected_rows"],
        "grain": spec["grain"],
        "raw_files": raw_files,
        "privacy_review": {
            "contains_direct_identifiers": False,
            "contains_sensitive_attributes": project_id in {"population-health-survival", "census-income-ai", "social-norm-field-experiment", "nhanes-population-transportability"},
            "treatment": spec["boundary"],
            "status": "approved_for_public_minimized_analysis",
        },
        "citation": f"{spec['publisher']}. {spec['version']}.",
    }
    for key in ("additional_sources",):
        if spec.get(key):
            manifest[key] = spec[key]
    manifest.update(spec.get("extra_manifest", {}))
    write_json(root / "source-manifest.json", manifest)
    if spec.get("config") is not None:
        write_json(root / "config.json", parameters(project_id, spec["config"], spec["boundary"]))
    source_rebuild = spec.get("source_rebuild", "")
    source_rebuild_section = (
        f"\n## Recreate the minimized public sources\n\n{source_rebuild}\n\n"
        if source_rebuild
        else "\n"
    )
    document = f"""# {spec['title']}

**Analytical question:** {spec['question']}

**Decision boundary:** {spec['boundary']}

## Evidence and methods

- Source: {spec['publisher']} — {spec['version']}.
- Analytical grain: {spec['grain']}.
- Methods: {spec['methods']}
- Every bundled raw or minimized source file is hash-locked in `source-manifest.json`.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```
{source_rebuild_section}Read the [technical report](outputs/report.md), [machine-readable results](outputs/results.json), [source manifest](source-manifest.json), and [data-quality report](data/quality-report.json).

## Non-negotiable limitation

{spec['boundary']}
"""
    (root / "PROJECT.md").write_text(document, encoding="utf-8")
    for filename, action in (("download_data.py", "download"), ("prepare_data.py", "prepare"), ("analyze.py", "analyze"), ("build_decision_case.py", "case")):
        path = root / filename
        if project_id in NEW_PROJECTS or not path.exists():
            path.write_text(WRAPPER.format(action=action), encoding="utf-8")


ORDER = [
    ("bike-demand-operations", "R01", ["operations research", "service operations", "forecasting"]),
    ("cross-city-311-shift", "R02", ["urban analytics", "distribution shift", "information systems"]),
    ("bank-marketing-response", "R03", ["business analytics", "causal pilot design", "capacity planning"]),
    ("census-income-ai", "R04", ["artificial intelligence", "responsible AI", "temporal validation"]),
    ("treasury-risk-engineering", "R05", ["financial risk engineering", "yield curves", "tail risk"]),
    ("cfpb-fintech-complaint-operations", "R06", ["financial technology", "human-in-the-loop systems", "model risk"]),
    ("commercial-real-estate-risk", "R07", ["real-estate finance", "transaction analytics", "diligence"]),
    ("wildfire-mitigation-under-uncertainty", "R08", ["decision analysis", "robust optimization", "climate risk"]),
    ("sec-nport-filing-review", "R09", ["regulatory filings", "liquidity risk", "review prioritization"]),
    ("social-norm-field-experiment", "R10", ["field experiments", "behavioral science", "clustered inference"]),
    ("population-health-survival", "R11", ["population health", "survey methods", "mortality prediction"]),
    ("opportunity-zone-policy-evaluation", "R12", ["public policy", "program evaluation", "urban economics"]),
    ("behavioral-reading-experiment", "R13", ["statistics", "repeated measures", "behavioral science"]),
    ("nhanes-population-transportability", "R14", ["biostatistics", "transportability", "health inequality"]),
    ("spatial-equity-planning", "R15", ["urban planning", "spatial analytics", "transit equity"]),
]

REPRESENTATIVE_FIGURES = {
    "bike-demand-operations": "forecast-mae.svg",
    "cross-city-311-shift": "within-city-shift.svg",
    "bank-marketing-response": "capacity-capture.svg",
    "census-income-ai": "temporal-performance.svg",
    "treasury-risk-engineering": "expected-shortfall.svg",
    "cfpb-fintech-complaint-operations": "cumulative-gain.svg",
    "commercial-real-estate-risk": "borough-price-per-sqft.svg",
    "wildfire-mitigation-under-uncertainty": "scenario-regret.svg",
    "sec-nport-filing-review": "risk-indicator-p90.svg",
    "social-norm-field-experiment": "cluster-robust-itt.svg",
    "population-health-survival": "temporal-calibration.svg",
    "opportunity-zone-policy-evaluation": "matched-change-effects.svg",
    "behavioral-reading-experiment": "paired-effect.svg",
    "nhanes-population-transportability": "transport-calibration.svg",
    "spatial-equity-planning": "need-map.svg",
}


def _headline_items(result: dict) -> list[dict[str, str]]:
    items = []
    for index, item in enumerate(result.get("headline_metrics", []), start=1):
        if ":" in item:
            label, value = item.split(":", 1)
        else:
            label, value = f"Evidence signal {index}", item
        items.append({"label": label.strip(), "value": value.strip()})
    return items


def configure_case_index() -> None:
    case_path = ROOT / "examples/real-data-cases/cases.json"
    old_cases = []
    if case_path.exists():
        old_cases = json.loads(case_path.read_text(encoding="utf-8")).get("cases", [])
    old_by_project = {item["project_id"]: item for item in old_cases}
    cases = []
    for index, (project_id, _, domains) in enumerate(ORDER, start=1):
        root = PROJECTS / project_id
        manifest = json.loads((root / "source-manifest.json").read_text())
        result = json.loads((root / "outputs/results.json").read_text())
        prior = old_by_project.get(project_id, {})
        spec = SPECS.get(project_id)
        headlines = _headline_items(result) or prior.get("headline_metrics", [])
        if not headlines:
            headlines = [{"label": "Prepared rows", "value": f"{manifest['expected_rows']:,}"}]
        decision_result = root / "outputs/decision/report/decision-results.json"
        if decision_result.exists():
            decision = json.loads(decision_result.read_text())
            terminal = decision.get("decision_status") or decision.get("decision", {}).get("status") or "claim-bounded decision review"
        else:
            terminal = (
                result.get("decision_support", {}).get("status")
                or result.get("transfer_gate", {}).get("status")
                or result.get("deployment_gate", {}).get("status")
                or "analytical evidence endpoint"
            )
        methods = (
            [item.strip() for item in str(spec["methods"]).split(",")]
            if spec
            else prior.get("methods", ["case-specific reproducible analysis"])
        )
        question = spec["question"] if spec else prior.get("question", "What claim-bounded conclusion does the source support?")
        boundary = spec["boundary"] if spec else prior.get("boundary", "Reuse requires new source and domain validation.")
        result_text = (
            spec["result"]
            if spec
            else prior.get("result", f"The analysis terminates at {terminal}.")
        )
        raw_snapshots = [
            {"name": Path(item["path"]).name, "sha256": item["sha256"]}
            for item in manifest["raw_files"]
        ]
        title = manifest.get("project_title", manifest["title"])
        cases.append(
            {
                "number": f"{index:02d}",
                "id": project_id,
                "project_id": project_id,
                "title": title,
                "gallery_title": title,
                "gallery_endpoint": str(terminal).replace("_", " "),
                "domain": domains[0].title(),
                "route": result.get("study_design", {}).get("route", prior.get("route", ["descriptive", "diagnostic", "decision"])),
                "question": question,
                "source": {
                    "dataset": manifest["title"],
                    "publisher": manifest["publisher"],
                    "url": manifest["landing_page"],
                    "version": manifest["version"],
                    "accessed_at": manifest["accessed_at"],
                    "license": manifest["license"],
                    "grain": manifest["grain"],
                    "prepared_rows": manifest["expected_rows"],
                    "snapshot_files": raw_snapshots,
                },
                "methods": methods,
                "headline_metrics": headlines,
                "result": result_text,
                "terminal_output": str(terminal).replace("_", " "),
                "boundary": boundary,
                "figure": f"figures/{index:02d}-{project_id}.svg",
                "figure_alt": f"Representative evidence figure for {title}",
            }
        )
    write_json(
        case_path,
        {
            "schema_version": "2.0",
            "case_count": 15,
            "scope": "Fifteen school-neutral, reproducible real-data projects with one distinct substantive case per private application-program mapping.",
            "cases": cases,
        },
    )


def configure_catalog() -> None:
    existing = json.loads((PROJECTS / "project-catalog.json").read_text())["projects"]
    by_id = {item["id"]: item for item in existing}
    entries = []
    for project_id, code, domains in ORDER:
        title = SPECS[project_id]["title"] if project_id in SPECS else by_id[project_id]["title"]
        analytics = by_id.get(project_id, {}).get("analytics", ["descriptive", "diagnostic", "decision"])
        entries.append({"id": project_id, "code": code, "title": title, "analytics": analytics, "decision_analysis": "claim_bounded_case_specific", "method_domains": domains})
    write_json(
        PROJECTS / "project-catalog.json",
        {
            "portfolio_version": "9.0.0",
            "verified_on": "2026-08-10",
            "public_project_type": "real_world_research_project",
            "project_count": 15,
            "projects": entries,
            "synthetic_fixture_policy": {"public_project_count": 0, "location": "tests/fixtures/synthetic-cases", "purpose": "offline regression and edge-case testing only"},
        },
    )


def main() -> int:
    for project_id, spec in SPECS.items():
        configure_project(project_id, spec)
    upgrade_source_manifests()
    configure_catalog()
    configure_case_index()
    print(json.dumps({"configured_projects": len(SPECS), "catalog_projects": len(ORDER)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
