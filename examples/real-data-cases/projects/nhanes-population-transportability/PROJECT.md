# NHANES Mortality Transportability and Population Inequality

**Analytical question:** Do population mortality risk patterns transport between NHANES cohorts, and what inequality gradient remains visible?

**Decision boundary:** Population research only; no individual diagnosis or treatment.

## Evidence and methods

- Source: U.S. Centers for Disease Control and Prevention, National Center for Health Statistics — NHANES 2011-2012 and 2015-2016 demographics linked to 2019 mortality.
- Analytical grain: one NHANES adult linked to 36-month mortality.
- Methods: Survey-weighted rates, cross-cohort AUC/Brier/calibration, and poverty-income-ratio gradients.
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

Population research only; no individual diagnosis or treatment.
