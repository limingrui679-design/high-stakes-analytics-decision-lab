# 09 · SEC N-PORT Liquidity and Crowding Filing Review

**Technical summary.** Across 11,747 reviewed filings, median top-10 holding concentration is 34.5% and the 90th-percentile Level-3 share is 0.2%.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/sec-nport-filing-review/outputs/report.md)
- [Review the project design](../projects/sec-nport-filing-review/PROJECT.md)
- [Inspect the source manifest](../projects/sec-nport-filing-review/source-manifest.json)
- [Inspect the machine-readable results](../projects/sec-nport-filing-review/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/sec-nport-filing-review/outputs/decision/report/decision-report.md)

![Representative evidence figure for SEC N-PORT Liquidity and Crowding Filing Review](../figures/09-sec-nport-filing-review.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Regulatory Filings |
| Adaptive route | descriptive → diagnostic → predictive → prescriptive |
| Analytical question | Which transparent concentration, liquidity, and redemption indicators should trigger targeted filing review? |
| Prepared rows | 11,747 |
| Valid terminal output | claim-bounded decision review |

## Evidence-backed findings

- **Reviewed fund filings:** 11,747
- **Median top-10 holding concentration:** 34.5%
- **90th-percentile Level-3 share:** 0.2%
- **Terminal use:** targeted filing review only

## Methods selected for this case

- Filing extraction
- percentile indicators
- transparent composite score
- and review-capacity trade-offs.

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Filing review only; no expected-return, suitability, fund-quality, or investment recommendation.

## Source identity

- **Dataset:** [SEC N-PORT Liquidity and Crowding Filing Review](https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets)
- **Publisher:** U.S. Securities and Exchange Commission
- **Version:** Form N-PORT Data Set 2025 Q4, minimized to fund-level review indicators
- **Accessed:** 2026-08-10
- **License:** U.S. Government public data
- **Analytical grain:** one fund filing snapshot

### Reviewed source-snapshot hashes

- `sec-nport-2025q4-fund-risk.csv` — `3c45ae1e8815a5bffd9fa0f0d2e100eae37113d3074324713670b4f975144d73`
- `sec-nport-2025q4-fund-risk.source-lock.json` — `c000a6bf8325b96f8b592cf09be99f634dc47fa095ac7b202c1cf86181c29c8a`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
