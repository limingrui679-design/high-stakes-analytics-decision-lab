# Cross-City 311 Distribution Shift and Transfer Gate

**Analytical question:** Are city service-request distributions sufficiently comparable to transfer an analytical rule between Chicago and New York?

**Decision boundary:** Administrative shift audit only; requests are not latent need or service quality.

## Evidence and methods

- Source: City of Chicago and City of New York — Daily source-category aggregates, 2022-2023.
- Analytical grain: one city-day-audited service-family aggregate.
- Methods: Audited ontology, unmatched-category retention, total variation, Jensen-Shannon divergence, and transfer gating.
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

Administrative shift audit only; requests are not latent need or service quality.
