from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import re
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import configure_tailored_portfolio as portfolio_configuration  # noqa: E402
from decision_engine import validate_case  # noqa: E402

MIGRATION_PATH = SCRIPT_DIR / "migrate_case_v12_to_v13.py"
SPEC = importlib.util.spec_from_file_location("case_migration", MIGRATION_PATH)
assert SPEC is not None and SPEC.loader is not None
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)

PROJECT_ROOT = ROOT / "examples" / "real-data-cases" / "projects"
SHARED_DIR = PROJECT_ROOT / "_shared"
sys.path.insert(0, str(SHARED_DIR))
from portfolio_core import (  # noqa: E402
    ACS_SPECIAL_VALUE_CODES,
    PROJECTS_WITH_CASES,
    _quality,
    is_missing_value,
)
from portfolio_modeling import _total_variation_distance  # noqa: E402


class RealPortfolioContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(
            (PROJECT_ROOT / "project-catalog.json").read_text(encoding="utf-8")
        )

    def test_public_catalog_contains_fifteen_real_projects(self) -> None:
        self.assertEqual(self.catalog["project_count"], 15)
        self.assertEqual(
            self.catalog["public_project_type"],
            "real_world_research_project",
        )
        self.assertEqual(
            self.catalog["synthetic_fixture_policy"]["public_project_count"],
            0,
        )
        self.assertEqual(
            len({item["id"] for item in self.catalog["projects"]}),
            15,
        )
        case_index = json.loads(
            (
                ROOT / "examples" / "real-data-cases" / "cases.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(case_index["case_count"], 15)
        self.assertEqual(len(case_index["cases"]), 15)
        for case in case_index["cases"]:
            with self.subTest(case_result=case["id"]):
                self.assertNotEqual(
                    case["result"].strip(),
                    case["boundary"].strip(),
                )
                self.assertRegex(case["result"], r"\d")
                self.assertIsNone(
                    re.search(
                        r"\b(?:would|could|might|may)\b",
                        case["result"],
                        flags=re.IGNORECASE,
                    )
                )

    def test_case_index_generation_preserves_results_and_is_idempotent(self) -> None:
        source_index = ROOT / "examples/real-data-cases/cases.json"
        canonical = json.loads(source_index.read_text(encoding="utf-8"))
        canonical_results = {
            case["project_id"]: case["result"] for case in canonical["cases"]
        }

        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            temporary_index = temporary_root / "examples/real-data-cases/cases.json"
            temporary_index.parent.mkdir(parents=True)
            shutil.copy2(source_index, temporary_index)

            original_root = portfolio_configuration.ROOT
            original_projects = portfolio_configuration.PROJECTS
            try:
                portfolio_configuration.ROOT = temporary_root
                portfolio_configuration.PROJECTS = PROJECT_ROOT
                portfolio_configuration.configure_case_index()
                first_generation = temporary_index.read_bytes()
                portfolio_configuration.configure_case_index()
                second_generation = temporary_index.read_bytes()
            finally:
                portfolio_configuration.ROOT = original_root
                portfolio_configuration.PROJECTS = original_projects

        self.assertEqual(first_generation, second_generation)
        regenerated = json.loads(first_generation)["cases"]
        self.assertEqual(
            {case["project_id"]: case["result"] for case in regenerated},
            canonical_results,
        )
        for case in regenerated:
            with self.subTest(project=case["project_id"]):
                self.assertNotEqual(case["result"], case["boundary"])
                self.assertRegex(case["result"], r"\d")

    def test_every_project_has_real_source_and_report_contract(self) -> None:
        for item in self.catalog["projects"]:
            with self.subTest(project=item["id"]):
                project = PROJECT_ROOT / item["id"]
                manifest = json.loads(
                    (project / "source-manifest.json").read_text(encoding="utf-8")
                )
                self.assertTrue(manifest["publisher"])
                self.assertTrue(manifest["landing_page"].startswith("https://"))
                self.assertNotIn("synthetic", manifest["title"].casefold())
                self.assertTrue(manifest["raw_files"])
                report = (project / "outputs/report.md").read_text(encoding="utf-8")
                self.assertIn("## Executive Summary", report)
                self.assertIn("## What this study cannot establish", report)
                result_hash = hashlib.sha256(
                    (project / "outputs/results.json").read_bytes()
                ).hexdigest()
                self.assertIn(f"Result SHA-256: `{result_hash}`", report)
                self.assertGreaterEqual(
                    len(list((project / "outputs/figures").glob("*.svg"))),
                    3,
                )

    def test_structured_source_manifests_map_upstream_hashes_to_output_fields(self) -> None:
        expected_multi_source = {
            "cross-city-311-shift": 2,
            "population-health-survival": 2,
            "nhanes-population-transportability": 2,
            "opportunity-zone-policy-evaluation": 3,
            "spatial-equity-planning": 2,
        }
        for item in self.catalog["projects"]:
            with self.subTest(project=item["id"]):
                project = PROJECT_ROOT / item["id"]
                manifest = json.loads(
                    (project / "source-manifest.json").read_text(encoding="utf-8")
                )
                dictionary = json.loads(
                    (project / "data/data-dictionary.json").read_text(encoding="utf-8")
                )
                results = json.loads(
                    (project / "outputs/results.json").read_text(encoding="utf-8")
                )

                def nested_keys(value: object) -> set[str]:
                    if isinstance(value, dict):
                        return set(value) | {
                            key
                            for child in value.values()
                            for key in nested_keys(child)
                        }
                    if isinstance(value, list):
                        return {
                            key
                            for child in value
                            for key in nested_keys(child)
                        }
                    return set()

                documented_outputs = set(dictionary.get("fields", {})) | nested_keys(results)
                self.assertEqual(manifest["schema_version"], "1.1")
                sources = manifest["sources"]
                self.assertEqual(
                    len(sources),
                    expected_multi_source.get(item["id"], 1),
                )
                for source in sources:
                    for field in (
                        "source_id",
                        "publisher",
                        "version",
                        "license",
                        "license_url",
                        "url",
                        "artifacts",
                        "output_fields",
                    ):
                        self.assertTrue(source[field], field)
                    self.assertTrue(source["url"].startswith("https://"))
                    self.assertTrue(source["license_url"].startswith("https://"))
                    self.assertTrue(
                        set(source["output_fields"]).issubset(documented_outputs)
                    )
                    for artifact in source["artifacts"]:
                        self.assertEqual(artifact["hash_algorithm"], "sha256")
                        self.assertRegex(artifact["sha256"], r"^[0-9a-f]{64}$")
                        self.assertTrue(artifact.get("path") or artifact.get("url"))
                        if artifact.get("url"):
                            self.assertTrue(artifact["url"].startswith("https://"))

    def test_raw_sources_match_manifests_and_download_receipts(self) -> None:
        checked = 0
        for item in self.catalog["projects"]:
            with self.subTest(project=item["id"]):
                project = PROJECT_ROOT / item["id"]
                manifest = json.loads(
                    (project / "source-manifest.json").read_text(encoding="utf-8")
                )
                receipt = json.loads(
                    (project / "data/download-receipt.json").read_text(encoding="utf-8")
                )
                self.assertEqual(receipt["status"], "verified")
                self.assertTrue(manifest["license"])
                self.assertTrue(manifest["redistribution"])
                receipt_hashes = {
                    record["path"]: record["sha256"]
                    for record in receipt["files"]
                }
                for raw in manifest["raw_files"]:
                    path = project / raw["path"]
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    self.assertEqual(digest, raw["sha256"])
                    self.assertEqual(digest, receipt_hashes[raw["path"]])
                    checked += 1
                quality = json.loads(
                    (project / "data/quality-report.json").read_text(encoding="utf-8")
                )
                self.assertEqual(quality["rows"], manifest["expected_rows"])
                self.assertTrue(quality["row_count_matches_manifest"])
        expected = sum(
            len(
                json.loads(
                    (
                        PROJECT_ROOT
                        / item["id"]
                        / "source-manifest.json"
                    ).read_text(encoding="utf-8")
                )["raw_files"]
            )
            for item in self.catalog["projects"]
        )
        self.assertEqual(checked, expected)

    def test_all_configured_parameters_have_resolved_records(self) -> None:
        for item in self.catalog["projects"]:
            with self.subTest(project=item["id"]):
                project = PROJECT_ROOT / item["id"]
                config = json.loads(
                    (project / "config.json").read_text(encoding="utf-8")
                )
                provenance = json.loads(
                    (project / "outputs/parameter-provenance.json").read_text(
                        encoding="utf-8"
                    )
                )
                required = {
                    "config.analysis_seed",
                    *{
                        f"config.parameters.{key}"
                        for key in config.get("parameters", {})
                    },
                }
                records = {
                    record["parameter_path"]: record
                    for record in provenance["records"]
                }
                self.assertTrue(required.issubset(records))
                for path in required:
                    self.assertTrue(records[path]["source_id"])
                    self.assertGreaterEqual(
                        len(records[path]["approval_chain"]),
                        2,
                    )

    def test_embedded_decision_cases_use_schema_13_and_explicit_uncertainty(self) -> None:
        cases = sorted(
            PROJECT_ROOT.glob("*/outputs/decision/case.json")
        )
        self.assertEqual(len(cases), len(PROJECTS_WITH_CASES))
        for path in cases:
            with self.subTest(project=path.parents[2].name):
                case = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(case["schema_version"], "1.3")
                self.assertEqual(validate_case(case).errors, [])
                for alternative in case["alternatives"]:
                    for metric in alternative["metrics"].values():
                        self.assertIn(
                            metric["uncertainty_type"],
                            {"none", "parameter", "process", "scenario"},
                        )

    def test_legacy_fixture_migration_is_explicit_and_valid(self) -> None:
        source = json.loads(
            (
                ROOT
                / "tests/fixtures/synthetic-cases/health-resource-allocation/case.json"
            ).read_text(encoding="utf-8")
        )
        migrated, added = MIGRATION.migrate(source)
        self.assertEqual(migrated["schema_version"], "1.3")
        self.assertGreater(added, 0)
        self.assertEqual(validate_case(migrated).errors, [])
        for alternative in migrated["alternatives"]:
            for metric in alternative["metrics"].values():
                if metric["distribution"] == "fixed":
                    self.assertEqual(metric["uncertainty_type"], "none")
                else:
                    self.assertEqual(metric["uncertainty_type"], "parameter")

    def test_every_project_is_routable_from_a_method_domain(self) -> None:
        mapping = json.loads(
            (ROOT / "references/method-domain-map.json").read_text(encoding="utf-8")
        )
        real_ids = {item["id"] for item in self.catalog["projects"]}
        routed_ids = set()
        for domain in mapping["domains"]:
            self.assertTrue(domain["project_ids"])
            self.assertTrue(set(domain["project_ids"]).issubset(real_ids))
            routed_ids.update(domain["project_ids"])
        self.assertEqual(routed_ids, real_ids)

    def test_replacement_cases_enforce_honest_claim_boundaries(self) -> None:
        filing_review = json.loads(
            (
                PROJECT_ROOT
                / "sec-nport-filing-review/outputs/results.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(filing_review["data"]["rows"], 11747)
        self.assertEqual(
            filing_review["decision_support"]["status"],
            "targeted_filing_review_only",
        )
        self.assertEqual(
            filing_review["decision_options"]["review-top-10%"]["high_risk_capture"],
            1.0,
        )

        complaints = json.loads(
            (
                PROJECT_ROOT
                / "cfpb-fintech-complaint-operations/outputs/results.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(complaints["deployment_gate"]["passes"])
        self.assertEqual(
            complaints["deployment_gate"]["status"],
            "do_not_deploy_ranking_model",
        )
        self.assertAlmostEqual(
            complaints["capacity_validation"]["5%"]["lift_vs_random"],
            0.9983333333333334,
        )

        real_estate = json.loads(
            (
                PROJECT_ROOT
                / "commercial-real-estate-risk/outputs/results.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(real_estate["data"]["transactions"], 12399)
        self.assertEqual(
            real_estate["planning_delivery"]["status"],
            "diligence_screen_only",
        )
        self.assertEqual(
            real_estate["planning_delivery"][
                "sufficiently_observed_segments"
            ],
            20,
        )
        quality = json.loads(
            (
                PROJECT_ROOT
                / "commercial-real-estate-risk/data/quality-report.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(quality["duplicate_key_count"], 0)
        case_index = json.loads(
            (
                ROOT
                / "examples/real-data-cases/cases.json"
            ).read_text(encoding="utf-8")
        )
        real_estate_case = next(
            item
            for item in case_index["cases"]
            if item["project_id"] == "commercial-real-estate-risk"
        )
        case_metrics = {
            item["label"]: item["value"]
            for item in real_estate_case["headline_metrics"]
        }
        self.assertEqual(case_metrics["Filtered transactions"], "12,399")
        self.assertEqual(case_metrics["Break-even cap rate at 8.5% debt"], "7.5%")

    def test_filing_review_and_real_estate_numerical_properties(self) -> None:
        filing_review = json.loads(
            (
                PROJECT_ROOT
                / "sec-nport-filing-review/outputs/results.json"
            ).read_text(encoding="utf-8")
        )
        options = filing_review["decision_options"]
        shares = [
            options[name]["review_share"]
            for name in ("review-top-5%", "review-top-10%", "review-top-20%")
        ]
        captures = [
            options[name]["high_risk_capture"]
            for name in ("review-top-5%", "review-top-10%", "review-top-20%")
        ]
        scores = [
            options[name]["average_review_score"]
            for name in ("review-top-5%", "review-top-10%", "review-top-20%")
        ]
        self.assertEqual(shares, sorted(shares))
        self.assertEqual(captures, sorted(captures))
        self.assertEqual(scores, sorted(scores, reverse=True))

        real_estate = json.loads(
            (
                PROJECT_ROOT
                / "commercial-real-estate-risk/outputs/results.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(real_estate["borough_statistics"]),
            {"Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"},
        )
        cap_rates = [
            item["break_even_cap_rate_for_target_dscr"]
            for item in real_estate["financing_stress"]["scenarios"]
        ]
        self.assertEqual(cap_rates, sorted(cap_rates))

    def test_modular_runtime_has_small_stable_facade(self) -> None:
        shared = PROJECT_ROOT / "_shared"
        facade_lines = (
            shared / "portfolio_runtime.py"
        ).read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(facade_lines), 25)
        modules = [
            "portfolio_core.py",
            "portfolio_clinical.py",
            "portfolio_modeling.py",
            "portfolio_treasury.py",
            "portfolio_spatial.py",
            "portfolio_asset_realestate.py",
            "portfolio_reporting.py",
            "portfolio_tailored.py",
        ]
        for name in modules:
            with self.subTest(module=name):
                lines = (shared / name).read_text(encoding="utf-8").splitlines()
                self.assertGreater(len(lines), 100)
                self.assertLess(len(lines), 2500)

    def test_categorical_drift_is_order_invariant(self) -> None:
        reference_a = Counter({"US": 91, "Canada": 7, "Mexico": 2})
        current_a = Counter({"US": 82, "Canada": 11, "Mexico": 5, "Other": 2})
        reference_b = Counter(dict(reversed(list(reference_a.items()))))
        current_b = Counter(dict(reversed(list(current_a.items()))))
        first = _total_variation_distance(reference_a, current_a, 100, 100)
        second = _total_variation_distance(reference_b, current_b, 100, 100)
        self.assertEqual(first, second)
        self.assertAlmostEqual(first, 0.09)

    def test_missing_value_policy_is_normalized_and_explicit(self) -> None:
        for value in (
            None,
            "",
            "  ",
            "?",
            "NA",
            " na ",
            "N/A",
            " n/a ",
            "NaN",
            "null",
            "-666666666",
        ):
            with self.subTest(value=value):
                self.assertTrue(is_missing_value(value))
        for value in ("Not Applicable", "No", "0", 0, False):
            with self.subTest(value=value):
                self.assertFalse(is_missing_value(value))

    def test_unhandled_sentinels_and_domain_range_fail_the_quality_gate(self) -> None:
        quality = _quality(
            [{"id": "tract-1", "median_rent": "-666666666"}],
            "id",
            {"numeric_ranges": {"median_rent": {"minimum": 1, "maximum": 100000}}},
        )
        self.assertEqual(quality["quality_status"], "blocked")
        self.assertEqual(
            {finding["code"] for finding in quality["findings"]},
            {"unnormalized_source_sentinel", "missing_values_present"},
        )
        outside = _quality(
            [{"id": "tract-1", "rate": "1.1"}],
            "id",
            {"numeric_ranges": {"rate": {"minimum": 0, "maximum": 1}}},
        )
        self.assertEqual(outside["quality_status"], "blocked")
        self.assertEqual(outside["outside_range_count_by_column"], {"rate": 1})

    def test_processed_analytical_fields_contain_no_acs_special_codes(self) -> None:
        for item in self.catalog["projects"]:
            analysis = PROJECT_ROOT / item["id"] / "data/processed/analysis.csv"
            with analysis.open(newline="", encoding="utf-8-sig") as handle:
                for row_number, row in enumerate(csv.DictReader(handle), start=2):
                    for field, value in row.items():
                        if field.endswith("_source_code"):
                            continue
                        self.assertNotIn(
                            value.strip(),
                            ACS_SPECIAL_VALUE_CODES,
                            f"{item['id']} row {row_number} field {field}",
                        )

    def test_qoz_special_values_are_audited_and_results_are_plausible(self) -> None:
        project = PROJECT_ROOT / "opportunity-zone-policy-evaluation"
        quality = json.loads(
            (project / "data/quality-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(quality["sentinel_count_by_column"], {})
        self.assertEqual(
            quality["source_annotation_count_by_column"],
            {
                "median_gross_rent_source_code": 128,
                "median_household_income_source_code": 47,
            },
        )
        self.assertEqual(quality["missing_count_by_column"]["median_gross_rent"], 128)
        self.assertEqual(
            quality["missing_count_by_column"]["median_household_income"],
            47,
        )
        with (
            project / "data/raw/massachusetts-qoz-tract-panel.csv"
        ).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        source_codes = [
            (field.removesuffix("_source_code"), value)
            for row in rows
            for field, value in row.items()
            if field.endswith("_source_code") and value
        ]
        self.assertEqual(len(source_codes), 175)
        for field, code in source_codes:
            self.assertEqual(code, "-666666666")
            row = next(
                candidate
                for candidate in rows
                if candidate[f"{field}_source_code"] == code
            )
            self.assertEqual(row[field], "")

        results = json.loads(
            (project / "outputs/results.json").read_text(encoding="utf-8")
        )
        self.assertEqual(results["data"]["excluded_tracts"], 84)
        self.assertEqual(results["data"]["exclusion_counts"], {"source_special_value": 84})
        self.assertEqual(
            results["data"]["complete_tracts"] + results["data"]["excluded_tracts"],
            results["data"]["panel_rows"] // 2,
        )
        effects = results["matched_change_effects"]
        self.assertLess(abs(effects["change_income"]["matched_difference_in_change"]), 1_000_000)
        self.assertLess(abs(effects["change_rent"]["matched_difference_in_change"]), 100_000)
        for outcome, result in effects.items():
            point = result["matched_difference_in_change"]
            interval = result["control_reuse_wild_cluster_95_interval"]
            self.assertTrue(math.isfinite(point), outcome)
            self.assertTrue(all(math.isfinite(value) for value in interval), outcome)
            self.assertLessEqual(interval[0], interval[1], outcome)
            if outcome in {"change_poverty", "change_unemployment"}:
                self.assertTrue(-1 <= point <= 1, outcome)
                self.assertTrue(all(-1 <= value <= 1 for value in interval), outcome)

    def test_nhanes_weight_policy_and_spatial_annotations_are_explicit(self) -> None:
        nhanes = PROJECT_ROOT / "nhanes-population-transportability"
        with (nhanes / "data/processed/analysis.csv").open(
            newline="",
            encoding="utf-8",
        ) as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(all(float(row["interview_weight"]) > 0 for row in rows))
        self.assertEqual(sum(not row["poverty_income_ratio"] for row in rows), 1196)
        nhanes_quality = json.loads(
            (nhanes / "data/quality-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            nhanes_quality["missing_count_by_column"]["poverty_income_ratio"],
            1196,
        )
        nhanes_results = json.loads(
            (nhanes / "outputs/results.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            nhanes_results["study_design"]["primary_weight"],
            "WTINT2YR interview weight",
        )
        self.assertEqual(
            nhanes_results["data"]["excluded_nonpositive_or_missing_weight"],
            0,
        )
        self.assertTrue(0 <= nhanes_results["transport_validation"]["auc"] <= 1)
        self.assertTrue(0 <= nhanes_results["transport_validation"]["brier"] <= 1)

        spatial = PROJECT_ROOT / "spatial-equity-planning"
        spatial_quality = json.loads(
            (spatial / "data/quality-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(spatial_quality["sentinel_count_by_column"], {})
        self.assertEqual(
            spatial_quality["source_annotation_count_by_column"][
                "median_income_moe_source_code"
            ],
            55,
        )
        self.assertEqual(
            spatial_quality["source_annotation_count_by_column"][
                "median_rent_moe_source_code"
            ],
            141,
        )
        spatial_results = json.loads(
            (spatial / "outputs/results.json").read_text(encoding="utf-8")
        )
        self.assertAlmostEqual(
            spatial_results["transit_access"][
                "high_poverty_weighted_nearest_stop_km"
            ],
            40.64967661673857,
        )

    def test_bike_scenario_key_matches_2021_evidence(self) -> None:
        results = json.loads(
            (
                PROJECT_ROOT / "bike-demand-operations/outputs/results.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn("scenario_evaluation", results["optimization"])
        self.assertNotIn("policies_2012_evaluation", results["optimization"])


if __name__ == "__main__":
    unittest.main()
