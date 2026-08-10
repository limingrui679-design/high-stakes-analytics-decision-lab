# Jersey City Bike Demand and Rebalancing Evidence

**Analytical question:** Can station-hour history improve held-out pickup forecasts, and which fixed-budget rebalancing scenario deserves a bounded operations pilot?

**Decision boundary:** Rebalancing outcomes are modeled; no stockout, routing, labor, or achieved-service claim.

## Evidence and methods

- Source: Citi Bike — Jersey City trip history, January-December 2021; derived station-hour aggregate.
- Analytical grain: one station-hour-month aggregate.
- Methods: Temporal holdout, weighted MAE, observed pickup-return imbalance, and fixed-budget scenario comparison.
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

Rebalancing outcomes are modeled; no stockout, routing, labor, or achieved-service claim.
