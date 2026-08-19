# 10 · Social-Norm Field Experiment with Household-Clustered Inference

**Technical summary.** The Neighbors arm has the largest observed intent-to-treat effect at 8.1%, with a household-clustered 95% interval of 7.5% to 8.8%.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/social-norm-field-experiment/outputs/report.md)
- [Review the project design](../projects/social-norm-field-experiment/PROJECT.md)
- [Inspect the source manifest](../projects/social-norm-field-experiment/source-manifest.json)
- [Inspect the machine-readable results](../projects/social-norm-field-experiment/outputs/results.json)

![Representative evidence figure for Social-Norm Field Experiment with Household-Clustered Inference](../figures/10-social-norm-field-experiment.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Field Experiments |
| Adaptive route | descriptive → diagnostic → decision |
| Analytical question | What were the intent-to-treat turnout effects of randomized social-pressure mailings after household clustering? |
| Prepared rows | 10 |
| Valid terminal output | observed field effect no new campaign authorization |

## Capability path

| Role | Capability |
|---|---|
| Primary | **Behavior and policy evidence** — Separate observed behavior, randomized or associational evidence, mechanisms, intervention claims, ethics, and implementation authority. |
| Supporting | Statistical research |

### Reviewer-visible signals

- randomized assignment
- household clustering
- intent-to-treat
- no new campaign authorization

Capability labels help readers find a relevant precedent. They do not upgrade
the evidence, permitted use, or empirical result of this case.

## Evidence-backed findings

- **Source individuals analyzed:** 344,084
- **Largest observed ITT:** Neighbors 8.1%
- **Household-clustered 95% interval:** 7.5% to 8.8%
- **Causal scope:** the randomized experiment only

## Methods selected for this case

- Randomized-arm rates
- household-clustered sandwich variance
- 95% intervals
- and descriptive strata contrasts.

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Causal scope is the historical randomized experiment; no new campaign authorization.

## Source identity

- **Dataset:** [Social-Norm Field Experiment with Household-Clustered Inference](https://doi.org/10.60600/YU/CGMWNW)
- **Publisher:** Yale Institution for Social and Policy Studies
- **Version:** Gerber-Green-Larimer 2008 replication file; non-identifying aggregate and locally computed clustered inference
- **Accessed:** 2026-08-10
- **License:** CC0 1.0 (Yale Dataverse dataset)
- **Analytical grain:** one treatment by prior-turnout aggregate

### Reviewed source-snapshot hashes

- `terms-compliant-treatment-aggregate.csv` — `86621bba1ca677c6c56fea2412143fe74e8fc4834b46c17f7accc8cfb34f61e6`
- `cluster-robust-itt.json` — `63219329010e08a005163c6bbe15227ccb2a73139995bb0f1ba5ceb8cbe45f61`
- `external-source-lock.json` — `336c93d11ad1536a3124ac93709cdf3e468a1483c75a7ae71ac0a27fd4aa3491`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
