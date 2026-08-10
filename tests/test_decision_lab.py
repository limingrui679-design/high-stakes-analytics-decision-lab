from __future__ import annotations

import copy
import csv
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from allocation_optimizer import optimize_allocation
from allocation_optimizer import write_outputs as write_optimization
from analytics_router import build_blueprint, render_blueprint_report, write_blueprint
from decision_engine import analyze_case, load_case, render_report, validate_case, write_outputs
from evidence_analysis import analyze_evidence
from evidence_analysis import write_outputs as write_evidence
from prediction_validation import validate_predictions
from prediction_validation import write_outputs as write_predictions
from visual_system import BLUE, CORAL, TEAL, VIOLET, theme_for


class DecisionLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example_paths = sorted(
            (
                REPO_ROOT / "tests" / "fixtures" / "synthetic-cases"
            ).glob("*/case.json")
        )
        if not cls.example_paths:
            raise AssertionError("No example case files were found.")

    def test_all_examples_validate_and_run(self) -> None:
        for path in self.example_paths:
            with self.subTest(case=path.parent.name):
                case = load_case(path)
                validation = validate_case(case)
                self.assertEqual(validation.errors, [])
                result = analyze_case(case, samples=500, seed=7)
                self.assertEqual(len(result["decision"]["ranking"]), len(case["alternatives"]))
                self.assertIn("decision_ready", result["decision"])

    def test_domain_theme_precedence_is_semantically_stable(self) -> None:
        self.assertEqual(
            theme_for("Urban planning, place-based policy, and public finance")[0],
            CORAL,
        )
        self.assertEqual(
            theme_for("Financial analytics, FinTech, and responsible AI")[0],
            VIOLET,
        )
        self.assertEqual(
            theme_for("Population health, public policy, and operations")[0],
            TEAL,
        )
        self.assertEqual(
            theme_for("Artificial intelligence, technology policy, and governance")[0],
            BLUE,
        )

    def test_bundled_case_template_is_valid(self) -> None:
        template_path = (
            REPO_ROOT
            / "assets"
            / "case-template.json"
        )
        validation = validate_case(load_case(template_path))
        self.assertEqual(validation.errors, [])

    def test_run_is_deterministic_for_same_seed(self) -> None:
        case = load_case(self.example_paths[0])
        first = analyze_case(case, samples=600, seed=123)
        second = analyze_case(case, samples=600, seed=123)
        first["metadata"].pop("generated_at")
        second["metadata"].pop("generated_at")
        self.assertEqual(first, second)

    def test_invalid_scenario_probability_is_rejected(self) -> None:
        case = load_case(self.example_paths[0])
        invalid = copy.deepcopy(case)
        invalid["scenarios"][0]["probability"] += 0.2
        result = validate_case(invalid)
        self.assertTrue(any("probabilities must sum" in item for item in result.errors))

    def test_no_feasible_alternative_produces_no_recommendation(self) -> None:
        case = load_case(self.example_paths[0])
        impossible = copy.deepcopy(case)
        impossible["constraints"] = [
            {
                "criterion": case["criteria"][0]["id"],
                "operator": ">=",
                "threshold": 1e12,
                "label": "Impossible threshold",
            }
        ]
        result = analyze_case(impossible, samples=500, seed=42)
        self.assertFalse(result["decision"]["decision_ready"])
        self.assertIsNone(result["decision"]["recommendation"])
        self.assertEqual(
            result["decision"]["decision_status"],
            "no_feasible_option",
        )

    def test_scoring_is_feasibility_first_and_risk_consistent(self) -> None:
        case = load_case(
            REPO_ROOT / "tests" / "fixtures" / "synthetic-cases"
            / "health-resource-allocation" / "case.json"
        )
        result = analyze_case(case, samples=1_000, seed=17)
        feasible_ids = [
            alternative_id
            for alternative_id, summary in result["alternatives"].items()
            if summary["feasible"]
        ]
        self.assertAlmostEqual(
            sum(
                result["alternatives"][alternative_id]["probability_best"]
                for alternative_id in feasible_ids
            ),
            1.0,
        )
        for alternative_id, summary in result["alternatives"].items():
            if not summary["feasible"]:
                self.assertEqual(summary["probability_best"], 0.0)
            self.assertEqual(
                len(summary["constraint_diagnostics"]),
                len(case["constraints"]),
            )
            self.assertTrue(
                all(
                    diagnostic["margin_p05"] <= diagnostic["margin_p95"]
                    for diagnostic in summary["constraint_diagnostics"]
                )
            )
        self.assertEqual(
            len(result["weight_sensitivity"]),
            2 * len(case["criteria"]),
        )
        self.assertEqual(
            {item["direction"] for item in result["weight_sensitivity"]},
            {"decrease", "increase"},
        )
        for item in result["weight_sensitivity"]:
            for alternative_id, score in item["scores"].items():
                self.assertAlmostEqual(
                    score,
                    item["score_details"][alternative_id][
                        "risk_adjusted_utility"
                    ],
                )

    def test_zero_observed_breach_is_not_reported_as_zero_risk(self) -> None:
        case = load_case(
            REPO_ROOT / "tests" / "fixtures" / "synthetic-cases"
            / "ai-procurement-governance" / "case.json"
        )
        for constraint in case["constraints"]:
            constraint["threshold"] = 1e12
        result = analyze_case(case, samples=500, seed=19)
        zero_event_summaries = [
            summary
            for summary in result["alternatives"].values()
            if summary["constraint_violation_count"] == 0
        ]
        self.assertTrue(zero_event_summaries)
        expected_upper = 1.0 - 0.05 ** (1.0 / 500)
        for summary in zero_event_summaries:
            self.assertAlmostEqual(
                summary["constraint_violation_rate_upper_95"],
                expected_upper,
            )
            self.assertIn(
                summary["constraint_support_status"],
                {
                    "declared_support_excludes_breach",
                    "modeled_tail_crosses_threshold",
                    "unbounded_tail",
                },
            )
        report = render_report(case, result)
        self.assertIn("U95", report)
        self.assertIn("never presented as proof of zero real-world risk", report)

    def test_preferred_demo_options_have_nonzero_tail_breach(self) -> None:
        for path in self.example_paths:
            with self.subTest(case=path.parent.name):
                result = analyze_case(load_case(path), samples=3_000, seed=20260726)
                recommendation = result["decision"]["recommendation"]
                self.assertIsNotNone(recommendation)
                self.assertGreater(
                    result["alternatives"][recommendation][
                        "constraint_violation_count"
                    ],
                    0,
                )

    def test_robustness_score_and_evidence_status_are_separate(self) -> None:
        case = load_case(
            REPO_ROOT / "tests" / "fixtures" / "synthetic-cases"
            / "behavioral-policy-nudge" / "case.json"
        )
        result = analyze_case(case, samples=1_000, seed=23)
        components = result["decision"]["robustness_components"]
        expected_score = 100 * sum(
            item["value"] * item["weight"] for item in components.values()
        )
        self.assertAlmostEqual(
            result["decision"]["robustness_score"],
            expected_score,
        )
        self.assertEqual(
            result["decision"]["decision_status"],
            "illustrative_preference",
        )
        self.assertFalse(result["decision"]["decision_ready"])
        self.assertIn(
            "evidence is not labeled for operational use",
            result["decision"]["blocking_reasons"],
        )

    def test_stratified_scenarios_cover_every_scenario(self) -> None:
        case = load_case(self.example_paths[0])
        result = analyze_case(case, samples=500, seed=31)
        for summary in result["alternatives"].values():
            counts = [
                item["sample_count"]
                for item in summary["scenario_utility"].values()
            ]
            self.assertEqual(sum(counts), 500)
            self.assertTrue(all(count > 0 for count in counts))

    def test_normalized_weights_and_scale_clipping_are_reported(self) -> None:
        case = load_case(self.example_paths[0])
        case["criteria"][0]["weight"] *= 2
        result = analyze_case(case, samples=500, seed=37)
        self.assertAlmostEqual(
            sum(item["normalized_weight"] for item in result["criteria"]),
            1.0,
        )
        self.assertTrue(
            any("engine will normalize" in warning for warning in result["metadata"]["warnings"])
        )
        recommendation = result["alternatives"][result["decision"]["recommendation"]]
        self.assertTrue(
            all(
                0 <= metric["scale_clipping_rate"] <= 1
                for metric in recommendation["criteria"].values()
            )
        )

    def test_operational_label_cannot_mask_synthetic_evidence(self) -> None:
        case = load_case(self.example_paths[0])
        case["evidence"]["decision_use"] = "operational"
        validation = validate_case(case)
        self.assertTrue(
            any(
                "Operational decision use is incompatible" in error
                for error in validation.errors
            )
        )

    def test_invalid_risk_and_sensitivity_settings_are_rejected(self) -> None:
        case = load_case(self.example_paths[0])
        case["risk_aversion"] = 1.1
        case["sensitivity_weight_multiplier"] = 1.0
        case["scenarios"][0]["probability"] = 0.0
        validation = validate_case(case)
        self.assertTrue(any("risk_aversion" in error for error in validation.errors))
        self.assertTrue(
            any("sensitivity_weight_multiplier" in error for error in validation.errors)
        )
        self.assertTrue(any("positive finite" in error for error in validation.errors))

    def test_reports_and_json_are_written(self) -> None:
        case = load_case(self.example_paths[0])
        result = analyze_case(case, samples=500, seed=99)
        report = render_report(case, result)
        self.assertIn("# ", report)
        self.assertIn("## Executive Summary", report)
        self.assertIn("![Decision summary]", report)
        self.assertIn("## Recommended next steps", report)
        with tempfile.TemporaryDirectory() as directory:
            result_path, report_path = write_outputs(case, result, directory)
            self.assertTrue(result_path.exists())
            self.assertTrue(report_path.exists())
            json.loads(result_path.read_text(encoding="utf-8"))
            figures_dir = Path(directory) / "figures"
            expected_figures = {
                "decision-scorecard.svg",
                "robustness-profile.svg",
                "alternative-ranking.svg",
                "constraint-risk.svg",
                "utility-uncertainty.svg",
                "criterion-scorecard.svg",
                "scenario-performance.svg",
                "weight-sensitivity.svg",
            }
            self.assertTrue(expected_figures.issubset({path.name for path in figures_dir.glob("*.svg")}))
            for svg_path in figures_dir.glob("*.svg"):
                root = ET.parse(svg_path).getroot()
                self.assertTrue(root.tag.endswith("svg"))
                tags = {child.tag.rsplit("}", 1)[-1] for child in root}
                self.assertIn("title", tags)
                self.assertIn("desc", tags)
            chart_map = json.loads(
                (figures_dir / "chart-map.json").read_text(encoding="utf-8")
            )
            self.assertGreaterEqual(len(chart_map), 8)
            self.assertTrue(
                all((Path(directory) / item["file"]).exists() for item in chart_map)
            )
            required_chart_fields = {
                "analytical_question",
                "supported_takeaway",
                "benchmark",
                "family",
                "source",
                "palette_policy",
                "accessibility",
            }
            self.assertTrue(
                all(required_chart_fields.issubset(item) for item in chart_map)
            )
            self.assertIn(
                "![Constraint risk boundary](figures/constraint-risk.svg)",
                report_path.read_text(encoding="utf-8"),
            )

    def test_question_router_builds_full_analytics_lifecycle(self) -> None:
        blueprint = build_blueprint(
            "How should a city allocate next year's screening capacity under a budget constraint?"
        )
        self.assertEqual(blueprint["routing"]["primary_mode"], "prescriptive")
        self.assertEqual(
            blueprint["routing"]["execution_order"],
            ["descriptive", "predictive", "prescriptive"],
        )
        self.assertEqual(
            [lens["id"] for lens in blueprint["analysis_lenses"]],
            ["descriptive", "predictive", "prescriptive"],
        )
        report = render_blueprint_report(blueprint)
        self.assertIn("## 1. Descriptive analytics", report)
        self.assertIn("## 2. Predictive analytics", report)
        self.assertIn("## 3. Prescriptive analytics", report)
        self.assertIn("analysis blueprint, not an empirical finding", report)

    def test_question_router_supports_auto_scope_and_chinese(self) -> None:
        descriptive = build_blueprint(
            "What happened to conversion last quarter?",
            scope="auto",
        )
        self.assertEqual(descriptive["routing"]["primary_mode"], "descriptive")
        self.assertEqual(
            descriptive["routing"]["execution_order"],
            ["descriptive"],
        )
        predictive = build_blueprint(
            "未来三个月的门诊量和需求风险会如何变化？",
            scope="auto",
        )
        self.assertEqual(predictive["routing"]["primary_mode"], "predictive")
        self.assertEqual(
            predictive["routing"]["execution_order"],
            ["descriptive", "predictive"],
        )

    def test_question_router_handles_diagnostic_and_action_boundaries(self) -> None:
        cases = [
            ("Explain why activation dropped after onboarding.", "diagnostic"),
            ("Forecast next-quarter demand by region.", "predictive"),
            ("Which policy minimizes delay under a fixed budget?", "prescriptive"),
            ("比较不同地区当前的服务覆盖率", "descriptive"),
            ("为什么高风险群体的续期率下降？", "diagnostic"),
            ("哪种方案可以在预算内最大化健康收益？", "prescriptive"),
        ]
        for question, expected in cases:
            with self.subTest(question=question):
                blueprint = build_blueprint(question, scope="auto")
                self.assertEqual(
                    blueprint["routing"]["primary_mode"],
                    expected,
                )
                self.assertIn(
                    blueprint["routing"]["confidence"],
                    {"medium", "high"},
                )

    def test_question_router_writes_json_markdown_and_svg(self) -> None:
        blueprint = build_blueprint(
            "Which credit strategy should we choose under recession risk?"
        )
        with tempfile.TemporaryDirectory() as directory:
            json_path, report_path, figure_path = write_blueprint(
                blueprint,
                directory,
            )
            self.assertTrue(json_path.exists())
            self.assertTrue(report_path.exists())
            self.assertTrue(figure_path.exists())
            parsed = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["routing"]["primary_mode"], "prescriptive")
            self.assertTrue(ET.parse(figure_path).getroot().tag.endswith("svg"))

    def test_evidence_prediction_and_optimization_modules(self) -> None:
        evidence_path = (
            REPO_ROOT / "tests" / "fixtures" / "synthetic-cases"
            / "clinical-evidence-design" / "study-data.csv"
        )
        with evidence_path.open("r", encoding="utf-8", newline="") as handle:
            evidence_rows = list(csv.DictReader(handle))
        evidence = analyze_evidence(
            evidence_rows,
            group_column="arm",
            binary_outcome="adverse_event_180d",
            exposed_group="adaptive",
            reference_group="standard",
            continuous_outcome="health_score_change",
            time_column="followup_days",
            event_column="event",
            horizon=180,
        )
        self.assertLess(evidence["binary_outcome"]["risk_difference"], 0)
        self.assertIsNotNone(evidence["continuous_outcome"])
        self.assertIsNotNone(evidence["time_to_event"])

        prediction_path = (
            REPO_ROOT / "tests" / "fixtures" / "synthetic-cases"
            / "ai-model-validation" / "predictions.csv"
        )
        with prediction_path.open("r", encoding="utf-8", newline="") as handle:
            prediction_rows = list(csv.DictReader(handle))
        prediction = validate_predictions(
            prediction_rows,
            label_column="label",
            score_column="score",
            threshold=0.5,
            group_column="group",
            period_column="period",
            calibration_bins=5,
        )
        self.assertGreater(prediction["overall"]["auc"], 0.5)
        self.assertEqual(set(prediction["subgroups"]), {"A", "B", "C"})
        self.assertIsNotNone(prediction["drift"])

        config = json.loads(
            (
                REPO_ROOT
                / "tests"
                / "fixtures"
                / "synthetic-cases"
                / "health-resource-allocation"
                / "optimization-config.json"
            ).read_text(encoding="utf-8")
        )
        optimization = optimize_allocation(config)
        self.assertEqual(optimization["status"], "optimal_on_declared_grid")
        self.assertGreater(optimization["feasible_allocations"], 0)
        self.assertTrue(
            all(
                diagnostic["holds"]
                for diagnostic in optimization["optimal_allocation"]["constraints"]
            )
        )

        with tempfile.TemporaryDirectory() as directory:
            evidence_paths = write_evidence(evidence, Path(directory) / "e", "Evidence")
            prediction_paths = write_predictions(
                prediction,
                Path(directory) / "p",
                "Prediction",
            )
            optimization_paths = write_optimization(
                optimization,
                Path(directory) / "o",
                "Optimization",
            )
            for path in (*evidence_paths, *prediction_paths, *optimization_paths):
                if path is not None:
                    self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
