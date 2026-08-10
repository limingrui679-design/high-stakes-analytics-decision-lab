# 07 · Commercial Real Estate Diligence Decision Product

**Technical summary.** Across 12,399 filtered commercial transactions, Manhattan has the highest borough median price per square foot at $743; the break-even cap rate at 8.5% debt is 7.5%.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/commercial-real-estate-risk/outputs/report.md)
- [Review the project design](../projects/commercial-real-estate-risk/PROJECT.md)
- [Inspect the source manifest](../projects/commercial-real-estate-risk/source-manifest.json)
- [Inspect the machine-readable results](../projects/commercial-real-estate-risk/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/commercial-real-estate-risk/outputs/decision/report/decision-report.md)

![Representative evidence figure for Commercial Real Estate Diligence Decision Product](../figures/07-commercial-real-estate-risk.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Real-Estate Finance |
| Adaptive route | descriptive → diagnostic → prescriptive |
| Analytical question | Which borough/property-type segments have enough public transaction evidence for property-level diligence, and how do financing-rate assumptions change the income hurdle? |
| Prepared rows | 12,399 |
| Valid terminal output | claim-bounded decision review |

## Evidence-backed findings

- **Filtered transactions:** 12,399
- **Observed segments:** 25
- **Segments passing the public-data gate:** 20
- **Break-even cap rate at 8.5% debt:** 7.5%

## Methods selected for this case

- privacy-minimized administrative data
- robust price-per-square-foot summaries
- median bootstrap intervals
- borough/property-type segment depth
- annual transaction-liquidity trend
- amortizing-debt break-even cap-rate scenarios

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

The source does not establish arm's-length status, NOI, expenses, occupancy, condition, appraisal value, debt terms, or causal regeneration effects.

## Source identity

- **Dataset:** [Commercial Real Estate Transactions and Regeneration Risk](https://data.cityofnewyork.us/City-Government/NYC-Citywide-Annualized-Calendar-Sales-Update/w2pb-icbu/about_data)
- **Publisher:** New York City Department of Finance via NYC Open Data
- **Version:** filtered 2021-2025 commercial-unit snapshot from dataset w2pb-icbu
- **Accessed:** 2026-07-30
- **License:** NYC Open Data Terms of Use
- **Analytical grain:** one public NYC property-sale record before robust analytical filtering

### Reviewed source-snapshot hashes

- `nyc-commercial-sales-2021-2025.csv` — `daa08cd7e6d95c2060cdc2eb1b8b6308932c334179dc57af46c203374935389a`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
