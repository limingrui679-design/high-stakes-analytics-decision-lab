# 11 · Population Health Risk Transport Across NHIS Cohorts

**Technical summary.** The 2017 temporal test yields an AUC of 0.846 and weighted two-year mortality of 2.32% across 58,754 linked adults.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/population-health-survival/outputs/report.md)
- [Review the project design](../projects/population-health-survival/PROJECT.md)
- [Inspect the source manifest](../projects/population-health-survival/source-manifest.json)
- [Inspect the machine-readable results](../projects/population-health-survival/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/population-health-survival/outputs/decision/report/decision-report.md)

![Representative evidence figure for Population Health Risk Transport Across NHIS Cohorts](../figures/11-population-health-survival.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Population Health |
| Adaptive route | descriptive → predictive → prescriptive |
| Analytical question | Do simple population-risk cells developed in NHIS 2016 retain discrimination and calibration in the 2017 linked-mortality cohort? |
| Prepared rows | 58,754 |
| Valid terminal output | claim-bounded decision review |

## Evidence-backed findings

- **2017 temporal-test AUC:** 0.846
- **2017 weighted two-year mortality:** 2.32%
- **Linked adult records:** 58,754
- **Terminal use:** research triage validation only

## Methods selected for this case

- Survey weighting
- temporal validation
- AUC
- Brier score
- calibration
- and bounded review protocols.

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Population-risk validation only; no individual diagnosis, treatment, or clinical deployment.

## Source identity

- **Dataset:** [Population Health Risk Transport Across NHIS Cohorts](https://www.cdc.gov/nchs/data-linkage/mortality-public.htm)
- **Publisher:** U.S. Centers for Disease Control and Prevention, National Center for Health Statistics
- **Version:** NHIS 2016 and 2017 Sample Adult files linked to 2019 public-use mortality
- **Accessed:** 2026-08-10
- **License:** U.S. Government public-use data
- **Analytical grain:** one NHIS sampled adult linked to mortality status

### Reviewed source-snapshot hashes

- `nhis-2016-2017-linked-mortality-extract.csv` — `ef2a7d308ebe9020d1d2bb53ef98115b9a60dbacacc1697c136512e8646d947a`
- `nhis-2016-2017-linked-mortality-extract.source-lock.json` — `7e660b86cddc42955e56d77842eadda11cd7e5c2dd8331fa7416a8adccb3dcd7`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
