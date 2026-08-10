# Which fixed-budget station-hour rebalancing scenario should advance to a bounded operations pilot

*Operations research and systems engineering · Prospective operations pilot only · 3,000 modeled simulations*

## Executive Summary

- **Provisional preference — Top 25 Station Hours.** It is the highest-ranked feasible option, with decision value score **43.5/100** and a modeled **100% probability of being best among decision-feasible alternatives**.
- **The lead is meaningful rather than absolute.** It leads the next feasible option, Top 10 Station Hours, by **0.049 utility points**.
- **Modeled robustness is 100/100.** The option remains preferred in **100%** of two-sided weight stresses and **100%** of probability-weighted scenario comparisons.
- **Shared-shock sensitivity is explicit.** Relative to independent residuals, the declared factor model changes this option's P(best) by **+0.0%** and CVaR10 by **+0.000**; the ×1.35 loading stress does not change the modeled winner.
- **Constraint-breach evidence — 0/3,000 observed; U95 0.00%; declared support excludes breach.** Feasibility uses the one-sided 95% upper bound against the **10.0% tolerance**; a zero event count is never presented as proof of zero real-world risk.
- **Decision status — Provisional—validate before action.** The current blockers are: evidence is not labeled for operational use.
- **Evidence boundary.** No causal claim unless explicitly identified in the source design; the decision comparison is exploratory.
- **Parameter lineage.** 48/48 governed parameters have a resolved source and approval-chain reference.

![Decision summary](figures/decision-scorecard.svg)

**Decision owner:** Hypothetical domain review panel; no real owner authorization
**Decision question:** Which fixed-budget station-hour rebalancing scenario should advance to a bounded operations pilot?

## Decision status and modeled robustness

**Status: Provisional—validate before action.** 7 of 8 configured readiness checks pass. The robustness score summarizes model behavior; it is not a posterior probability that the real-world decision is correct and cannot upgrade illustrative evidence into operational evidence.

![Decision robustness profile](figures/robustness-profile.svg)

## Top 25 Station Hours leads on balanced value, not every dimension

**The preferred option earns its position through Modeled residual imbalance, Allocation concentration.** The comparison still exposes a trade-off on **no single modeled criterion**, so the decision should be presented as a transparent compromise rather than a universal optimum.

![Alternative ranking](figures/alternative-ranking.svg)

The ranking combines expected value with downside performance and excludes options whose one-sided 95% breach-frequency upper bound exceeds **10%**. Probability-best remains visible because a lower-ranked option may still win in a material share of simulations.

## The conservative risk boundary determines feasibility

**The decision rule compares the one-sided 95% breach-frequency upper bound—not only the observed simulation rate—with the 10.0% tolerance.** This makes finite-sample uncertainty visible and prevents a zero event count from being presented as proof of zero risk.

![Constraint risk boundary](figures/constraint-risk.svg)

The dark circle is the observed breach rate; the diamond is its conservative upper bound. An option fails the modeled feasibility rule when that diamond crosses the red tolerance line. The test is conditional on the declared distributions and cannot cover omitted real-world hazards.

## The criterion profile reveals where the preferred option earns—and gives up—value

Each cell below places an outcome on its declared worst-to-best reference scale. This avoids recalibrating the chart around whichever alternatives happen to be present.

![Criterion scorecard](figures/criterion-scorecard.svg)

**The decision is therefore driven by an explicit value model.** A stakeholder who places substantially more weight on no single modeled criterion may reasonably prefer another option; the two-sided weight-sensitivity section tests that possibility directly. The preferred option clips **0.0%** of criterion draws at the declared reference-scale bounds.

## Downside risk remains visible behind the average

**Top 25 Station Hours has expected utility 0.443, but its worst-decile average falls to 0.410.** The widest criterion-level uncertainty for this option is associated with **Modeled residual imbalance**, making it a priority for further evidence collection.

![Utility uncertainty and downside](figures/utility-uncertainty.svg)

The interval chart prevents a precise-looking average from obscuring overlap among alternatives. A close overlap means the practical decision may depend more on constraints, reversibility, and the cost of learning than on a small utility difference.

## Shared shocks change the uncertainty question

**The declared factor model gives Top 25 Station Hours P(best) 100%, versus 100% under independent residuals and 100% under the stronger correlation stress.** Its CVaR10 moves from 0.410 independently to 0.410 under declared dependence and 0.410 under stress.

![Correlation and tail-risk stress](figures/correlation-stress.svg)

The three states use matched seeds, stratified scenario counts, and the same marginal distributions. Differences therefore isolate the declared dependence structure as closely as this simulation design allows. The Gaussian copula remains an approximation: factor definitions, signs, and loadings must be replaced or approved using domain evidence.

## Scenario tests show when the preferred option is most exposed

**The weakest modeled environment is Adverse transfer to a new setting, where the preferred option's risk-adjusted utility is 0.410.** The same feasible alternative remains ahead in every modeled scenario.

![Scenario performance](figures/scenario-performance.svg)

The preferred option leads in **100%** of the probability-weighted scenario comparison. Scenario probabilities are assumptions, not forecasts with guaranteed calibration. They are useful because they reveal which external conditions deserve monitoring and which contingency plans should be prepared before implementation.

## Distributional effects remain an evidence gap

**No group-level outcomes were supplied for this case.** Before operational use, the analysis should add affected groups, absolute outcomes, disparity measures, and a qualitative review of harms that cannot be reduced to a numeric parity ratio.

## The result is stable to stakeholder priorities

**The baseline choice survives 100% of local weight stresses.** No single criterion emphasis changes the preferred feasible alternative.

![Weight sensitivity](figures/weight-sensitivity.svg)

This test both increases and decreases each criterion weight while preserving risk adjustment. It remains a local stress test rather than a substitute for formal stakeholder elicitation. If the winner changes under a plausible emphasis, the next step is deliberation and better evidence—not hiding the sensitivity.

## Recommended next steps

1. **Resolve the failed readiness checks before acting.** evidence is not labeled for operational use.
2. **Reduce uncertainty in Modeled residual imbalance.** Validate or replace the widest uncertainty input using experimental, quasi-experimental, observational, or engineering evidence appropriate to the domain.
3. **Monitor the Adverse transfer to a new setting trigger.** Specify leading indicators and a contingency response before rollout.
4. **Review distributional impacts with affected stakeholders.** Examine absolute group outcomes alongside disparity measures and document unresolved normative choices.

## Further questions

- Which empirical or elicited evidence would best validate the declared factor loadings?
- Which omitted externality or stakeholder could materially alter the criterion set?
- What evidence would justify replacing the current scenario probabilities?
- Is the preferred option reversible if early monitoring contradicts the model?

## Caveats and assumptions

- **Evidence type:** source-backed exploratory project evidence
- **Evidence as of:** 2026-08-10
- **Permitted decision use:** exploratory
- **Causal status:** No causal claim unless explicitly identified in the source design; the decision comparison is exploratory.
- **Dependence model:** latent_factor_gaussian_copula with 1 declared shared factor(s); the loading stress is ×1.35. Copula choice and loadings remain assumptions.
- **Parameter provenance:** 100% source coverage and 100% approval coverage for the declared decision use. Approval for exploratory use is not operational approval.
- **Zero-breach interpretation:** zero simulated events means either no event was observed in the finite run or the declared bounded input support excludes a breach. Neither statement establishes zero real-world risk.
- Pickups minus returns is an imbalance proxy, not observed stockout demand; modeled residual imbalance is not an achieved service result.
- Weights, scales, scenarios, and correlation loadings are analyst judgments without external approval.

<details>
<summary><strong>Detailed numerical appendix and reproducibility</strong></summary>

### Ranked alternatives

| Rank | Alternative | Feasible | Value score | Expected utility | CVaR10 | P(best feasible) | P(best all) | Breach evidence | Feasible Pareto |
|---:|---|:---:|---:|---:|---:|---:|---:|---|:---:|
| 1 | Top 25 Station Hours | Yes | 43.5 | 0.443 | 0.410 | 100.0% | 100.0% | 0/3,000 observed; U95 0.00%; declared support excludes breach | Yes |
| 2 | Top 10 Station Hours | Yes | 38.6 | 0.395 | 0.360 | 0.0% | 0.0% | 0/3,000 observed; U95 0.00%; declared support excludes breach | No |
| 3 | Baseline: Monitoring Only | Yes | 38.3 | 0.386 | 0.376 | 0.0% | 0.0% | 0/3,000 observed; U95 0.00%; declared support excludes breach | Yes |

### Readiness checks

| Check | Result |
|---|:---:|
| Feasible Alternative | Pass |
| Probability Best | Pass |
| Weight Stability | Pass |
| Scenario Stability | Pass |
| Scale Clipping | Pass |
| Parameter Provenance | Pass |
| Approval Scope | Pass |
| Operational Evidence | Fail |

### Constraint diagnostics

No hard constraints were supplied.

### Criterion outcomes

#### Top 25 Station Hours

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Modeled residual imbalance | 45.0% | 0.863 share | 0.846 share–0.914 share | 0.137 | 0.0% |
| Station-hours with residual imbalance | 35.0% | 0.456 share | 0.447 share–0.483 share | 0.544 | 0.0% |
| Allocation concentration | 20.0% | 0.044 Herfindahl index | 0.043 Herfindahl index–0.047 Herfindahl index | 0.956 | 0.0% |

#### Top 10 Station Hours

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Modeled residual imbalance | 45.0% | 0.936 share | 0.917 share–0.991 share | 0.064 | 0.0% |
| Station-hours with residual imbalance | 35.0% | 0.464 share | 0.455 share–0.491 share | 0.536 | 0.0% |
| Allocation concentration | 20.0% | 0.107 Herfindahl index | 0.105 Herfindahl index–0.113 Herfindahl index | 0.893 | 0.0% |

#### Baseline: Monitoring Only

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Modeled residual imbalance | 45.0% | 1.02 share | 1 share–1.08 share | 0.000 | 25.0% |
| Station-hours with residual imbalance | 35.0% | 0.469 share | 0.46 share–0.497 share | 0.531 | 0.0% |
| Allocation concentration | 20.0% | 0 Herfindahl index | 0 Herfindahl index–0 Herfindahl index | 1.000 | 0.0% |

### Correlation sensitivity

| Dependence state | Modeled winner | Recommended option P(best) | CVaR10 | Breach U95 |
|---|---|---:|---:|---:|
| Independent residuals | Top 25 Station Hours | 100.0% | 0.410 | 0.00% |
| Declared factor model | Top 25 Station Hours | 100.0% | 0.410 | 0.00% |
| Loading stress ×1.35 | Top 25 Station Hours | 100.0% | 0.410 | 0.00% |

### Parameter provenance and approval

Coverage: **48/48 parameters sourced** and **48/48 approved for the declared use**. Every expanded JSON path is recorded in `decision-results.json` under `parameter_provenance.records`.

| Source ID | Source type | Owner | Approved uses | Approval chain |
|---|---|---|---|---|
| `bike-demand-operations-analysis-output` | reproducible_project_output | Original publisher and repository analysis author | exploratory | 1. model_author (approved) |
| `portfolio-author-governance-assumptions` | analyst_judgment_not_externally_approved | Repository analysis author | exploratory | 1. self_review (approved) |
### Sources and reproducibility

- Citi Bike. Jersey City trip history, January-December 2021; derived station-hour aggregate.
- projects/bike-demand-operations/outputs/results.json
- Engine version: `7.0.0`
- Samples: `3000`
- Random seed: `20260810`
- Sampling design: Stratified scenario allocation with a declared latent-factor Gaussian copula, shared shocks across alternatives, marginal-preserving inverse transforms, and matched independent/correlation-stress counterfactuals.
- Case SHA-256: `eb7c46986234ba13f6a8806f9c1c3566caa68d6e71096d3e608f0757d3379913`

### Decision notes

- The comparison selects a candidate for further review, not an operational action.
- No institutional, clinical, financial, engineering, or policy approval is represented.

</details>

> Source-backed exploratory analysis, not an authorization to act. Domain review and current local evidence remain required.
