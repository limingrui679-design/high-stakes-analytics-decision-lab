# Social-Norm Field Experiment with Household-Clustered Inference

**Analytical question:** What were the intent-to-treat turnout effects of randomized social-pressure mailings after household clustering?

**Decision boundary:** Causal scope is the historical randomized experiment; no new campaign authorization.

## Evidence and methods

- Source: Yale Institution for Social and Policy Studies — Gerber-Green-Larimer 2008 replication file; non-identifying aggregate and locally computed clustered inference.
- Analytical grain: one treatment by prior-turnout aggregate.
- Methods: Randomized-arm rates, household-clustered sandwich variance, 95% intervals, and descriptive strata contrasts.
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

Causal scope is the historical randomized experiment; no new campaign authorization.
