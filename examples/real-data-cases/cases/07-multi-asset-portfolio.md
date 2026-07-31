# 07 · Regime-Aware Multi-Asset Portfolio Construction

**Technical summary.** The bounded adaptive rule reduced historical drawdown and tail loss relative to both benchmarks and had the highest return-to-volatility ratio, but it did not maximize sampled mean return.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/regime-aware-multi-asset-portfolio/outputs/report.md)
- [Review the project design](../projects/regime-aware-multi-asset-portfolio/PROJECT.md)
- [Inspect the source manifest](../projects/regime-aware-multi-asset-portfolio/source-manifest.json)
- [Inspect the machine-readable results](../projects/regime-aware-multi-asset-portfolio/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/regime-aware-multi-asset-portfolio/outputs/decision/report/decision-report.md)

![Walk-forward multi-asset portfolio growth beside equal-weight and 60/40 benchmarks](../figures/07-multi-asset.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Asset allocation and financial risk |
| Adaptive route | descriptive → diagnostic → predictive → prescriptive |
| Analytical question | Can a transparent walk-forward allocation improve the historical risk-return trade-off without breaking turnover, tail-risk, or evidence constraints? |
| Prepared rows | 2,766 |
| Valid terminal output | Prospective paper-portfolio validation; no investment instruction |

## Evidence-backed findings

- **Walk-forward evaluation:** 2,513 trading days
- **Adaptive annual return / volatility:** 6.9% / 7.1%
- **Adaptive maximum drawdown:** -16.6%
- **Adaptive shared-block P(best):** 0.8% for mean return

## Methods selected for this case

- walk-forward inverse-volatility allocation
- bounded monthly rebalancing
- equal-weight and 60/40 benchmarks
- turnover-cost sensitivity
- historical drawdown and expected shortfall
- shared month-block probability-best

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Provider terms apply; ETF histories omit future regimes, taxes, bid-ask spreads, impact, investor liabilities, capacity, and suitability.

## Source identity

- **Dataset:** [Reviewed ETF Adjusted-Price Snapshot](https://finance.yahoo.com/)
- **Publisher:** Yahoo Finance
- **Version:** 2015-01-01 through 2025-12-31 request window
- **Accessed:** 2026-07-30
- **License:** Yahoo terms of service; upstream market-data rights remain separate
- **Analytical grain:** one common trading date across SPY, TLT, VNQ, GLD, and BIL

### Reviewed source-snapshot hashes

- `yahoo-adjusted-close-2015-2025.json` — `8a29e3094f6280384bd98723f827b94de3f72538f80bd4beb8505413afe56546`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
