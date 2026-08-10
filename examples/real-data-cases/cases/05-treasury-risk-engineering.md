# 05 · Treasury Curve and Tail-Risk Decision Engine

**Technical summary.** Historical ES95 loss rises from 0.4% for the short baseline to 0.9% for the long-duration portfolio; the short-baseline rolling VaR exceedance rate is 6.0%.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/treasury-risk-engineering/outputs/report.md)
- [Review the project design](../projects/treasury-risk-engineering/PROJECT.md)
- [Inspect the source manifest](../projects/treasury-risk-engineering/source-manifest.json)
- [Inspect the machine-readable results](../projects/treasury-risk-engineering/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/treasury-risk-engineering/outputs/decision/report/decision-report.md)

![Representative evidence figure for Treasury Curve and Tail-Risk Decision Engine](../figures/05-treasury-risk-engineering.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Financial Risk Engineering |
| Adaptive route | descriptive → predictive → prescriptive |
| Analytical question | How do duration choices change historical tail loss, backtest behavior, and sensitivity to dependent market shocks? |
| Prepared rows | 1,500 |
| Valid terminal output | claim-bounded decision review |

## Evidence-backed findings

- **Short-baseline historical ES95 loss:** 0.4%
- **Short-baseline rolling VaR exceedance rate:** 6.0%
- **Kupiec coverage p approximation:** 0.114
- **Daily yield curves:** 1,500

## Methods selected for this case

- daily carry plus first-order duration response
- historical VaR and expected shortfall
- rolling coverage backtest
- breach-independence diagnostic
- regime comparison
- block bootstrap

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

First-order duration omits convexity, security selection, costs, financing, taxes, liquidity, and future-regime uncertainty.

## Source identity

- **Dataset:** [Daily Treasury Par Yield Curve Rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve)
- **Publisher:** U.S. Department of the Treasury
- **Version:** Official daily par yields, 2020-01-02 through 2025-12-31
- **Accessed:** 2026-07-27
- **License:** U.S. Government work
- **Analytical grain:** one U.S. Treasury business-day yield curve

### Reviewed source-snapshot hashes

- `treasury-2020.csv` — `edcf1c8be9622f3cd92eb7de1847aefc3977e2118e2ff9af67f46614a5c306a7`
- `treasury-2021.csv` — `1be57e49c63a99f6002431a1030c8fbe539b71066c3eaf14f9f58ddc34492cea`
- `treasury-2022.csv` — `c33cb2758e5e34c2c23b7ab759d18681091860f3f9e5960112859f64f31cd814`
- `treasury-2023.csv` — `edb7f3904e11dcaa502cdcc03ad9b1b16c893802d166ce9bc5fa1118251249d4`
- `treasury-2024.csv` — `6775840b76cd7fd41121f61d6f6c60184eca6b2ba49954ec7372c463cbeef34d`
- `treasury-2025.csv` — `cf2fa3da7f160384b63d2ead698532b1d76cd9f789ce4911e2304db85b14e6d5`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
