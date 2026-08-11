# 12 · Opportunity Zone One-Year Policy Evidence Screen

**Technical summary.** The matched one-year screen contains 1,460 complete tract panels, including 138 designated QOZ tracts and 121 unique matched controls.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/opportunity-zone-policy-evaluation/outputs/report.md)
- [Review the project design](../projects/opportunity-zone-policy-evaluation/PROJECT.md)
- [Inspect the source manifest](../projects/opportunity-zone-policy-evaluation/source-manifest.json)
- [Inspect the machine-readable results](../projects/opportunity-zone-policy-evaluation/outputs/results.json)

![Representative evidence figure for Opportunity Zone One-Year Policy Evidence Screen](../figures/12-opportunity-zone-policy-evaluation.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Public Policy |
| Adaptive route | descriptive → diagnostic → decision |
| Analytical question | How did selected tract outcomes change immediately after QOZ designation relative to observed-covariate matches? |
| Prepared rows | 2,956 |
| Valid terminal output | associational policy screen only |

## Evidence-backed findings

- **Complete tract panels:** 1,460
- **Designated QOZ tracts analyzed:** 138
- **Unique matched controls:** 121
- **Causal status:** not identified

## Methods selected for this case

- Panel linkage
- nearest-neighbor matching
- change contrasts
- bootstrap intervals
- and support diagnostics.

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Associational one-year screen; no causal effect because parallel trends are unavailable.

## Source identity

- **Dataset:** [Opportunity Zone One-Year Policy Evidence Screen](https://www.cdfifund.gov/opportunity-zones)
- **Publisher:** CDFI Fund and U.S. Census Bureau
- **Version:** 2018 designated QOZ list with 2018-2019 ACS and LODES Massachusetts tract panel
- **Accessed:** 2026-08-10
- **License:** U.S. Government public data
- **Analytical grain:** one Massachusetts tract-year row

### Reviewed source-snapshot hashes

- `massachusetts-qoz-tract-panel.csv` — `372b2a44ef2d38cd7d402cf3c58d1a9788f09baec3399065db4f8e93cde707ae`
- `massachusetts-qoz-tract-panel.source-lock.json` — `5602509c4659062bed956f315feaed2aff429fdc384627b6fab68ebe85918790`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
