# 06 · Human-in-the-Loop Complaint Triage Information System

**Technical summary.** The later-period AUC is 0.611 (block-bootstrap 95% interval 0.539 to 0.697), while top-5% lift is 1.00 (95% interval 0.33 to 2.46); the ranking model fails the deployment gate.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/cfpb-fintech-complaint-operations/outputs/report.md)
- [Review the project design](../projects/cfpb-fintech-complaint-operations/PROJECT.md)
- [Inspect the source manifest](../projects/cfpb-fintech-complaint-operations/source-manifest.json)
- [Inspect the machine-readable results](../projects/cfpb-fintech-complaint-operations/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/cfpb-fintech-complaint-operations/outputs/decision/report/decision-report.md)

![Representative evidence figure for Human-in-the-Loop Complaint Triage Information System](../figures/06-cfpb-fintech-complaint-operations.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Financial Technology |
| Adaptive route | descriptive → predictive |
| Analytical question | Does a privacy-minimized complaint model create reliable ranking gain over random review in a later calendar period? |
| Prepared rows | 13,534 |
| Valid terminal output | do not deploy |

## Capability path

| Role | Capability |
|---|---|
| Primary | **Data systems and governance** — Make data contracts, semantics, lineage, privacy, human review, failure states, and reproducibility part of the analytical system. |
| Supporting | AI and model validation, Analytics to action |

### Reviewer-visible signals

- privacy minimization
- calendar holdout
- human review
- do not deploy

Capability labels help readers find a relevant precedent. They do not upgrade
the evidence, permitted use, or empirical result of this case.

## Evidence-backed findings

- **Later-period untimely-response prevalence:** 2.5%
- **Later-period AUC:** 0.611 (95% block interval 0.539–0.697)
- **Top-5% lift versus random:** 1.00 (95% interval 0.33–2.46)
- **Decision:** do_not_deploy

## Methods selected for this case

- privacy-minimized administrative data
- calendar train-validation-test split
- rare-event calibration
- cumulative gain and capacity lift
- day-block bootstrap
- 500-label-permutation null benchmark

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

The timely flag is not complaint merit, harm, resolution quality, company quality, or compliance; the 2022 model may not transport.

## Source identity

- **Dataset:** [Consumer Complaint Database: Money Transfer, Virtual Currency, or Money Service](https://www.consumerfinance.gov/data-research/consumer-complaints/)
- **Publisher:** Consumer Financial Protection Bureau
- **Version:** Closed 2022 UTC date window; privacy-minimized extract created 2026-07-27
- **Accessed:** 2026-07-27
- **License:** CC0
- **Analytical grain:** one CFPB complaint received in 2022 for a money-transfer, virtual-currency, or money-service product

### Reviewed source-snapshot hashes

- `cfpb-digital-payments-2022-sanitized.csv` — `88057035226470e0a1291486198ff81325ae98eb8ba3ad3c881bb3960790d35b`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
