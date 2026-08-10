# 04 · ACS Employment AI Temporal Transport and Audit

**Technical summary.** No eligibility, hiring, credit, benefits, or other consequential action.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/census-income-ai/outputs/report.md)
- [Review the project design](../projects/census-income-ai/PROJECT.md)
- [Inspect the source manifest](../projects/census-income-ai/source-manifest.json)
- [Inspect the machine-readable results](../projects/census-income-ai/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/census-income-ai/outputs/decision/report/decision-report.md)

![Representative evidence figure for ACS Employment AI Temporal Transport and Audit](../figures/04-census-income-ai.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Artificial Intelligence |
| Adaptive route | descriptive → predictive |
| Analytical question | How well does a protected-attribute-excluded employment model developed on 2019 PUMS transport to 2023? |
| Prepared rows | 12,469 |
| Valid terminal output | do not use for consequential action |

## Evidence-backed findings

- **2023 temporal-test AUC:** 0.640
- **2023 weighted Brier score:** 0.158
- **2019/2023 analyzed people:** 6,413 / 6,056
- **Decision status:** no consequential use

## Methods selected for this case

- Survey-weighted grouped-rate model
- temporal AUC/Brier/calibration
- and protected-attribute audit slices.

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

No eligibility, hiring, credit, benefits, or other consequential action.

## Source identity

- **Dataset:** [ACS Employment AI Temporal Transport and Audit](https://www.census.gov/programs-surveys/acs/microdata.html)
- **Publisher:** U.S. Census Bureau
- **Version:** Rhode Island ACS 1-year PUMS person files, 2019 and 2023
- **Accessed:** 2026-08-10
- **License:** U.S. Government open data
- **Analytical grain:** one working-age ACS PUMS person record

### Reviewed source-snapshot hashes

- `acs2019-ri-person-pums.zip` — `22eebb2e2654577708d1baaf611109dba696f334c105236d3b3708d95864d824`
- `acs2023-ri-person-pums.zip` — `588cdc6059db4bcc6eb0add4722e6c75f5abe246ce59bf1cad83344966987819`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
