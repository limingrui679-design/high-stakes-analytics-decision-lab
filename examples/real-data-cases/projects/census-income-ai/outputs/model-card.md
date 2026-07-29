# Model card · Census-income benchmark

## Intended use

Reproducible classification and validation benchmark only. It is not authorized for employment, credit, benefits, immigration, eligibility, or any consequential decision.

## Data and split

- Development source: 32,561 Adult training records.
- Independent source test: 16,281 Adult test records.
- Hyperparameters use a stratified 80/20 split inside the training file.
- The source test file is untouched until final evaluation.

## Model and metrics

- Majority baseline, mixed naive Bayes baseline, and sparse one-hot logistic regression.
- Selected L2: 0.0; final AUC: 0.905; Brier: 0.102.
- Decision threshold 0.2124 comes from an illustrative 3:1 false-negative/false-positive validation cost.

## Failure modes and governance

- Historical 1994 Census-derived patterns are not current causal relationships.
- Recorded sex and race diagnostics expose error variation; they do not legitimate use of those attributes.
- Unknown categories require review; impossible numeric inputs should be rejected.
- Human review, notice, appeal, rollback, and drift monitoring would be mandatory before any new use.

## Explainability boundary

Coefficients describe model associations after encoding. They are not causal effects or policy levers.
