# ACS Employment AI Temporal Transport and Audit

**Analytical question:** How well does a protected-attribute-excluded employment model developed on 2019 PUMS transport to 2023?

**Decision boundary:** No eligibility, hiring, credit, benefits, or other consequential action.

## Evidence and methods

- Source: U.S. Census Bureau — Rhode Island ACS 1-year PUMS person files, 2019 and 2023.
- Analytical grain: one working-age ACS PUMS person record.
- Methods: Survey-weighted grouped-rate model, temporal AUC/Brier/calibration, and protected-attribute audit slices.
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

No eligibility, hiring, credit, benefits, or other consequential action.
