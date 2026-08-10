# 14 · NHANES Mortality Transportability and Population Inequality

**Technical summary.** The external-cohort check yields an AUC of 0.804 and a Brier score of 0.022 across 11,820 linked adults.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/nhanes-population-transportability/outputs/report.md)
- [Review the project design](../projects/nhanes-population-transportability/PROJECT.md)
- [Inspect the source manifest](../projects/nhanes-population-transportability/source-manifest.json)
- [Inspect the machine-readable results](../projects/nhanes-population-transportability/outputs/results.json)

![Representative evidence figure for NHANES Mortality Transportability and Population Inequality](../figures/14-nhanes-population-transportability.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Biostatistics |
| Adaptive route | descriptive → diagnostic → decision |
| Analytical question | Do population mortality risk patterns transport between NHANES cohorts, and what inequality gradient remains visible? |
| Prepared rows | 11,820 |
| Valid terminal output | population research only |

## Evidence-backed findings

- **External-cohort AUC:** 0.804
- **External-cohort Brier score:** 0.022
- **Linked adults:** 11,820
- **Terminal use:** population research only

## Methods selected for this case

- Survey-weighted rates
- cross-cohort AUC/Brier/calibration
- and poverty-income-ratio gradients.

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Population research only; no individual diagnosis or treatment.

## Source identity

- **Dataset:** [NHANES Mortality Transportability and Population Inequality](https://www.cdc.gov/nchs/data-linkage/mortality-public.htm)
- **Publisher:** U.S. Centers for Disease Control and Prevention, National Center for Health Statistics
- **Version:** NHANES 2011-2012 and 2015-2016 demographics linked to 2019 mortality
- **Accessed:** 2026-08-10
- **License:** U.S. Government public-use data
- **Analytical grain:** one NHANES adult linked to 36-month mortality

### Reviewed source-snapshot hashes

- `nhanes-36-month-mortality-cohorts.csv` — `e346bd95cab22bc86b6525e02db7d41a7c2767cc26e115539944dddd4e5755ad`
- `nhanes-36-month-mortality-cohorts.source-lock.json` — `ef6a8e02bd1d0068a437e4cfd3706f04741f059f14572aae138725b8f762b358`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
