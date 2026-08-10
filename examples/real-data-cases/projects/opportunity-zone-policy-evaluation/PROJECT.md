# Opportunity Zone One-Year Policy Evidence Screen

**Analytical question:** How did selected tract outcomes change immediately after QOZ designation relative to observed-covariate matches?

**Decision boundary:** Associational one-year screen; no causal effect because parallel trends are unavailable.

## Evidence and methods

- Source: CDFI Fund and U.S. Census Bureau — 2018 designated QOZ list with 2018-2019 ACS and LODES Massachusetts tract panel.
- Analytical grain: one Massachusetts tract-year row.
- Methods: Panel linkage, nearest-neighbor matching, change contrasts, bootstrap intervals, and support diagnostics.
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

Associational one-year screen; no causal effect because parallel trends are unavailable.
