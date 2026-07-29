from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from decision_engine import validate_case  # noqa: E402

MIGRATION_PATH = SCRIPT_DIR / "migrate_case_v12_to_v13.py"
SPEC = importlib.util.spec_from_file_location("case_migration", MIGRATION_PATH)
assert SPEC is not None and SPEC.loader is not None
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)

PROJECT_ROOT = ROOT / "examples" / "real-data-cases" / "projects"
SHARED_DIR = PROJECT_ROOT / "_shared"
sys.path.insert(0, str(SHARED_DIR))
from portfolio_modeling import _total_variation_distance  # noqa: E402
from portfolio_core import is_missing_value  # noqa: E402


class RealPortfolioContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(
            (PROJECT_ROOT / "project-catalog.json").read_text(encoding="utf-8")
        )

    def test_public_catalog_contains_only_ten_real_projects(self) -> None:
        self.assertEqual(self.catalog["project_count"], 10)
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
            10,
        )

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
                self.assertGreaterEqual(
                    len(list((project / "outputs/figures").glob("*.svg"))),
                    3,
                )

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
        self.assertEqual(checked, 22)

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
        self.assertEqual(len(cases), 5)
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

    def test_weak_cases_enforce_honest_claim_boundaries(self) -> None:
        finance = json.loads(
            (
                PROJECT_ROOT
                / "mckesson-financial-quality/outputs/results.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(finance["data"]["entities"], 3)
        self.assertEqual(finance["data"]["company_years"], 24)

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

        disclosure = json.loads(
            (
                PROJECT_ROOT
                / "federal-ai-governance/outputs/results.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(disclosure["public_fields_analyzed"], 34)
        self.assertGreater(
            disclosure["field_availability_status_counts"][
                "unavailable in snapshot (0%)"
            ],
            0,
        )
        self.assertIn(
            "not governance maturity",
            disclosure["disclosure_readiness"]["interpretation"],
        )
        quality = json.loads(
            (
                PROJECT_ROOT
                / "federal-ai-governance/data/quality-report.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            quality["missing_count_by_column"]["High Impact Justification"],
            70,
        )
        self.assertEqual(
            disclosure["field_reporting_completeness"][
                "High Impact Justification"
            ],
            0.0,
        )
        self.assertEqual(
            disclosure["field_availability_status_counts"],
            {
                "fully populated (95–100%)": 12,
                "partially populated (>0–<95%)": 8,
                "unavailable in snapshot (0%)": 14,
            },
        )
        self.assertAlmostEqual(
            disclosure["disclosure_readiness"]["mean"],
            0.4157142857142857,
        )
        case_index = json.loads(
            (
                ROOT
                / "examples/real-data-cases/cases.json"
            ).read_text(encoding="utf-8")
        )
        governance_case = next(
            item
            for item in case_index["cases"]
            if item["project_id"] == "federal-ai-governance"
        )
        case_metrics = {
            item["label"]: item["value"]
            for item in governance_case["headline_metrics"]
        }
        self.assertEqual(
            case_metrics["Fields unavailable in the snapshot"],
            "14",
        )
        self.assertEqual(
            case_metrics["Mean disclosure readiness"],
            "41.6% (observability only)",
        )

    def test_peer_panel_and_disclosure_taxonomy_properties(self) -> None:
        finance = json.loads(
            (
                PROJECT_ROOT
                / "mckesson-financial-quality/outputs/results.json"
            ).read_text(encoding="utf-8")
        )
        by_year = {}
        for row in finance["annual_metrics"]:
            by_year.setdefault(row["fiscal_year"], []).append(row)
        self.assertEqual(set(by_year), set(range(2018, 2026)))
        for rows in by_year.values():
            self.assertEqual(len(rows), 3)
            self.assertEqual(
                {row["peer_rank_operating_margin"] for row in rows},
                {1, 2, 3},
            )
            median = sorted(row["operating_margin"] for row in rows)[1]
            for row in rows:
                self.assertAlmostEqual(
                    row["peer_median_operating_margin"],
                    median,
                )

        disclosure = json.loads(
            (
                PROJECT_ROOT
                / "federal-ai-governance/outputs/results.json"
            ).read_text(encoding="utf-8")
        )
        classified = [
            field
            for fields in disclosure["information_families"].values()
            for field in fields
        ]
        self.assertEqual(len(classified), 34)
        self.assertEqual(len(set(classified)), 34)
        self.assertEqual(
            sum(disclosure["field_availability_status_counts"].values()),
            34,
        )

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
            "portfolio_finance.py",
            "portfolio_governance_spatial.py",
            "portfolio_reporting.py",
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
        for value in (None, "", "  ", "?", "NA", " na ", "N/A", " n/a "):
            with self.subTest(value=value):
                self.assertTrue(is_missing_value(value))
        for value in ("Not Applicable", "No", "0", 0, False):
            with self.subTest(value=value):
                self.assertFalse(is_missing_value(value))


if __name__ == "__main__":
    unittest.main()
