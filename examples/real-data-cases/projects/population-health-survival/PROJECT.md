# Population Health Risk Transport Across NHIS Cohorts

**Analytical question:** Do simple population-risk cells developed in NHIS 2016 retain discrimination and calibration in the 2017 linked-mortality cohort?

**Decision boundary:** Population-risk validation only; no individual diagnosis, treatment, or clinical deployment.

## Evidence and methods

- Source: U.S. Centers for Disease Control and Prevention, National Center for Health Statistics — NHIS 2016 and 2017 Sample Adult files linked to 2019 public-use mortality.
- Analytical grain: one NHIS sampled adult linked to mortality status.
- Methods: Survey weighting, temporal validation, AUC, Brier score, calibration, and bounded review protocols.
- Every bundled raw or minimized source file is hash-locked in `source-manifest.json`.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

Read the [technical report](outputs/report.md), [machine-readable results](outputs/results.json), [source manifest](source-manifest.json), and [data-quality report](data/quality-report.json).

## Non-negotiable limitation

Population-risk validation only; no individual diagnosis, treatment, or clinical deployment.
