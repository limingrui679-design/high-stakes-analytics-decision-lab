# 13 · Small-Sample Repeated-Measures Inference

**Technical summary.** Pseudoword passages increase fixation-duration burden; paired analysis preserves the repeated-measures design and exposes group heterogeneity.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/behavioral-reading-experiment/outputs/report.md)
- [Review the project design](../projects/behavioral-reading-experiment/PROJECT.md)
- [Inspect the source manifest](../projects/behavioral-reading-experiment/source-manifest.json)
- [Inspect the machine-readable results](../projects/behavioral-reading-experiment/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/behavioral-reading-experiment/outputs/decision/report/decision-report.md)

![Representative evidence figure for Small-Sample Repeated-Measures Inference](../figures/13-behavioral-reading-experiment.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Statistics |
| Adaptive route | descriptive → inferential |
| Analytical question | How does passage type change eye-movement burden within the same participant, and how stable is the contrast across reader groups? |
| Prepared rows | 57 |
| Valid terminal output | claim-bounded decision review |

## Evidence-backed findings

- **Complete participant pairs:** 57
- **Mean paired fixation-duration difference:** 34.25 (95% bootstrap interval 25.87–43.35)
- **Holm-adjusted sign-flip p-value:** 0.0003
- **80% power design-sensitivity MDE:** 12.22

## Methods selected for this case

- within-participant contrasts
- participant bootstrap
- sign-flip inference
- Holm multiplicity correction
- label permutation
- minimum-detectable-effect sensitivity

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

The public sample is small and does not establish downstream educational outcomes or an intervention effect.

## Source identity

- **Dataset:** [Eye movements of dyslexic and average readers in meaningful and pseudoword passage reading](https://doi.org/10.7910/DVN/3YCB56)
- **Publisher:** Harvard Dataverse
- **Version:** V1; file UNF:6:XJRpAtIOiQJZWyv7L3uj3A==
- **Accessed:** 2026-07-27
- **License:** CC0 1.0
- **Analytical grain:** one de-identified study participant with repeated passage measures

### Reviewed source-snapshot hashes

- `pseudoword-passage-reading.tsv` — `9b3bb62263779fc847a7ae2c7f7ab7d6e248d6595648f44c92f44769d66750b8`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
