# 01 · Jersey City Bike Demand and Rebalancing Evidence

**Technical summary.** Held-out station-hour MAE is 0.69 pickups/day, a 33.1% improvement over the hour-only baseline.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/bike-demand-operations/outputs/report.md)
- [Review the project design](../projects/bike-demand-operations/PROJECT.md)
- [Inspect the source manifest](../projects/bike-demand-operations/source-manifest.json)
- [Inspect the machine-readable results](../projects/bike-demand-operations/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/bike-demand-operations/outputs/decision/report/decision-report.md)

![Representative evidence figure for Jersey City Bike Demand and Rebalancing Evidence](../figures/01-bike-demand-operations.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Operations Research |
| Adaptive route | descriptive → predictive → prescriptive |
| Analytical question | Can station-hour history improve held-out pickup forecasts, and which fixed-budget rebalancing scenario deserves a bounded operations pilot? |
| Prepared rows | 17,906 |
| Valid terminal output | claim-bounded decision review |

## Capability path

| Role | Capability |
|---|---|
| Primary | **Analytics to action** — Connect prediction or diagnosis to capacity, workflow, implementation, communication, and a bounded next step. |
| Supporting | AI and model validation, Risk and decision analysis |

### Reviewer-visible signals

- temporal holdout
- simple baseline
- fixed capacity
- modeled pilot boundary

Capability labels help readers find a relevant precedent. They do not upgrade
the evidence, permitted use, or empirical result of this case.

## Evidence-backed findings

- **Held-out station-hour MAE:** 0.69 pickups/day
- **Improvement vs hour-only baseline:** 33.1%
- **Observed station-hour-month rows:** 17,906
- **Rebalancing results:** modeled scenario only

## Methods selected for this case

- Temporal holdout
- weighted MAE
- observed pickup-return imbalance
- and fixed-budget scenario comparison.

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Rebalancing outcomes are modeled; no stockout, routing, labor, or achieved-service claim.

## Source identity

- **Dataset:** [Jersey City Bike Demand and Rebalancing Evidence](https://citibikenyc.com/system-data)
- **Publisher:** Citi Bike
- **Version:** Jersey City trip history, January-December 2021; derived station-hour aggregate
- **Accessed:** 2026-08-10
- **License:** Citi Bike Data Sharing Policy
- **Analytical grain:** one station-hour-month aggregate

### Reviewed source-snapshot hashes

- `citibike-jc-2021-station-hour.csv` — `e34022dc61250b3a5e499fa429570a87104cec0985caeaa5980a5b2206e45524`
- `citibike-jc-2021-station-hour.source-lock.json` — `85d43b52e3f44a308aa72280726e4a0a28cb77197f634f2548b7c88168035eeb`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
