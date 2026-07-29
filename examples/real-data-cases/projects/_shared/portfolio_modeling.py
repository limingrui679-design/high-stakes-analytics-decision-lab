#!/usr/bin/env python3
"""Predictive, operations, marketing, and model-validation modules."""

from __future__ import annotations

from portfolio_core import *

NUMERIC_ADULT = {
    "age",
    "fnlwgt",
    "education_num",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
}
ADULT_FEATURES = [
    field for field in ADULT_FIELDS if field not in {"income", "source_split"}
]


def _fit_naive_bayes(rows: list[dict[str, str]]) -> dict[str, Any]:
    classes = ("0", "1")
    labels = {"0": "<=50K", "1": ">50K"}
    counts = Counter(
        "1" if row["income"].replace(".", "") == ">50K" else "0" for row in rows
    )
    numeric: dict[str, dict[str, dict[str, float]]] = {}
    categories: dict[str, dict[str, Counter[str]]] = {}
    vocab: dict[str, set[str]] = {}
    for field in ADULT_FEATURES:
        if field in NUMERIC_ADULT:
            numeric[field] = {}
            for class_id in classes:
                values = [
                    float(row[field])
                    for row in rows
                    if ("1" if row["income"] == ">50K" else "0") == class_id
                ]
                numeric[field][class_id] = {
                    "mean": mean(values),
                    "variance": max(sd(values) ** 2, 1e-6),
                }
        else:
            vocab[field] = {row[field] for row in rows}
            categories[field] = {}
            for class_id in classes:
                categories[field][class_id] = Counter(
                    row[field]
                    for row in rows
                    if ("1" if row["income"] == ">50K" else "0") == class_id
                )
    return {
        "labels": labels,
        "class_counts": dict(counts),
        "total": len(rows),
        "numeric": numeric,
        "categories": {
            field: {
                class_id: dict(counter)
                for class_id, counter in class_counters.items()
            }
            for field, class_counters in categories.items()
        },
        "vocabulary": {field: sorted(values) for field, values in vocab.items()},
    }


def _predict_naive_bayes(model: dict[str, Any], row: dict[str, str]) -> float:
    scores = {}
    for class_id in ("0", "1"):
        class_count = model["class_counts"][class_id]
        score = math.log(class_count / model["total"])
        for field in ADULT_FEATURES:
            if field in NUMERIC_ADULT:
                parameters = model["numeric"][field][class_id]
                value = float(row[field])
                variance = parameters["variance"]
                score += -0.5 * (
                    math.log(2 * math.pi * variance)
                    + (value - parameters["mean"]) ** 2 / variance
                )
            else:
                count = model["categories"][field][class_id].get(row[field], 0)
                vocabulary = len(model["vocabulary"][field]) + 1
                score += math.log((count + 1) / (class_count + vocabulary))
        scores[class_id] = score
    difference = max(-700, min(700, scores["1"] - scores["0"]))
    return 1 / (1 + math.exp(-difference))


LOGISTIC_NUMERIC_FIELDS = [
    "age",
    "education_num",
    "capital_gain",
    "capital_loss",
    "hours_per_week",
]
LOGISTIC_CATEGORICAL_FIELDS = [
    "workclass",
    "marital_status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "native_country",
]


def _total_variation_distance(
    reference_counts: Counter[str],
    current_counts: Counter[str],
    reference_total: int,
    current_total: int,
) -> float:
    """Return a stable categorical-distribution distance."""
    values = sorted(set(reference_counts) | set(current_counts))
    return 0.5 * math.fsum(
        abs(
            reference_counts[value] / reference_total
            - current_counts[value] / current_total
        )
        for value in values
    )


def _build_sparse_encoder(rows: list[dict[str, str]]) -> dict[str, Any]:
    centers = {
        field: mean(float(row[field]) for row in rows)
        for field in LOGISTIC_NUMERIC_FIELDS
    }
    spreads = {
        field: sd(float(row[field]) for row in rows) or 1.0
        for field in LOGISTIC_NUMERIC_FIELDS
    }
    feature_names = [f"numeric:{field}" for field in LOGISTIC_NUMERIC_FIELDS]
    category_index: dict[str, dict[str, int]] = {}
    for field in LOGISTIC_CATEGORICAL_FIELDS:
        category_index[field] = {}
        values = sorted({row[field] for row in rows})
        for value in [*values, "__UNSEEN__"]:
            category_index[field][value] = len(feature_names)
            feature_names.append(f"{field}={value}")
    return {
        "numeric_fields": LOGISTIC_NUMERIC_FIELDS,
        "categorical_fields": LOGISTIC_CATEGORICAL_FIELDS,
        "centers": centers,
        "spreads": spreads,
        "category_index": category_index,
        "feature_names": feature_names,
        "numeric_clip_sd": 8.0,
    }


def _encode_sparse(
    encoder: dict[str, Any],
    row: dict[str, str],
) -> tuple[list[tuple[int, float]], int]:
    encoded: list[tuple[int, float]] = []
    clipped = 0
    for index, field in enumerate(encoder["numeric_fields"]):
        value = _safe_number(row.get(field))
        if value is None:
            standardized = 0.0
        else:
            standardized = (
                value - encoder["centers"][field]
            ) / encoder["spreads"][field]
        bounded = max(
            -encoder["numeric_clip_sd"],
            min(encoder["numeric_clip_sd"], standardized),
        )
        clipped += not math.isclose(bounded, standardized)
        if bounded:
            encoded.append((index, bounded))
    for field in encoder["categorical_fields"]:
        value = row.get(field, "")
        index = encoder["category_index"][field].get(
            value,
            encoder["category_index"][field]["__UNSEEN__"],
        )
        encoded.append((index, 1.0))
    return encoded, int(clipped)


def _fit_sparse_logistic(
    rows: list[dict[str, str]],
    labels: list[int],
    encoder: dict[str, Any],
    *,
    l2: float,
    epochs: int,
    seed: int,
    learning_rate: float = 0.035,
) -> dict[str, Any]:
    weights = [0.0] * len(encoder["feature_names"])
    prevalence = (sum(labels) + 0.5) / (len(labels) + 1)
    intercept = math.log(prevalence / (1 - prevalence))
    indices = list(range(len(rows)))
    rng = random.Random(seed)
    for epoch in range(epochs):
        rng.shuffle(indices)
        rate = learning_rate / math.sqrt(epoch + 1)
        shrink = max(0.0, 1 - rate * l2)
        weights = [weight * shrink for weight in weights]
        for row_index in indices:
            encoded, _ = _encode_sparse(encoder, rows[row_index])
            linear = intercept + sum(
                weights[index] * value for index, value in encoded
            )
            prediction = 1 / (
                1 + math.exp(-max(-35.0, min(35.0, linear)))
            )
            error = prediction - labels[row_index]
            intercept -= rate * error
            for index, value in encoded:
                weights[index] -= rate * error * value
    return {
        "model_type": "sparse one-hot logistic regression",
        "weights": weights,
        "intercept": intercept,
        "l2": l2,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "feature_count": len(weights),
    }


def _predict_sparse_logistic(
    model: dict[str, Any],
    encoder: dict[str, Any],
    row: dict[str, str],
) -> tuple[float, int]:
    encoded, clipped = _encode_sparse(encoder, row)
    linear = model["intercept"] + sum(
        model["weights"][index] * value for index, value in encoded
    )
    score = 1 / (1 + math.exp(-max(-35.0, min(35.0, linear))))
    return score, clipped


def _select_cost_threshold(
    labels: list[int],
    scores: list[float],
    *,
    false_negative_cost: float,
    false_positive_cost: float,
) -> dict[str, float]:
    candidates = sorted(set(scores))
    if len(candidates) > 200:
        candidates = [
            quantile(candidates, index / 199) for index in range(200)
        ]
    best = None
    for threshold in candidates:
        predictions = [score >= threshold for score in scores]
        false_negatives = sum(
            label and not prediction
            for label, prediction in zip(labels, predictions)
        )
        false_positives = sum(
            not label and prediction
            for label, prediction in zip(labels, predictions)
        )
        cost = (
            false_negative_cost * false_negatives
            + false_positive_cost * false_positives
        ) / len(labels)
        candidate = {
            "threshold": threshold,
            "mean_validation_cost": cost,
        }
        if best is None or (cost, threshold) < (
            best["mean_validation_cost"],
            best["threshold"],
        ):
            best = candidate
    assert best is not None
    return best


def _auc(labels: list[int], scores: list[float]) -> float:
    ordered = sorted(zip(scores, labels))
    rank_sum = 0.0
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        average_rank = (index + 1 + end) / 2
        rank_sum += average_rank * sum(label for _, label in ordered[index:end])
        index = end
    positives = sum(labels)
    negatives = len(labels) - positives
    return (
        (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)
        if positives and negatives
        else float("nan")
    )


def _classification_metrics(labels: list[int], scores: list[float], threshold: float) -> dict[str, Any]:
    predictions = [score >= threshold for score in scores]
    tp = sum(prediction and label for prediction, label in zip(predictions, labels))
    fp = sum(prediction and not label for prediction, label in zip(predictions, labels))
    tn = sum(not prediction and not label for prediction, label in zip(predictions, labels))
    fn = sum(not prediction and label for prediction, label in zip(predictions, labels))
    return {
        "n": len(labels),
        "prevalence": mean(labels),
        "auc": _auc(labels, scores),
        "brier": mean((score - label) ** 2 for score, label in zip(scores, labels)),
        "accuracy": (tp + tn) / len(labels),
        "true_positive_rate": tp / (tp + fn) if tp + fn else None,
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
    }


def _fit_mixed_nb(
    rows: list[dict[str, str]],
    labels: list[int],
    *,
    numeric_fields: list[str],
    categorical_fields: list[str],
) -> dict[str, Any]:
    if len(rows) != len(labels) or not rows:
        raise ValueError("Mixed naive Bayes requires aligned nonempty rows and labels.")
    class_counts = Counter(str(label) for label in labels)
    if set(class_counts) != {"0", "1"}:
        raise ValueError("Mixed naive Bayes requires both binary outcome classes.")
    numeric: dict[str, dict[str, dict[str, float]]] = {}
    categorical: dict[str, dict[str, dict[str, int]]] = {}
    vocabulary: dict[str, list[str]] = {}
    for field in numeric_fields:
        numeric[field] = {}
        for class_id in ("0", "1"):
            values = [
                float(row[field])
                for row, label in zip(rows, labels)
                if str(label) == class_id and _safe_number(row.get(field)) is not None
            ]
            numeric[field][class_id] = {
                "mean": mean(values),
                "variance": max(sd(values) ** 2, 1e-6),
            }
    for field in categorical_fields:
        values = sorted({row.get(field, "") or "__MISSING__" for row in rows})
        vocabulary[field] = values
        categorical[field] = {}
        for class_id in ("0", "1"):
            categorical[field][class_id] = dict(
                Counter(
                    row.get(field, "") or "__MISSING__"
                    for row, label in zip(rows, labels)
                    if str(label) == class_id
                )
            )
    return {
        "class_counts": dict(class_counts),
        "total": len(rows),
        "numeric_fields": numeric_fields,
        "categorical_fields": categorical_fields,
        "numeric": numeric,
        "categorical": categorical,
        "vocabulary": vocabulary,
        "smoothing": "Laplace add-one for categorical fields",
    }


def _predict_mixed_nb(model: dict[str, Any], row: dict[str, str]) -> float:
    log_scores: dict[str, float] = {}
    for class_id in ("0", "1"):
        class_count = model["class_counts"][class_id]
        log_score = math.log((class_count + 1) / (model["total"] + 2))
        for field in model["numeric_fields"]:
            value = _safe_number(row.get(field))
            if value is None:
                continue
            parameters = model["numeric"][field][class_id]
            variance = parameters["variance"]
            log_score += -0.5 * (
                math.log(2 * math.pi * variance)
                + (value - parameters["mean"]) ** 2 / variance
            )
        for field in model["categorical_fields"]:
            value = row.get(field, "") or "__MISSING__"
            count = model["categorical"][field][class_id].get(value, 0)
            vocabulary_size = len(model["vocabulary"][field]) + 1
            log_score += math.log(
                (count + 1) / (class_count + vocabulary_size)
            )
        log_scores[class_id] = log_score
    difference = max(-700.0, min(700.0, log_scores["1"] - log_scores["0"]))
    return 1 / (1 + math.exp(-difference))


def _fit_platt_calibrator(
    scores: list[float],
    labels: list[int],
    *,
    iterations: int = 2500,
    learning_rate: float = 0.04,
    l2: float = 0.001,
) -> dict[str, float | int | str]:
    if len(scores) != len(labels) or not scores:
        raise ValueError("Calibration requires aligned nonempty scores and labels.")
    epsilon = 1e-15
    logits = []
    for score in scores:
        clipped = min(1 - epsilon, max(epsilon, score))
        logits.append(math.log(clipped / (1 - clipped)))
    center = mean(logits)
    spread = sd(logits) or 1.0
    standardized = [(value - center) / spread for value in logits]
    intercept = math.log((sum(labels) + 0.5) / (len(labels) - sum(labels) + 0.5))
    slope = 0.0
    for _ in range(iterations):
        predictions = [
            1 / (1 + math.exp(-max(-35.0, min(35.0, intercept + slope * value))))
            for value in standardized
        ]
        gradient_intercept = mean(
            prediction - label
            for prediction, label in zip(predictions, labels)
        )
        gradient_slope = (
            mean(
                (prediction - label) * value
                for prediction, label, value in zip(
                    predictions, labels, standardized
                )
            )
            + l2 * slope
        )
        intercept -= learning_rate * gradient_intercept
        slope -= learning_rate * gradient_slope
    return {
        "method": "validation-set Platt calibration",
        "center": center,
        "spread": spread,
        "intercept": intercept,
        "slope": slope,
        "iterations": iterations,
        "l2": l2,
    }


def _apply_platt(
    calibrator: dict[str, Any],
    score: float,
) -> float:
    epsilon = 1e-15
    clipped = min(1 - epsilon, max(epsilon, score))
    logit = math.log(clipped / (1 - clipped))
    standardized = (logit - calibrator["center"]) / calibrator["spread"]
    value = calibrator["intercept"] + calibrator["slope"] * standardized
    return 1 / (1 + math.exp(-max(-35.0, min(35.0, value))))


def _calibration_bins(
    labels: list[int],
    scores: list[float],
    *,
    bins: int = 10,
) -> list[dict[str, Any]]:
    if not 2 <= bins <= min(50, len(labels)):
        raise ValueError("Calibration bins must be between 2 and min(50, n).")
    ordered = sorted(zip(scores, labels))
    result = []
    for bin_index in range(bins):
        left = bin_index * len(ordered) // bins
        right = (bin_index + 1) * len(ordered) // bins
        subset = ordered[left:right]
        if not subset:
            continue
        result.append(
            {
                "bin": bin_index + 1,
                "n": len(subset),
                "mean_score": mean(score for score, _ in subset),
                "observed_rate": mean(label for _, label in subset),
                "score_min": subset[0][0],
                "score_max": subset[-1][0],
            }
        )
    return result


def _capacity_metrics(
    labels: list[int],
    scores: list[float],
    capacity_share: float,
) -> dict[str, float | int]:
    if not 0 < capacity_share <= 1:
        raise ValueError("Capacity share must be in (0, 1].")
    if len(labels) != len(scores) or not labels:
        raise ValueError("Capacity metrics require aligned nonempty inputs.")
    selected_count = max(1, math.ceil(len(labels) * capacity_share))
    ranked = sorted(
        range(len(scores)),
        key=lambda index: (-scores[index], index),
    )
    selected = ranked[:selected_count]
    captured = sum(labels[index] for index in selected)
    positives = sum(labels)
    prevalence = positives / len(labels)
    precision = captured / selected_count
    return {
        "capacity_share": selected_count / len(labels),
        "selected_count": selected_count,
        "positive_capture": captured / positives if positives else 0.0,
        "precision": precision,
        "lift_vs_random": precision / prevalence if prevalence else 0.0,
    }


def _row_block_indices(
    size: int,
    block_size: int,
    rng: random.Random,
) -> list[int]:
    if size < 1 or not 1 <= block_size <= size:
        raise ValueError("Invalid row-block bootstrap dimensions.")
    sampled: list[int] = []
    while len(sampled) < size:
        start = rng.randrange(size)
        sampled.extend((start + offset) % size for offset in range(block_size))
    return sampled[:size]


def _day_block_indices(
    rows: list[dict[str, str]],
    *,
    date_field: str,
    block_days: int,
    rng: random.Random,
) -> list[int]:
    if block_days < 1:
        raise ValueError("Calendar block length must be positive.")
    dates = sorted({row[date_field][:10] for row in rows})
    by_date: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        by_date[row[date_field][:10]].append(index)
    sampled: list[int] = []
    while len(sampled) < len(rows):
        start = rng.randrange(len(dates))
        for offset in range(block_days):
            sampled.extend(by_date[dates[(start + offset) % len(dates)]])
    return sampled[: len(rows)]


def _correlated_capacity_decision(
    labels: list[int],
    scores: list[float],
    capacities: list[float],
    *,
    sample_indices: list[list[int]],
    utility_weights: dict[str, float],
) -> dict[str, Any]:
    if not math.isclose(sum(utility_weights.values()), 1.0, abs_tol=1e-9):
        raise ValueError("Capacity-decision utility weights must sum to one.")
    point = {
        f"{capacity:.0%}": _capacity_metrics(labels, scores, capacity)
        for capacity in capacities
    }
    samples = {
        label: {
            "positive_capture": [],
            "precision": [],
            "capacity_share": [],
            "utility": [],
        }
        for label in point
    }
    winners = Counter()
    for indices in sample_indices:
        sample_labels = [labels[index] for index in indices]
        sample_scores = [scores[index] for index in indices]
        utilities: dict[str, float] = {}
        for capacity in capacities:
            label = f"{capacity:.0%}"
            metrics = _capacity_metrics(
                sample_labels,
                sample_scores,
                capacity,
            )
            utility = (
                utility_weights["positive_capture"] * metrics["positive_capture"]
                + utility_weights["precision"] * metrics["precision"]
                + utility_weights["workload"]
                * (1 - metrics["capacity_share"] / max(capacities))
            )
            for key in ("positive_capture", "precision", "capacity_share"):
                samples[label][key].append(round(float(metrics[key]), 8))
            samples[label]["utility"].append(round(utility, 8))
            utilities[label] = utility
        winner = max(
            utilities,
            key=lambda label: (utilities[label], -float(label.rstrip("%"))),
        )
        winners[winner] += 1
    for label, metrics in point.items():
        utility = (
            utility_weights["positive_capture"] * metrics["positive_capture"]
            + utility_weights["precision"] * metrics["precision"]
            + utility_weights["workload"]
            * (1 - metrics["capacity_share"] / max(capacities))
        )
        metrics["utility"] = utility
        metrics["bootstrap"] = samples[label]
        metrics["probability_best"] = winners[label] / len(sample_indices)
        metrics["utility_interval_95"] = [
            quantile(samples[label]["utility"], 0.025),
            quantile(samples[label]["utility"], 0.975),
        ]
    recommended = max(
        point,
        key=lambda label: (
            point[label]["probability_best"],
            point[label]["utility"],
        ),
    )
    return {
        "recommended_capacity": recommended,
        "options": point,
        "utility_weights": utility_weights,
        "dependence_design": (
            "Every capacity option is evaluated on the same block-resampled "
            "replicate, preserving shared campaign or calendar shocks and the "
            "cross-option dependence required for probability-best estimates."
        ),
        "decision_use": "candidate for prospective validation only",
    }


def analyze_adult(project_root: Path) -> dict[str, Any]:
    rows = read_csv(project_root / "data/processed/analysis.csv")
    source_train = [row for row in rows if row["source_split"] == "train"]
    test = [row for row in rows if row["source_split"] == "test"]
    rng = random.Random(20260727)
    by_label: dict[int, list[dict[str, str]]] = {0: [], 1: []}
    for row in source_train:
        label = 1 if row["income"].replace(".", "") == ">50K" else 0
        by_label[label].append(row)
    development: list[dict[str, str]] = []
    validation: list[dict[str, str]] = []
    for label_rows in by_label.values():
        rng.shuffle(label_rows)
        cut = int(len(label_rows) * 0.8)
        development.extend(label_rows[:cut])
        validation.extend(label_rows[cut:])
    rng.shuffle(development)
    rng.shuffle(validation)

    def labels_for(materialized: list[dict[str, str]]) -> list[int]:
        return [
            1 if row["income"].replace(".", "") == ">50K" else 0
            for row in materialized
        ]

    development_labels = labels_for(development)
    validation_labels = labels_for(validation)
    labels = [1 if row["income"].replace(".", "") == ">50K" else 0 for row in test]
    encoder = _build_sparse_encoder(development)
    hyperparameter_results = {}
    candidate_models = {}
    for index, l2 in enumerate((0.0, 0.0005, 0.005)):
        model = _fit_sparse_logistic(
            development,
            development_labels,
            encoder,
            l2=l2,
            epochs=8,
            seed=20260727 + index,
        )
        candidate_models[str(l2)] = model
        validation_scores = [
            _predict_sparse_logistic(model, encoder, row)[0]
            for row in validation
        ]
        hyperparameter_results[str(l2)] = {
            "validation_auc": _auc(validation_labels, validation_scores),
            "validation_brier": mean(
                (score - label) ** 2
                for score, label in zip(validation_scores, validation_labels)
            ),
        }
    selected_l2 = max(
        hyperparameter_results,
        key=lambda value: (
            hyperparameter_results[value]["validation_auc"],
            -hyperparameter_results[value]["validation_brier"],
        ),
    )
    selected_development_model = candidate_models[selected_l2]
    validation_scores = [
        _predict_sparse_logistic(
            selected_development_model,
            encoder,
            row,
        )[0]
        for row in validation
    ]
    threshold_selection = _select_cost_threshold(
        validation_labels,
        validation_scores,
        false_negative_cost=3.0,
        false_positive_cost=1.0,
    )
    final_encoder = _build_sparse_encoder(source_train)
    final_model = _fit_sparse_logistic(
        source_train,
        labels_for(source_train),
        final_encoder,
        l2=float(selected_l2),
        epochs=8,
        seed=20260827,
    )
    predictions_with_clipping = [
        _predict_sparse_logistic(final_model, final_encoder, row)
        for row in test
    ]
    scores = [item[0] for item in predictions_with_clipping]
    clipped_values = sum(item[1] for item in predictions_with_clipping)
    threshold = threshold_selection["threshold"]
    overall = _classification_metrics(labels, scores, threshold)
    baseline_accuracy = max(mean(labels), 1 - mean(labels))
    naive_bayes_model = _fit_naive_bayes(source_train)
    naive_bayes_scores = [
        _predict_naive_bayes(naive_bayes_model, row) for row in test
    ]
    naive_bayes_metrics = _classification_metrics(
        labels,
        naive_bayes_scores,
        0.5,
    )
    subgroup = {}
    for field in ("sex", "race"):
        subgroup[field] = {}
        for value in sorted({row[field] for row in test}):
            indices = [index for index, row in enumerate(test) if row[field] == value]
            metrics = _classification_metrics(
                [labels[index] for index in indices],
                [scores[index] for index in indices],
                threshold,
            )
            subgroup[field][value] = metrics
    calibration = _calibration_bins(labels, scores, bins=10)

    numeric_shift = {}
    for field in LOGISTIC_NUMERIC_FIELDS:
        train_values = [float(row[field]) for row in source_train]
        test_values = [float(row[field]) for row in test]
        numeric_shift[field] = {
            "standardized_mean_shift": (
                mean(test_values) - mean(train_values)
            )
            / (sd(train_values) or 1.0),
            "train_mean": mean(train_values),
            "test_mean": mean(test_values),
        }
    categorical_shift = {}
    for field in LOGISTIC_CATEGORICAL_FIELDS:
        train_counts = Counter(row[field] for row in source_train)
        test_counts = Counter(row[field] for row in test)
        total_variation = _total_variation_distance(
            train_counts,
            test_counts,
            len(source_train),
            len(test),
        )
        categorical_shift[field] = {
            "total_variation_distance": total_variation,
            "unseen_test_categories": sorted(
                value for value in test_counts if value not in train_counts
            ),
        }

    abnormal_rows = []
    for row in test[:250]:
        abnormal = dict(row)
        for field in LOGISTIC_CATEGORICAL_FIELDS:
            abnormal[field] = "__UNSEEN_INPUT__"
        abnormal["age"] = "999"
        abnormal["hours_per_week"] = "-20"
        abnormal_rows.append(abnormal)
    abnormal_predictions = [
        _predict_sparse_logistic(final_model, final_encoder, row)
        for row in abnormal_rows
    ]
    robustness = {
        "abnormal_input_rows": len(abnormal_rows),
        "finite_scores": all(
            math.isfinite(score) and 0 <= score <= 1
            for score, _ in abnormal_predictions
        ),
        "numeric_values_clipped": sum(
            clipped for _, clipped in abnormal_predictions
        ),
        "mean_score_shift_vs_same_clean_rows": (
            mean(score for score, _ in abnormal_predictions)
            - mean(scores[: len(abnormal_rows)])
        ),
        "failure_behavior": (
            "Unseen categories map to explicit fallback features; numeric inputs "
            "are clipped at eight training standard deviations. Production use "
            "would reject rather than silently repair impossible values."
        ),
    }

    coefficients = sorted(
        zip(final_encoder["feature_names"], final_model["weights"]),
        key=lambda item: abs(item[1]),
        reverse=True,
    )[:20]
    prediction_rows = [
        {
            "row_id": index + 1,
            "label": labels[index],
            "score": round(scores[index], 8),
            "sex": test[index]["sex"],
            "race": test[index]["race"],
        }
        for index in range(len(test))
    ]
    write_csv(
        project_root / "outputs/predictions.csv",
        prediction_rows,
        ["row_id", "label", "score", "sex", "race"],
    )
    model_payload = {
        "selected_hyperparameter": {"l2": float(selected_l2), "epochs": 8},
        "hyperparameter_validation": hyperparameter_results,
        "threshold_selection": {
            **threshold_selection,
            "false_negative_cost": 3.0,
            "false_positive_cost": 1.0,
            "status": "illustrative analyst cost ratio",
        },
        "encoder": final_encoder,
        "model": final_model,
        "top_absolute_coefficients": [
            {"feature": feature, "coefficient": coefficient}
            for feature, coefficient in coefficients
        ],
    }
    write_json(project_root / "outputs/model.json", model_payload)
    (project_root / "outputs/model-card.md").write_text(
        "\n".join(
            [
                "# Model card · Census-income benchmark",
                "",
                "## Intended use",
                "",
                "Reproducible classification and validation benchmark only. It is "
                "not authorized for employment, credit, benefits, immigration, "
                "eligibility, or any consequential decision.",
                "",
                "## Data and split",
                "",
                f"- Development source: {len(source_train):,} Adult training records.",
                f"- Independent source test: {len(test):,} Adult test records.",
                "- Hyperparameters use a stratified 80/20 split inside the training file.",
                "- The source test file is untouched until final evaluation.",
                "",
                "## Model and metrics",
                "",
                "- Majority baseline, mixed naive Bayes baseline, and sparse one-hot logistic regression.",
                f"- Selected L2: {selected_l2}; final AUC: {overall['auc']:.3f}; Brier: {overall['brier']:.3f}.",
                f"- Decision threshold {threshold:.4f} comes from an illustrative 3:1 false-negative/false-positive validation cost.",
                "",
                "## Failure modes and governance",
                "",
                "- Historical 1994 Census-derived patterns are not current causal relationships.",
                "- Recorded sex and race diagnostics expose error variation; they do not legitimate use of those attributes.",
                "- Unknown categories require review; impossible numeric inputs should be rejected.",
                "- Human review, notice, appeal, rollback, and drift monitoring would be mandatory before any new use.",
                "",
                "## Explainability boundary",
                "",
                "Coefficients describe model associations after encoding. They are not causal effects or policy levers.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (project_root / "outputs/deployment-checklist.md").write_text(
        "\n".join(
            [
                "# Pre-deployment checklist",
                "",
                "- [ ] New target population and decision use are explicitly approved.",
                "- [ ] Current, representative data replace the 1994 benchmark.",
                "- [ ] Feature availability is verified at the decision time.",
                "- [ ] Calibration, error cost, and subgroup performance pass prospective thresholds.",
                "- [ ] Unknown and impossible inputs fail safely.",
                "- [ ] Human review, notice, appeal, fallback, rollback, and monitoring owners are named.",
                "- [ ] A prospective impact study tests whether action improves outcomes.",
                "",
                "Repository status: **not deployment-ready**.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    result = {
        "project_id": "census-income-ai",
        "data": {
            "source_train_rows": len(source_train),
            "development_rows": len(development),
            "validation_rows": len(validation),
            "independent_test_rows": len(test),
        },
        "models": {
            "majority_baseline_accuracy": baseline_accuracy,
            "naive_bayes_baseline": naive_bayes_metrics,
            "advanced_model": "sparse one-hot logistic regression",
            "hyperparameter_validation": hyperparameter_results,
            "selected_l2": float(selected_l2),
        },
        "threshold": threshold,
        "threshold_governance": (
            "Selected only on validation under an illustrative 3:1 error-cost "
            "ratio; it has no real decision-owner approval."
        ),
        "overall": overall,
        "subgroup_metrics": subgroup,
        "calibration": calibration,
        "drift_diagnostics": {
            "numeric": numeric_shift,
            "categorical": categorical_shift,
        },
        "robustness": robustness,
        "explainability": {
            "top_absolute_coefficients": [
                {"feature": feature, "coefficient": coefficient}
                for feature, coefficient in coefficients
            ],
            "boundary": "Associational model coefficients are not causal effects.",
        },
        "model_artifacts": [
            "outputs/model.json",
            "outputs/model-card.md",
            "outputs/deployment-checklist.md",
        ],
        "decision_boundary": (
            "Benchmark classification only; not validated for eligibility, credit, "
            "employment, or other consequential decisions."
        ),
    }
    source = "UCI Adult, DOI 10.24432/C5XW20; source-defined train/test split"
    figures = project_root / "outputs/figures"
    svg_line(
        figures / "calibration.svg",
        "Calibration on the held-out Adult test split",
        "Mean predicted probability versus observed >50K rate by populated score bin",
        [
            ("Observed", [(item["mean_score"], item["observed_rate"]) for item in calibration]),
            ("Ideal", [(0, 0), (1, 1)]),
        ],
        source,
        y_percent=True,
    )
    sex_items = [
        (
            value,
            metrics["false_positive_rate"] if metrics["false_positive_rate"] is not None else 0,
        )
        for value, metrics in subgroup["sex"].items()
    ]
    svg_bar(
        figures / "subgroup-fpr.svg",
        "False-positive rate by recorded sex",
        f"Held-out source test split at validation-selected threshold {threshold:.3f}",
        sex_items,
        source,
        percent=True,
    )
    svg_bar(
        figures / "model-comparison.svg",
        "Independent-test discrimination by model",
        "Source-provided Adult test file; majority baseline has no rank AUC",
        [
            ("Naive Bayes", naive_bayes_metrics["auc"]),
            ("Sparse logistic", overall["auc"]),
        ],
        source,
    )
    return result


def _block(hour: int) -> str:
    return ("00–05", "06–11", "12–17", "18–23")[hour // 6]


def _daily_block_demand(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        date = row["dteday"]
        record = grouped.setdefault(
            date,
            {"date": date, "wet": False, **{block: 0.0 for block in ("00–05", "06–11", "12–17", "18–23")}},
        )
        record[_block(int(row["hr"]))] += float(row["cnt"])
        record["wet"] = record["wet"] or int(row["weathersit"]) >= 3
    return list(grouped.values())


def _allocation_metrics(
    allocation: tuple[int, int, int, int],
    days: list[dict[str, Any]],
    capacity: float,
) -> dict[str, float]:
    blocks = ("00–05", "06–11", "12–17", "18–23")
    unmet = []
    wet_unmet = []
    for day in days:
        demand = sum(day[block] for block in blocks)
        shortfall = sum(
            max(0.0, day[block] - allocation[index] * capacity)
            for index, block in enumerate(blocks)
        )
        rate = shortfall / demand if demand else 0
        unmet.append(rate)
        if day["wet"]:
            wet_unmet.append(rate)
    return {
        "unmet_rate": mean(unmet),
        "p90_unmet_rate": quantile(unmet, 0.90),
        "wet_unmet_rate": mean(wet_unmet),
        "shift_imbalance": (max(allocation) - min(allocation)) / sum(allocation),
    }


def _proportional_allocation(days: list[dict[str, Any]], total: int) -> tuple[int, ...]:
    blocks = ("00–05", "06–11", "12–17", "18–23")
    averages = [mean(day[block] for day in days) for block in blocks]
    remaining = total - 8
    raw = [2 + remaining * value / sum(averages) for value in averages]
    allocation = [math.floor(value) for value in raw]
    while sum(allocation) < total:
        index = max(range(4), key=lambda item: raw[item] - allocation[item])
        allocation[index] += 1
    return tuple(allocation)


def _enumerate_allocations(
    days: list[dict[str, Any]],
    *,
    total_units: int,
    capacity: float,
    minimum: int = 2,
) -> list[tuple[tuple[int, int, int, int], dict[str, float], float]]:
    candidates = []
    for first in range(minimum, total_units - 3 * minimum + 1):
        for second in range(
            minimum,
            total_units - first - 2 * minimum + 1,
        ):
            for third in range(
                minimum,
                total_units - first - second - minimum + 1,
            ):
                fourth = total_units - first - second - third
                if fourth < minimum:
                    continue
                allocation = (first, second, third, fourth)
                metrics = _allocation_metrics(allocation, days, capacity)
                objective = (
                    metrics["unmet_rate"] + 0.5 * metrics["p90_unmet_rate"]
                )
                candidates.append((allocation, metrics, objective))
    return candidates


def _pareto_allocations(
    candidates: list[
        tuple[tuple[int, int, int, int], dict[str, float], float]
    ],
) -> list[dict[str, Any]]:
    ordered = sorted(
        candidates,
        key=lambda item: (
            item[1]["unmet_rate"],
            item[1]["p90_unmet_rate"],
            item[1]["shift_imbalance"],
        ),
    )
    frontier: list[
        tuple[tuple[int, int, int, int], dict[str, float], float]
    ] = []
    for candidate in ordered:
        metrics = candidate[1]
        dominated = any(
            existing[1]["p90_unmet_rate"] <= metrics["p90_unmet_rate"]
            and existing[1]["shift_imbalance"] <= metrics["shift_imbalance"]
            for existing in frontier
        )
        if dominated:
            continue
        frontier = [
            existing
            for existing in frontier
            if not (
                metrics["p90_unmet_rate"]
                <= existing[1]["p90_unmet_rate"]
                and metrics["shift_imbalance"]
                <= existing[1]["shift_imbalance"]
            )
        ]
        frontier.append(candidate)
    return [
        {
            "allocation": allocation,
            "unmet_rate": metrics["unmet_rate"],
            "p90_unmet_rate": metrics["p90_unmet_rate"],
            "shift_imbalance": metrics["shift_imbalance"],
        }
        for allocation, metrics, _ in frontier
    ]


def analyze_bike(project_root: Path) -> dict[str, Any]:
    rows = read_csv(project_root / "data/processed/analysis.csv")
    train = [row for row in rows if row["yr"] == "0"]
    test = [row for row in rows if row["yr"] == "1"]
    lookup: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in train:
        lookup[(row["workingday"], row["hr"], row["weathersit"])].append(float(row["cnt"]))
    overall_mean = mean(float(row["cnt"]) for row in train)
    predictions = [
        mean(lookup.get((row["workingday"], row["hr"], row["weathersit"]), [overall_mean]))
        for row in test
    ]
    actuals = [float(row["cnt"]) for row in test]
    mae = mean(abs(actual - predicted) for actual, predicted in zip(actuals, predictions))
    baseline_mae = mean(abs(actual - overall_mean) for actual in actuals)
    train_days = _daily_block_demand(train)
    test_days = _daily_block_demand(test)
    total_units, capacity = 40, 120.0
    candidates = _enumerate_allocations(
        train_days,
        total_units=total_units,
        capacity=capacity,
    )
    best_allocation, best_metrics, best_objective = min(
        candidates,
        key=lambda item: (item[2], item[0]),
    )
    allocations = {
        "equal-baseline": (10, 10, 10, 10),
        "demand-proportional": _proportional_allocation(train_days, total_units),
        "robust-optimized": best_allocation,
    }
    policies = {}
    rng = random.Random(41)
    for name, allocation in allocations.items():
        metrics = _allocation_metrics(allocation, test_days, capacity)
        boot = {key: [] for key in metrics}
        for _ in range(400):
            sample = [test_days[rng.randrange(len(test_days))] for _ in test_days]
            sampled = _allocation_metrics(allocation, sample, capacity)
            for key, value in sampled.items():
                boot[key].append(round(value, 7))
        policies[name] = {
            "allocation": dict(zip(("00–05", "06–11", "12–17", "18–23"), allocation)),
            **metrics,
            "bootstrap": boot,
        }
    shadow_values = {}
    previous_objective = None
    for units in range(38, 43):
        unit_candidates = _enumerate_allocations(
            train_days,
            total_units=units,
            capacity=capacity,
        )
        allocation, metrics, objective = min(
            unit_candidates,
            key=lambda item: (item[2], item[0]),
        )
        shadow_values[str(units)] = {
            "best_allocation": allocation,
            "objective": objective,
            "marginal_objective_improvement_from_previous_unit": (
                None
                if previous_objective is None
                else previous_objective - objective
            ),
        }
        previous_objective = objective
    blocks = ("00–05", "06–11", "12–17", "18–23")
    perfect_foresight_rates = []
    for day in test_days:
        demand = sum(day[block] for block in blocks)
        best_shortfall = float("inf")
        for allocation, _, _ in candidates:
            shortfall = sum(
                max(0.0, day[block] - allocation[index] * capacity)
                for index, block in enumerate(blocks)
            )
            best_shortfall = min(best_shortfall, shortfall)
        perfect_foresight_rates.append(
            best_shortfall / demand if demand else 0.0
        )
    robust_test_unmet = policies["robust-optimized"]["unmet_rate"]
    perfect_foresight_unmet = mean(perfect_foresight_rates)
    pareto = _pareto_allocations(candidates)
    result = {
        "project_id": "bike-demand-operations",
        "data": {"train_hours": len(train), "test_hours": len(test)},
        "forecast": {
            "model": "training-year mean by working-day, hour, and weather state",
            "test_mae": mae,
            "overall_mean_baseline_mae": baseline_mae,
            "relative_mae_improvement": 1 - mae / baseline_mae,
        },
        "optimization": {
            "system_boundary": (
                "Four six-hour service blocks, one planning day, system-level "
                "demand, and a fixed homogeneous resource pool"
            ),
            "decision_variables": "integer units assigned to each time block",
            "resource_units": total_units,
            "capacity_per_unit_per_block": capacity,
            "minimum_units_per_block": 2,
            "objective": "mean unmet share + 0.5 × p90 unmet share on 2011",
            "feasible_allocations_enumerated": len(candidates),
            "enumeration_justification": (
                "Four bounded integer variables yield a small finite feasible "
                f"set of {len(candidates):,} allocations; every feasible point is checked."
            ),
            "training_optimum": {
                "allocation": dict(zip(blocks, best_allocation)),
                "metrics": best_metrics,
                "objective": best_objective,
                "binding_minimum_blocks": [
                    block
                    for block, units in zip(blocks, best_allocation)
                    if units == 2
                ],
            },
            "policies_2012_evaluation": policies,
            "resource_shadow_value_sensitivity": shadow_values,
            "pareto_frontier": pareto,
            "value_of_perfect_information_upper_bound": {
                "robust_static_test_unmet_rate": robust_test_unmet,
                "perfect_foresight_test_unmet_rate": perfect_foresight_unmet,
                "maximum_avoidable_unmet_share": (
                    robust_test_unmet - perfect_foresight_unmet
                ),
                "boundary": (
                    "Perfect foresight is an unattainable upper bound, not a forecast "
                    "or the value of a purchasable information system."
                ),
            },
        },
        "uncertainty_decomposition": {
            "parameter_uncertainty": (
                "Day-block bootstrap of held-out policy metrics."
            ),
            "operating_randomness": (
                "Observed day-to-day and wet-day demand variation in 2012."
            ),
            "shared_shocks": (
                "Each bootstrap day is shared by every policy, preserving common "
                "weather and demand shocks across alternatives."
            ),
        },
        "implementation": {
            "pilot": "time-limited reversible scheduling pilot",
            "monitor": ["unmet demand", "wet-day unmet demand", "shift imbalance"],
            "reversal_conditions": [
                "Station-level imbalance dominates system-block demand.",
                "Unit capacity differs materially by block.",
                "Labor, travel-time, or maintenance constraints invalidate feasibility.",
            ],
        },
    }
    source = "UCI Bike Sharing, DOI 10.24432/C5W894; train 2011, test 2012"
    figures = project_root / "outputs/figures"
    hourly = defaultdict(list)
    for row in rows:
        hourly[int(row["hr"])].append(float(row["cnt"]))
    svg_line(
        figures / "hourly-demand.svg",
        "Average hourly bike demand",
        "Capital Bikeshare, 2011–2012; observed rentals by hour",
        [("Average demand", [(hour, mean(values)) for hour, values in sorted(hourly.items())])],
        source,
    )
    svg_bar(
        figures / "allocation-unmet.svg",
        "Unmet-demand share by allocation policy",
        "Out-of-time 2012 evaluation; 40 resource units and 120 rentals/unit/block",
        [(name.replace("-", " ").title(), value["unmet_rate"]) for name, value in policies.items()],
        source,
        percent=True,
    )
    svg_line(
        figures / "resource-shadow-value.svg",
        "Training objective by available resource units",
        "Exhaustive integer solution for 38–42 units",
        [
            (
                "Objective",
                [
                    (float(units), value["objective"])
                    for units, value in shadow_values.items()
                ],
            )
        ],
        source,
        y_percent=True,
    )
    return result


def analyze_bank_marketing(project_root: Path) -> dict[str, Any]:
    rows = read_csv(project_root / "data/processed/analysis.csv")
    config = load_json(project_root / "config.json")
    first_cut = int(len(rows) * config["parameters"]["split_fractions"][0])
    second_cut = int(
        len(rows)
        * sum(config["parameters"]["split_fractions"][:2])
    )
    train, validation, test = (
        rows[:first_cut],
        rows[first_cut:second_cut],
        rows[second_cut:],
    )

    def labels_for(materialized: list[dict[str, str]]) -> list[int]:
        return [1 if row["y"] == "yes" else 0 for row in materialized]

    train_labels = labels_for(train)
    validation_labels = labels_for(validation)
    test_labels = labels_for(test)
    base_numeric = ["age", "campaign", "pdays", "previous"]
    base_categorical = [
        "job",
        "marital",
        "education",
        "default",
        "housing",
        "loan",
        "contact",
        "poutcome",
    ]
    model_specs = {
        "client-history-only": {
            "numeric": base_numeric,
            "categorical": base_categorical,
        },
        "client-history-plus-campaign-context": {
            "numeric": [
                *base_numeric,
                "emp.var.rate",
                "cons.price.idx",
                "cons.conf.idx",
                "euribor3m",
                "nr.employed",
            ],
            "categorical": [*base_categorical, "month", "day_of_week"],
        },
    }
    candidate_results: dict[str, Any] = {}
    fitted: dict[str, dict[str, Any]] = {}
    for name, spec in model_specs.items():
        model = _fit_mixed_nb(
            train,
            train_labels,
            numeric_fields=spec["numeric"],
            categorical_fields=spec["categorical"],
        )
        fitted[name] = model
        validation_scores = [
            _predict_mixed_nb(model, row) for row in validation
        ]
        candidate_results[name] = {
            "validation_auc": _auc(validation_labels, validation_scores),
            "validation_brier": mean(
                (score - label) ** 2
                for score, label in zip(validation_scores, validation_labels)
            ),
            "features": spec,
        }
    selected_name = max(
        candidate_results,
        key=lambda name: (
            candidate_results[name]["validation_auc"],
            -candidate_results[name]["validation_brier"],
        ),
    )
    selected_model = fitted[selected_name]
    selected_validation_scores = [
        _predict_mixed_nb(selected_model, row) for row in validation
    ]
    calibrator = _fit_platt_calibrator(
        selected_validation_scores,
        validation_labels,
    )
    raw_test_scores = [
        _predict_mixed_nb(selected_model, row) for row in test
    ]
    test_scores = [
        _apply_platt(calibrator, score) for score in raw_test_scores
    ]
    test_overall = _classification_metrics(test_labels, test_scores, 0.5)
    business_rule_scores = [
        1.0 if row["poutcome"] == "success" else 0.0 for row in test
    ]
    business_rule = {
        "rule": "prior campaign outcome equals success",
        "test": _classification_metrics(
            test_labels,
            business_rule_scores,
            0.5,
        ),
        "top_10_percent_comparison": _capacity_metrics(
            test_labels,
            business_rule_scores,
            0.10,
        ),
    }
    calibration = _calibration_bins(test_labels, test_scores, bins=10)
    capacities = config["parameters"]["contact_capacity_shares"]
    rng = random.Random(config["analysis_seed"])
    bootstrap_indices = [
        _row_block_indices(
            len(test),
            config["parameters"]["bootstrap_block_rows"],
            rng,
        )
        for _ in range(config["parameters"]["bootstrap_samples"])
    ]
    decision = _correlated_capacity_decision(
        test_labels,
        test_scores,
        capacities,
        sample_indices=bootstrap_indices,
        utility_weights={
            "positive_capture": 0.50,
            "precision": 0.30,
            "workload": 0.20,
        },
    )
    decision.update(
        {
            "question": (
                "Which review-capacity tier should advance to a randomized "
                "campaign test?"
            ),
            "alternatives": [f"review top {capacity:.0%}" for capacity in capacities],
            "constraint": "contact review capacity cannot exceed 20% in the scenario set",
            "source_of_metrics": "untouched final 20% source-order holdout",
            "source_of_weights": (
                "repository-author exploratory trade-off register; no bank approval"
            ),
            "approval_chain": [
                {
                    "role": "repository author",
                    "status": "self-reviewed for exploratory demonstration",
                    "scope": "prospective test candidate only",
                }
            ],
            "reversal_conditions": [
                "A randomized test shows no incremental response lift.",
                "Contact costs or customer-burden constraints dominate observed response concentration.",
                "Performance degrades on a true dated out-of-period sample.",
            ],
        }
    )
    block_sensitivity = {}
    for block_size in (25, 50, 100):
        sensitivity_rng = random.Random(config["analysis_seed"] + block_size)
        sensitivity_indices = [
            _row_block_indices(len(test), block_size, sensitivity_rng)
            for _ in range(200)
        ]
        sensitivity = _correlated_capacity_decision(
            test_labels,
            test_scores,
            capacities,
            sample_indices=sensitivity_indices,
            utility_weights=decision["utility_weights"],
        )
        block_sensitivity[str(block_size)] = {
            "recommended_capacity": sensitivity["recommended_capacity"],
            "probability_best": {
                label: value["probability_best"]
                for label, value in sensitivity["options"].items()
            },
        }

    subgroup = {}
    for field in ("contact",):
        subgroup[field] = {}
        for value in sorted({row[field] for row in test}):
            indices = [
                index for index, row in enumerate(test) if row[field] == value
            ]
            subgroup[field][value] = {
                "n": len(indices),
                "response_rate": mean(test_labels[index] for index in indices),
                "auc": _auc(
                    [test_labels[index] for index in indices],
                    [test_scores[index] for index in indices],
                ),
            }
    prediction_rows = [
        {
            "source_order": row["source_order"],
            "label": test_labels[index],
            "score": round(test_scores[index], 8),
            "contact": row["contact"],
            "month": row["month"],
        }
        for index, row in enumerate(test)
    ]
    write_csv(
        project_root / "outputs/predictions.csv",
        prediction_rows,
        ["source_order", "label", "score", "contact", "month"],
    )
    write_json(
        project_root / "outputs/model.json",
        {
            "selected_candidate": selected_name,
            "classifier": selected_model,
            "calibration": calibrator,
        },
    )
    write_json(project_root / "outputs/decision-analysis.json", decision)

    month_order = [
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]
    monthly = {}
    for month in month_order:
        relevant = [row for row in rows if row["month"] == month]
        if relevant:
            monthly[month] = {
                "contacts": len(relevant),
                "response_rate": mean(row["y"] == "yes" for row in relevant),
            }
    result = {
        "project_id": "bank-marketing-response",
        "data": {
            "rows": len(rows),
            "train_rows": len(train),
            "validation_rows": len(validation),
            "test_rows": len(test),
            "split": "first 60% / next 20% / final 20% of source order",
        },
        "model_selection": {
            "selected": selected_name,
            "candidate_validation_results": candidate_results,
            "selection_rule": "highest validation AUC, then lowest validation Brier",
            "probability_calibration": calibrator,
            "selected_validation_brier_after_calibration": mean(
                (
                    _apply_platt(calibrator, score) - label
                )
                ** 2
                for score, label in zip(
                    selected_validation_scores,
                    validation_labels,
                )
            ),
        },
        "business_kpis": {
            "primary": {
                "name": "term-deposit response rate",
                "numerator": "contacts with y=yes",
                "denominator": "all observed campaign contacts",
            },
            "capacity_kpi": {
                "name": "positive response capture",
                "numerator": "observed responders inside the selected review tier",
                "denominator": "all observed responders in the evaluation split",
            },
            "unobserved": [
                "revenue",
                "margin",
                "contact cost",
                "customer lifetime value",
                "brand impact",
                "incremental treatment effect",
            ],
        },
        "simple_business_rule": business_rule,
        "test": test_overall,
        "test_calibration": calibration,
        "capacity_decision": decision,
        "block_length_sensitivity": block_sensitivity,
        "subgroup_metrics": subgroup,
        "monthly_response": monthly,
        "leakage_control": (
            "Call duration is excluded because it is only known after contact."
        ),
        "claim_boundary": (
            "Response prediction on observational campaign records is not an "
            "estimate of causal lift, profit, or customer lifetime value."
        ),
        "segment_and_horizon_boundary": (
            "Contact-channel diagnostics are reported, but the source has no "
            "long-term value, retention, cannibalization, or brand outcome. "
            "Short-term response concentration cannot substitute for them."
        ),
    }
    source = "UCI Bank Marketing, DOI 10.24432/C5K306"
    figures = project_root / "outputs/figures"
    svg_bar(
        figures / "monthly-response.svg",
        "Observed term-deposit response rate by campaign month",
        "All 41,188 contacts; descriptive and not seasonally causal",
        [
            (month.title(), metrics["response_rate"])
            for month, metrics in monthly.items()
        ],
        source,
        percent=True,
    )
    svg_bar(
        figures / "capacity-capture.svg",
        "Held-out response capture by review capacity",
        "Final source-order 20%; all options share each block-bootstrap shock",
        [
            (f"Top {label}", metrics["positive_capture"])
            for label, metrics in decision["options"].items()
        ],
        source,
        percent=True,
    )
    svg_line(
        figures / "calibration.svg",
        "Held-out response calibration",
        "Equal-count score bins on the untouched final source-order split",
        [
            (
                "Observed",
                [
                    (item["mean_score"], item["observed_rate"])
                    for item in calibration
                ],
            ),
            ("Ideal", [(0, 0), (1, 1)]),
        ],
        source,
        y_percent=True,
    )
    return result

def analyze_cfpb(project_root: Path) -> dict[str, Any]:
    source_rows = read_csv(project_root / "data/processed/analysis.csv")
    rows = []
    for source_row in source_rows:
        row = dict(source_row)
        received = datetime.fromisoformat(
            row["date_received"].replace("Z", "+00:00")
        )
        sent = datetime.fromisoformat(
            row["date_sent_to_company"].replace("Z", "+00:00")
        )
        row["received_month"] = received.strftime("%m")
        row["received_weekday"] = received.strftime("%a")
        row["transmission_hours"] = str(
            max(0.0, (sent - received).total_seconds() / 3600)
        )
        rows.append(row)
    train = [
        row for row in rows if row["date_received"][:10] <= "2022-08-31"
    ]
    validation = [
        row
        for row in rows
        if "2022-09-01" <= row["date_received"][:10] <= "2022-10-31"
    ]
    test = [
        row
        for row in rows
        if "2022-11-01" <= row["date_received"][:10] <= "2022-12-31"
    ]

    def late_labels(materialized: list[dict[str, str]]) -> list[int]:
        return [0 if row["timely"].strip().casefold() == "yes" else 1 for row in materialized]

    train_labels = late_labels(train)
    validation_labels = late_labels(validation)
    test_labels = late_labels(test)
    model_specs = {
        "issue-and-product": {
            "numeric": [],
            "categorical": ["sub_product", "issue", "sub_issue"],
        },
        "intake-context": {
            "numeric": [],
            "categorical": [
                "sub_product",
                "issue",
                "sub_issue",
                "state",
                "submitted_via",
                "received_month",
                "received_weekday",
            ],
        },
    }
    candidates = {}
    fitted = {}
    for name, spec in model_specs.items():
        model = _fit_mixed_nb(
            train,
            train_labels,
            numeric_fields=spec["numeric"],
            categorical_fields=spec["categorical"],
        )
        fitted[name] = model
        scores = [_predict_mixed_nb(model, row) for row in validation]
        candidates[name] = {
            "validation_auc": _auc(validation_labels, scores),
            "validation_brier": mean(
                (score - label) ** 2
                for score, label in zip(scores, validation_labels)
            ),
            "features": spec,
        }
    selected_name = max(
        candidates,
        key=lambda name: (
            candidates[name]["validation_auc"],
            -candidates[name]["validation_brier"],
        ),
    )
    selected_model = fitted[selected_name]
    selected_validation_scores = [
        _predict_mixed_nb(selected_model, row) for row in validation
    ]
    calibrator = _fit_platt_calibrator(
        selected_validation_scores,
        validation_labels,
    )
    raw_test_scores = [
        _predict_mixed_nb(selected_model, row) for row in test
    ]
    test_scores = [
        _apply_platt(calibrator, score) for score in raw_test_scores
    ]
    test_overall = _classification_metrics(test_labels, test_scores, 0.5)
    calibration = _calibration_bins(test_labels, test_scores, bins=8)
    config = load_json(project_root / "config.json")
    capacities = config["parameters"]["triage_capacity_shares"]
    rng = random.Random(config["analysis_seed"])
    bootstrap_indices = [
        _day_block_indices(
            test,
            date_field="date_received",
            block_days=config["parameters"]["bootstrap_block_days"],
            rng=rng,
        )
        for _ in range(config["parameters"]["bootstrap_samples"])
    ]
    observed_auc = test_overall["auc"]
    auc_bootstrap = []
    capacity_bootstrap: dict[str, list[float]] = {
        f"{capacity:.0%}": [] for capacity in capacities
    }
    for indices in bootstrap_indices:
        sampled_labels = [test_labels[index] for index in indices]
        sampled_scores = [test_scores[index] for index in indices]
        sampled_auc = _auc(sampled_labels, sampled_scores)
        if math.isfinite(sampled_auc):
            auc_bootstrap.append(sampled_auc)
        for capacity in capacities:
            metrics = _capacity_metrics(
                sampled_labels,
                sampled_scores,
                capacity,
            )
            capacity_bootstrap[f"{capacity:.0%}"].append(
                float(metrics["lift_vs_random"])
            )
    permutation_rng = random.Random(config["analysis_seed"] + 991)
    null_auc = []
    for _ in range(config["parameters"]["permutation_samples"]):
        permuted = list(test_labels)
        permutation_rng.shuffle(permuted)
        null_auc.append(_auc(permuted, test_scores))
    auc_validation = {
        "observed_auc": observed_auc,
        "block_bootstrap_95_interval": [
            quantile(auc_bootstrap, 0.025),
            quantile(auc_bootstrap, 0.975),
        ],
        "permutation_null": {
            "samples": len(null_auc),
            "mean_auc": mean(null_auc),
            "95_interval": [
                quantile(null_auc, 0.025),
                quantile(null_auc, 0.975),
            ],
            "one_sided_p_value": (
                1 + sum(value >= observed_auc for value in null_auc)
            )
            / (len(null_auc) + 1),
        },
    }
    capacity_validation: dict[str, dict[str, Any]] = {}
    for capacity in capacities:
        label = f"{capacity:.0%}"
        point = _capacity_metrics(test_labels, test_scores, capacity)
        lift_samples = capacity_bootstrap[label]
        capacity_validation[label] = {
            **point,
            "random_capture_benchmark": point["capacity_share"],
            "excess_capture_over_random": (
                point["positive_capture"] - point["capacity_share"]
            ),
            "lift_block_bootstrap_95_interval": [
                quantile(lift_samples, 0.025),
                quantile(lift_samples, 0.975),
            ],
        }
    minimum_auc = config["parameters"]["minimum_deployment_auc"]
    minimum_lift = config["parameters"]["minimum_deployment_lift"]
    capacity_gate_passes = [
        metrics["lift_vs_random"] >= minimum_lift
        and metrics["lift_block_bootstrap_95_interval"][0] > 1.0
        for metrics in capacity_validation.values()
    ]
    gate_passes = observed_auc >= minimum_auc and any(capacity_gate_passes)
    deployment_gate = {
        "status": (
            "eligible_for_prospective_workflow_test"
            if gate_passes
            else "do_not_deploy_ranking_model"
        ),
        "passes": gate_passes,
        "auc_gate": {
            "threshold": minimum_auc,
            "observed": observed_auc,
            "passes": observed_auc >= minimum_auc,
        },
        "capacity_lift_gate": {
            "threshold": minimum_lift,
            "passes_any_review_capacity": any(capacity_gate_passes),
        },
        "reason": (
            "Later-period discrimination is weak and no tested capacity has both "
            "the required point lift and a block-bootstrap lower bound above "
            "random review."
        ),
        "permitted_use": (
            "Retain the privacy-minimized data contract, calendar split, aggregate "
            "monitoring, and negative-validation evidence; do not operationalize "
            "individual complaint ranking."
        ),
        "reversal_conditions": [
            (
                "A pre-registered future-period evaluation exceeds the AUC gate "
                "and reproduces material lift above random review."
            ),
            (
                "Operationally available features add stable signal without "
                "violating the privacy and use boundary."
            ),
            (
                "A prospective workflow study demonstrates benefit and checks "
                "distributional burden before any ranking use."
            ),
        ],
    }
    validation_decision = {
        "question": (
            "Does the later-period evidence justify deploying an individual "
            "complaint ranking model?"
        ),
        "decision": deployment_gate["status"],
        "auc_validation": auc_validation,
        "capacity_validation": capacity_validation,
        "deployment_gate": deployment_gate,
        "source_of_metrics": "untouched November-December 2022 evaluation",
        "approval_chain": [
            {
                "role": "repository author",
                "status": "self-reviewed negative validation",
                "scope": "public-data research demonstration only",
            }
        ],
    }
    write_json(
        project_root / "outputs/decision-analysis.json",
        validation_decision,
    )

    block_sensitivity: dict[str, Any] = {}
    for block_days in (3, 7, 14):
        sensitivity_rng = random.Random(config["analysis_seed"] + block_days)
        sensitivity_indices = [
            _day_block_indices(
                test,
                date_field="date_received",
                block_days=block_days,
                rng=sensitivity_rng,
            )
            for _ in range(200)
        ]
        block_sensitivity[str(block_days)] = {
            f"{capacity:.0%}": {
                "lift_95_interval": [
                    quantile(lifts, 0.025),
                    quantile(lifts, 0.975),
                ]
            }
            for capacity in capacities
            for lifts in [
                [
                    float(
                        _capacity_metrics(
                            [test_labels[index] for index in indices],
                            [test_scores[index] for index in indices],
                            capacity,
                        )["lift_vs_random"]
                    )
                    for indices in sensitivity_indices
                ]
            ]
        }

    monthly = {}
    for month in range(1, 13):
        month_rows = [
            row for row in rows if int(row["received_month"]) == month
        ]
        labels = late_labels(month_rows)
        monthly[f"2022-{month:02d}"] = {
            "complaints": len(month_rows),
            "late_response_rate": mean(labels),
        }
    by_product = {}
    for product in sorted({row["sub_product"] for row in rows}):
        product_rows = [row for row in rows if row["sub_product"] == product]
        labels = late_labels(product_rows)
        by_product[product] = {
            "complaints": len(product_rows),
            "late_response_rate": mean(labels),
        }
    subgroup = {}
    for product in sorted({row["sub_product"] for row in test}):
        indices = [
            index for index, row in enumerate(test) if row["sub_product"] == product
        ]
        if len(indices) < 50:
            continue
        labels = [test_labels[index] for index in indices]
        scores = [test_scores[index] for index in indices]
        auc = _auc(labels, scores)
        subgroup[product] = {
            "n": len(indices),
            "late_response_rate": mean(labels),
            "auc": None if not math.isfinite(auc) else auc,
            "top_10_percent": _capacity_metrics(labels, scores, 0.10),
        }
    prediction_rows = [
        {
            "evaluation_row": index + 1,
            "date_received": row["date_received"][:10],
            "sub_product": row["sub_product"],
            "late_label": test_labels[index],
            "late_score": round(test_scores[index], 8),
        }
        for index, row in enumerate(test)
    ]
    write_csv(
        project_root / "outputs/predictions.csv",
        prediction_rows,
        [
            "evaluation_row",
            "date_received",
            "sub_product",
            "late_label",
            "late_score",
        ],
    )
    write_json(
        project_root / "outputs/model.json",
        {
            "selected_candidate": selected_name,
            "classifier": selected_model,
            "calibration": calibrator,
        },
    )
    result = {
        "project_id": "cfpb-fintech-complaint-operations",
        "data": {
            "rows": len(rows),
            "train_rows": len(train),
            "validation_rows": len(validation),
            "test_rows": len(test),
            "period": ["2022-01-01", "2022-12-31"],
        },
        "model_selection": {
            "selected": selected_name,
            "candidate_validation_results": candidates,
            "selection_rule": "highest validation AUC, then lowest validation Brier",
            "probability_calibration": calibrator,
            "selected_validation_brier_after_calibration": mean(
                (
                    _apply_platt(calibrator, score) - label
                )
                ** 2
                for score, label in zip(
                    selected_validation_scores,
                    validation_labels,
                )
            ),
        },
        "test": test_overall,
        "test_calibration": calibration,
        "auc_validation": auc_validation,
        "capacity_validation": capacity_validation,
        "deployment_gate": deployment_gate,
        "block_length_sensitivity": block_sensitivity,
        "monthly_operations": monthly,
        "sub_product_operations": by_product,
        "subgroup_metrics": subgroup,
        "privacy_design": (
            "Narratives, company names, ZIP codes, tags, and public-response text "
            "were excluded before repository storage."
        ),
        "claim_boundary": (
            "The timely indicator is not complaint merit, consumer harm, "
            "resolution quality, company quality, or regulatory compliance. "
            "Weak ranking performance cannot be rescued by privacy or validation "
            "discipline; those are separate contributions."
        ),
    }
    source = (
        "CFPB Consumer Complaint Database, 2022 money-transfer, "
        "virtual-currency, and money-service complaints"
    )
    figures = project_root / "outputs/figures"
    svg_line(
        figures / "monthly-volume.svg",
        "Published digital-payment complaints received by month",
        "Closed 2022 UTC date window; publication is selective",
        [
            (
                "Complaints",
                [
                    (month, monthly[f"2022-{month:02d}"]["complaints"])
                    for month in range(1, 13)
                ],
            )
        ],
        source,
    )
    top_products = sorted(
        by_product.items(),
        key=lambda item: item[1]["complaints"],
        reverse=True,
    )[:6]
    svg_bar(
        figures / "subproduct-late-rate.svg",
        "Observed untimely-response rate by digital-payment sub-product",
        "Six largest sub-products in the 2022 public extract",
        [
            (name, value["late_response_rate"])
            for name, value in top_products
        ],
        source,
        percent=True,
    )
    svg_bar(
        figures / "capacity-capture.svg",
        "Held-out ranking lift by review capacity",
        "November-December 2022; 1.0 is random review",
        [
            (f"Top {label}", metrics["lift_vs_random"])
            for label, metrics in capacity_validation.items()
        ],
        source,
        benchmark=1.0,
    )
    svg_line(
        figures / "calibration.svg",
        "Held-out late-response calibration",
        "Equal-count score bins on November-December 2022",
        [
            (
                "Observed",
                [
                    (item["mean_score"], item["observed_rate"])
                    for item in calibration
                ],
            ),
            ("Ideal", [(0, 0), (1, 1)]),
        ],
        source,
        y_percent=True,
    )
    gain_shares = [0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 0.75, 1.0]
    observed_gain = []
    for share in gain_shares:
        if share == 0:
            observed_gain.append((0.0, 0.0))
            continue
        metrics = _capacity_metrics(test_labels, test_scores, share)
        observed_gain.append(
            (
                float(metrics["capacity_share"]),
                float(metrics["positive_capture"]),
            )
        )
    svg_line(
        figures / "cumulative-gain.svg",
        "Held-out cumulative gain versus random review",
        "November-December 2022; useful ranking should rise above the diagonal",
        [
            ("Observed ranking", observed_gain),
            ("Random review", [(0.0, 0.0), (1.0, 1.0)]),
        ],
        source,
        y_percent=True,
    )
    svg_bar(
        figures / "auc-null-benchmark.svg",
        "Held-out AUC against the permutation null",
        "Observed AUC compared with the 95th percentile of 500 label permutations",
        [
            ("Observed AUC", observed_auc),
            ("Permutation 95th percentile", quantile(null_auc, 0.95)),
        ],
        source,
        benchmark=0.5,
    )
    return result

__all__ = [name for name in globals() if not name.startswith("__")]
