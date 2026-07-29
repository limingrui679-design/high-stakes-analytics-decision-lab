# R3 · Census-Income Classification and Subgroup Validation

**Portfolio role:** end-to-end AI, statistical prediction, and responsible model validation  
**Decision boundary:** benchmark model development only—never eligibility, hiring, credit, or other consequential classification.

## Analytical question

Can a transparent mixed-feature classifier improve on a majority benchmark out of sample, and what do calibration and subgroup error diagnostics reveal that aggregate accuracy hides?

## Evidence and methods

- UCI Adult dataset, 48,842 Census-derived records, CC BY 4.0.
- Source-provided train/test split; the final test set is never used for fitting.
- Majority and mixed Gaussian/categorical naïve-Bayes baselines.
- Sparse one-hot logistic regression selected on an internal validation split,
  with the source Adult test file untouched until final evaluation.
- AUC, Brier score, calibration, sex/race subgroup confusion metrics, drift,
  and abnormal/unseen/extreme-input challenges.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

`build_decision_case.py` intentionally creates only a boundary note: predictive performance alone does not justify an action comparison. Review the [report](outputs/report.md), [model](outputs/model.json), [predictions](outputs/predictions.csv), and [results](outputs/results.json).

## Transferable methods

The case demonstrates baseline comparison, internal model selection, an
independent test set, calibration, subgroup error analysis, drift checks, and
an explicit boundary against consequential deployment.

## Non-negotiable limitation

The benchmark reflects 1994 social and labor structures and includes sensitive attributes. It is unsuitable for real high-stakes use and is retained to demonstrate validation discipline.
