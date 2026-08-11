# 02 · Cross-City 311 Distribution Shift and Transfer Gate

**Technical summary.** The 2023 cross-city total-variation distance is 58.1%, and the transfer gate is refused.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/cross-city-311-shift/outputs/report.md)
- [Review the project design](../projects/cross-city-311-shift/PROJECT.md)
- [Inspect the source manifest](../projects/cross-city-311-shift/source-manifest.json)
- [Inspect the machine-readable results](../projects/cross-city-311-shift/outputs/results.json)

![Representative evidence figure for Cross-City 311 Distribution Shift and Transfer Gate](../figures/02-cross-city-311-shift.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Urban Analytics |
| Adaptive route | descriptive → diagnostic → decision |
| Analytical question | Are city service-request distributions sufficiently comparable to transfer an analytical rule between Chicago and New York? |
| Prepared rows | 8,760 |
| Valid terminal output | transfer refused |

## Evidence-backed findings

- **Cross-city 2023 total-variation distance:** 58.1%
- **Chicago mapped share:** 96.9%
- **New York mapped share:** 52.6%
- **Transfer gate:** refused

## Methods selected for this case

- Audited ontology
- unmatched-category retention
- total variation
- Jensen-Shannon divergence
- and transfer gating.

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Administrative shift audit only; requests are not latent need or service quality.

## Source identity

- **Dataset:** [Cross-City 311 Distribution Shift and Transfer Gate](https://data.cityofchicago.org/Service-Requests/311-Service-Requests-Request-and-Response-Times/v6vf-nfxy)
- **Publisher:** City of Chicago and City of New York
- **Version:** Daily source-category aggregates, 2022-2023
- **Accessed:** 2026-08-10
- **License:** Municipal open-data terms
- **Analytical grain:** one city-day-audited service-family aggregate

### Reviewed source-snapshot hashes

- `cross-city-311-daily.csv` — `46a932811648b1e0282a74456624a3928cad5f3b24860ffad5c6d4c66402006f`
- `cross-city-311-daily.source-lock.json` — `d0f1740a18bc759ee4d8fab6c8ab7f0efd225df02918cf3a9bb0a7f5eee36424`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
