# 01 · Heart-Failure Follow-up Risk and Survival

**Technical summary.** Low ejection fraction is associated with higher observed risk; censoring-aware analysis supports external triage validation, not a treatment recommendation.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/population-health-survival/outputs/report.md)
- [Review the project design](../projects/population-health-survival/PROJECT.md)
- [Inspect the source manifest](../projects/population-health-survival/source-manifest.json)
- [Inspect the machine-readable results](../projects/population-health-survival/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/population-health-survival/outputs/decision/report/decision-report.md)

![Multivariable Cox proportional-hazards estimates for the heart-failure cohort](../figures/01-survival.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Population health |
| Adaptive route | descriptive → predictive → prescriptive |
| Analytical question | How should censored follow-up evidence inform an illustrative triage-rule comparison without becoming a treatment claim? |
| Prepared rows | 299 |
| Valid terminal output | Illustrative triage comparison requiring prospective or external validation |

## Evidence-backed findings

- **Observed death-event rate:** 32.1%
- **Observed 180-day survival:** 65.4%
- **Low-versus-higher ejection-fraction risk difference:** 33.0% (95% bootstrap interval 20.9%–44.7%)
- **Apparent Cox Harrell C-index:** 0.731

## Methods selected for this case

- Kaplan-Meier survival
- Breslow-tie Cox proportional hazards
- 180-day calibration
- patient bootstrap
- candidate protocol comparison

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Small observational cohort, incomplete treatment information, analyst-defined thresholds, and no causal treatment estimand.

## Source identity

- **Dataset:** [Heart Failure Clinical Records](https://doi.org/10.24432/C5Z89R)
- **Publisher:** UCI Machine Learning Repository
- **Version:** UCI static archive snapshot; source file timestamp 2023-05-22
- **Accessed:** 2026-07-27
- **License:** CC BY 4.0
- **Analytical grain:** one de-identified patient follow-up record

### Reviewed source-snapshot hashes

- `uci-heart-failure.zip` — `f0739603e2f9573ffc7d509573cbf9bcb4cc889e4eea0f35a75bec68fc9163d7`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
