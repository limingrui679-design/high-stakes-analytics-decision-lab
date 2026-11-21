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
