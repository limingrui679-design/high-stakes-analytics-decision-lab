# 03 · Capacity-Constrained Marketing Pilot

**Technical summary.** Pre-contact features weakly concentrate observed responses; common campaign shocks are preserved across capacity options.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/bank-marketing-response/outputs/report.md)
- [Review the project design](../projects/bank-marketing-response/PROJECT.md)
- [Inspect the source manifest](../projects/bank-marketing-response/source-manifest.json)
- [Inspect the machine-readable results](../projects/bank-marketing-response/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/bank-marketing-response/outputs/decision/report/decision-report.md)

![Representative evidence figure for Capacity-Constrained Marketing Pilot](../figures/03-bank-marketing-response.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Business Analytics |
| Adaptive route | descriptive → predictive → prescriptive |
| Analytical question | Can pre-contact information concentrate observed responses under a fixed outreach capacity without using post-contact leakage? |
| Prepared rows | 41,188 |
| Valid terminal output | randomized pilot required |

## Evidence-backed findings

- **Untouched-test AUC:** 0.650
- **Untouched-test Brier score:** 0.210
- **Top-5% observed response capture:** 7.4%
- **Shared-block P(best):** 59.0%

## Methods selected for this case

- leakage-safe feature timing
- ordered train-validation-test split
- probability calibration
- capacity capture
- shared-block bootstrap
- probability-best comparison

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Observed response concentration is not incremental lift, causal treatment effect, profit, or return on outreach.

## Source identity

- **Dataset:** [Bank Marketing](https://archive.ics.uci.edu/dataset/222/bank+marketing)
- **Publisher:** UCI Machine Learning Repository
- **Version:** UCI archive retrieved 2026-07-27; bank-additional-full.csv
- **Accessed:** 2026-07-27
- **License:** CC BY 4.0
- **Analytical grain:** one direct-marketing contact outcome

### Reviewed source-snapshot hashes

- `uci-bank-marketing.zip` — `e0bf5f5de5b846e2f18e9d90606637267d46dfa260e0f17bb12e605db5efbeb4`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
