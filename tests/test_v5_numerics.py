from __future__ import annotations

import copy
import math
import random
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from decision_engine import (  # noqa: E402
    _normalize,
    _one_sided_binomial_upper_95,
    _probability_best,
    _sample_distribution_from_uniform,
    analyze_case,
    load_case,
    validate_case,
)
from prediction_validation import validate_predictions  # noqa: E402


class IndependentNumericalBenchmarks(unittest.TestCase):
    def test_zero_event_upper_bound_matches_exact_rule_of_three_expression(self) -> None:
        expected = 1.0 - 0.05 ** (1.0 / 1_000)
        self.assertAlmostEqual(
            _one_sided_binomial_upper_95(0, 1_000),
            expected,
            places=15,
        )

    def test_distribution_quantiles_match_closed_form_reference_points(self) -> None:
        self.assertAlmostEqual(
            _sample_distribution_from_uniform(
                {"distribution": "uniform", "low": 10.0, "high": 20.0},
                0.25,
            ),
            12.5,
        )
        self.assertAlmostEqual(
            _sample_distribution_from_uniform(
                {
                    "distribution": "triangular",
                    "low": 0.0,
                    "mode": 0.5,
                    "high": 1.0,
                },
                0.5,
            ),
            0.5,
        )
        self.assertAlmostEqual(
            _sample_distribution_from_uniform(
                {"distribution": "normal", "mean": 7.0, "sd": 2.0},
                0.5,
            ),
            7.0,
        )

    def test_prediction_metrics_match_hand_calculated_perfect_example(self) -> None:
        rows = [
            {"label": "0", "score": "0.1"},
            {"label": "0", "score": "0.2"},
            {"label": "1", "score": "0.8"},
            {"label": "1", "score": "0.9"},
        ]
        result = validate_predictions(
            rows,
            label_column="label",
            score_column="score",
            calibration_bins=2,
        )
        self.assertEqual(result["overall"]["auc"], 1.0)
        expected_brier = (0.1**2 + 0.2**2 + 0.2**2 + 0.1**2) / 4
        self.assertAlmostEqual(result["overall"]["brier_score"], expected_brier)
        self.assertEqual(
            result["overall"]["confusion_matrix"],
            {
                "true_positive": 2,
                "true_negative": 2,
                "false_positive": 0,
                "false_negative": 0,
            },
        )


class PropertyTests(unittest.TestCase):
    def test_inverse_marginals_are_monotone(self) -> None:
        specifications = [
            {"distribution": "fixed", "value": 3.0},
            {"distribution": "normal", "mean": 0.0, "sd": 1.0},
            {"distribution": "uniform", "low": -2.0, "high": 5.0},
            {
                "distribution": "triangular",
                "low": -3.0,
                "mode": 1.0,
                "high": 8.0,
            },
        ]
        probabilities = [index / 100 for index in range(1, 100)]
        for specification in specifications:
            values = [
                _sample_distribution_from_uniform(specification, probability)
                for probability in probabilities
            ]
            self.assertTrue(
                all(left <= right for left, right in zip(values, values[1:]))
            )

    def test_normalization_is_always_bounded(self) -> None:
        rng = random.Random(20260727)
        criteria = [
            {
                "direction": "maximize",
                "scale": {"worst": -10.0, "best": 10.0},
            },
            {
                "direction": "minimize",
                "scale": {"worst": 10.0, "best": -10.0},
            },
        ]
        for criterion in criteria:
            for _ in range(1_000):
                normalized = _normalize(rng.uniform(-1e9, 1e9), criterion)
                self.assertGreaterEqual(normalized, 0.0)
                self.assertLessEqual(normalized, 1.0)

    def test_probability_best_conserves_total_mass_and_splits_ties(self) -> None:
        utilities = {
            "a": [0.4, 0.8, 0.5, 0.2],
            "b": [0.4, 0.1, 0.5, 0.9],
        }
        shares = _probability_best(utilities, ["a", "b"], 4)
        self.assertAlmostEqual(sum(shares.values()), 1.0)
        self.assertAlmostEqual(shares["a"], 0.5)
        self.assertAlmostEqual(shares["b"], 0.5)

    def test_declared_factor_model_creates_realized_shared_utility_dependence(self) -> None:
        case = load_case(
            REPO_ROOT / "tests" / "fixtures" / "synthetic-cases"
            / "health-resource-allocation" / "case.json"
        )
        result = analyze_case(case, samples=3_000, seed=71)
        correlations = [
            item["correlation"]
            for item in result["correlation_sensitivity"][
                "realized_pairwise_utility_correlations"
            ]
            if item["correlation"] is not None
        ]
        self.assertTrue(correlations)
        self.assertGreater(sum(correlations) / len(correlations), 0.10)
        for state in (
            "independent_baseline",
            "declared_correlation",
            "correlation_stress",
        ):
            comparison = result["correlation_sensitivity"][state]
            feasible = comparison["feasible_alternatives"]
            self.assertAlmostEqual(
                sum(
                    comparison["alternatives"][alternative_id]["probability_best"]
                    for alternative_id in feasible
                ),
                1.0 if feasible else 0.0,
            )

    def test_parameter_provenance_resolves_every_expanded_path(self) -> None:
        case = load_case(
            REPO_ROOT / "tests" / "fixtures" / "synthetic-cases"
            / "supply-chain-resilience" / "case.json"
        )
        result = analyze_case(case, samples=300, seed=9)
        coverage = result["parameter_provenance"]["coverage"]
        self.assertGreater(coverage["parameters_required"], 50)
        self.assertEqual(coverage["source_coverage_rate"], 1.0)
        self.assertEqual(coverage["approval_coverage_rate"], 1.0)
        self.assertTrue(
            all(record["approval_chain"] for record in result["parameter_provenance"]["records"])
        )


class ExtremeInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [
            {"label": "0", "score": "0.0", "period": "2025-10"},
            {"label": "1", "score": "1.0", "period": "2026-02"},
            {"label": "0", "score": "0.2", "period": "2025-10"},
            {"label": "1", "score": "0.8", "period": "2026-02"},
        ]

    def test_threshold_closed_interval_accepts_zero_and_one(self) -> None:
        for threshold in (0.0, 1.0):
            result = validate_predictions(
                self.rows,
                label_column="label",
                score_column="score",
                threshold=threshold,
                calibration_bins=2,
            )
            self.assertEqual(result["overall"]["threshold"], threshold)

    def test_threshold_rejects_out_of_range_and_nonfinite_values(self) -> None:
        for threshold in (-0.01, 1.01, float("nan"), float("inf")):
            with self.subTest(threshold=threshold):
                with self.assertRaisesRegex(ValueError, "threshold"):
                    validate_predictions(
                        self.rows,
                        label_column="label",
                        score_column="score",
                        threshold=threshold,
                        calibration_bins=2,
                    )

    def test_calibration_bins_reject_invalid_and_overfragmented_values(self) -> None:
        for bins in (1, 101, 5):
            with self.subTest(bins=bins):
                with self.assertRaisesRegex(ValueError, "calibration_bins"):
                    validate_predictions(
                        self.rows,
                        label_column="label",
                        score_column="score",
                        calibration_bins=bins,
                    )

    def test_fractional_label_and_nonfinite_score_are_rejected(self) -> None:
        invalid_label = copy.deepcopy(self.rows)
        invalid_label[0]["label"] = "0.5"
        with self.assertRaisesRegex(ValueError, "0/1"):
            validate_predictions(
                invalid_label,
                label_column="label",
                score_column="score",
                calibration_bins=2,
            )
        invalid_score = copy.deepcopy(self.rows)
        invalid_score[0]["score"] = "nan"
        with self.assertRaisesRegex(ValueError, "between 0 and 1"):
            validate_predictions(
                invalid_score,
                label_column="label",
                score_column="score",
                calibration_bins=2,
            )

    def test_iso_periods_are_sorted_chronologically_not_lexically(self) -> None:
        rows = [
            {"label": "0", "score": "0.1", "period": "2026-10-01"},
            {"label": "1", "score": "0.9", "period": "2026-02-01"},
            {"label": "0", "score": "0.2", "period": "2026-10-01"},
            {"label": "1", "score": "0.8", "period": "2026-02-01"},
        ]
        result = validate_predictions(
            rows,
            label_column="label",
            score_column="score",
            period_column="period",
            calibration_bins=2,
        )
        self.assertEqual(result["drift"]["reference_period"], "2026-02-01")
        self.assertEqual(result["drift"]["current_period"], "2026-10-01")
        self.assertEqual(
            result["drift"]["period_ordering"],
            "iso8601_chronological",
        )

    def test_ambiguous_periods_and_missing_periods_are_rejected(self) -> None:
        ambiguous = copy.deepcopy(self.rows)
        ambiguous[0]["period"] = "wave-z"
        ambiguous[1]["period"] = "wave-a"
        with self.assertRaisesRegex(ValueError, "Period values"):
            validate_predictions(
                ambiguous,
                label_column="label",
                score_column="score",
                period_column="period",
                calibration_bins=2,
            )
        missing = copy.deepcopy(self.rows)
        missing[0]["period"] = ""
        with self.assertRaisesRegex(ValueError, "must be complete"):
            validate_predictions(
                missing,
                label_column="label",
                score_column="score",
                period_column="period",
                calibration_bins=2,
            )

    def test_degenerate_marginals_remain_finite(self) -> None:
        specifications = [
            {"distribution": "normal", "mean": 2.0, "sd": 0.0},
            {"distribution": "uniform", "low": 4.0, "high": 4.0},
            {
                "distribution": "triangular",
                "low": 6.0,
                "mode": 6.0,
                "high": 6.0,
            },
        ]
        for specification in specifications:
            for probability in (0.0, 0.5, 1.0):
                self.assertTrue(
                    math.isfinite(
                        _sample_distribution_from_uniform(
                            specification,
                            probability,
                        )
                    )
                )

    def test_governance_and_invalid_stressed_loadings_are_enforced(self) -> None:
        case = load_case(
            REPO_ROOT / "tests" / "fixtures" / "synthetic-cases"
            / "ai-model-validation" / "case.json"
        )
        missing_governance = copy.deepcopy(case)
        del missing_governance["parameter_governance"]
        self.assertTrue(
            any(
                "parameter_governance" in error
                for error in validate_case(missing_governance).errors
            )
        )
        invalid_stress = copy.deepcopy(case)
        invalid_stress["uncertainty_model"]["stress_multiplier"] = 3.0
        self.assertTrue(
            any(
                "Stressed squared factor loadings" in error
                for error in validate_case(invalid_stress).errors
            )
        )


if __name__ == "__main__":
    unittest.main()
