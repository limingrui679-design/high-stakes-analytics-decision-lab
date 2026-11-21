import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prediction_validation import _auc, validate_predictions  # noqa: E402


class ReviewCapacityTests(unittest.TestCase):
    def test_ties_have_bounds_and_do_not_use_input_order(self):
        rows = [{"y": str(y), "s": str(s)} for y, s in [(1, 0.9), (1, 0.5), (0, 0.5), (0, 0.1)]]
        for sample in [rows, rows[::-1]]:
            result = validate_predictions(
                sample,
                label_column="y",
                score_column="s",
                calibration_bins=2,
                review_budgets=[4, 2],
            )
            middle, full = result["review_capacity"]
            self.assertEqual(
                (middle["min_positives"], middle["expected_positives"], middle["max_positives"]),
                (1, 1.5, 2),
            )
            self.assertEqual(middle["expected_positives_random_review"], 1)
            self.assertEqual(full["expected_recall"], 1)
        self.assertEqual(_auc([1, 1, 0, 0], [0.9, 0.5, 0.5, 0.1]), 0.875)
        with self.assertRaisesRegex(ValueError, "review budget"):
            validate_predictions(
                rows, label_column="y", score_column="s", calibration_bins=2, review_budgets=[5]
            )

    def test_batch_capacity_expires_and_pooled_ranking_uses_the_same_slots(self):
        rows = [
            {"y": str(y), "s": str(s), "batch": b}
            for y, s, b in [(1, .9, "A"), (1, .9, "A"), (0, .9, "A"), (0, .1, "B")]
        ]
        def result(sample, **kwargs):
            return validate_predictions(sample, label_column="y", score_column="s", calibration_bins=2, **kwargs)
        for sample in (rows, rows[::-1]):
            report = result(sample, batch_column="batch", batch_capacity=2)["batch_review"]
            self.assertEqual((report["slots_used"], report["unused_slots_in_observed_batches"]), (3, 1))
            self.assertAlmostEqual(report["expected_positives"], 4 / 3)
            self.assertAlmostEqual(report["expected_positives_random_within_batch"], 4 / 3)
            self.assertEqual((report["min_positives"], report["max_positives"]), (1, 2))
            self.assertEqual(report["pooled_same_slots_expected_positives"], 2)
        for args in ({"batch_capacity": 2}, {"batch_column": "batch", "batch_capacity": 0}):
            with self.assertRaises(ValueError):
                result(rows, **args)
        with self.assertRaisesRegex(ValueError, "complete"):
            result([*rows, {"y": "0", "s": ".2"}], batch_column="batch", batch_capacity=1)

    def test_exact_yield_matches_exhaustive_two_batch_lotteries(self):
        from itertools import combinations, product

        from prediction_validation import _draw_distribution

        rows = [
            {"day": day, "score": str(score), "y": str(label)}
            for day in ("a", "b")
            for score, label in [(1, 1), (.5, 1), (.5, 0), (.1, 0)]
        ]
        report = validate_predictions(
            rows, score_column="score", label_column="y", batch_column="day",
            batch_capacity=2, exact_batch_yield=True, calibration_bins=2,
        )["batch_review"]["yield_comparison"]
        ranked = [sum(x) for x in product([1, 2], repeat=2)]
        uniform_day = [sum(pair) for pair in combinations([1, 1, 0, 0], 2)]
        uniform = [sum(x) for x in product(uniform_day, repeat=2)]
        wins = sum(a > b for a, b in product(ranked, uniform))
        self.assertAlmostEqual(report["probability_ranked_more_hits"], wins / (len(ranked) * len(uniform)))
        self.assertEqual(report["ranked_yield"], {"first": 2, "probabilities": [.25, .5, .25]})
        self.assertEqual(_draw_distribution(12, 0, 5), (0, [1.0]))
        with self.assertRaisesRegex(ValueError, "requires a batch"):
            validate_predictions(rows, score_column="score", label_column="y", exact_batch_yield=True)
