# Which duration profile should remain in exploratory risk review under the historical evidence

*Financial risk engineering · Historical-risk review only · 10,000 modeled simulations*

## Executive Summary

- **Provisional preference — Short Baseline.** It is the highest-ranked feasible option, with decision value score **80.0/100** and a modeled **69% probability of being best among decision-feasible alternatives**.
- **The lead is narrow rather than absolute.** It leads the next feasible option, Intermediate, by **0.029 utility points**.
- **Modeled robustness is 91/100.** The option remains preferred in **100%** of two-sided weight stresses and **100%** of probability-weighted scenario comparisons.
- **Shared-shock sensitivity is explicit.** Relative to independent residuals, the declared factor model changes this option's P(best) by **+1.8%** and CVaR10 by **-0.000**; the ×1.35 loading stress does not change the modeled winner.
- **Constraint-breach evidence — 0/10,000 observed; U95 0.00%; declared support excludes breach.** Feasibility uses the one-sided 95% upper bound against the **10.0% tolerance**; a zero event count is never presented as proof of zero real-world risk.
- **Decision status — Provisional—validate before action.** The current blockers are: evidence is not labeled for operational use.
- **Evidence boundary.** No causal claim unless explicitly identified in the source design; the decision comparison is exploratory.
- **Parameter lineage.** 57/57 governed parameters have a resolved source and approval-chain reference.

![Decision summary](figures/decision-scorecard.svg)

**Decision owner:** Hypothetical domain review panel; no real owner authorization  
**Decision question:** Which duration profile should remain in exploratory risk review under the historical evidence?

## Decision status and modeled robustness

**Status: Provisional—validate before action.** 7 of 8 configured readiness checks pass. The robustness score summarizes model behavior; it is not a posterior probability that the real-world decision is correct and cannot upgrade illustrative evidence into operational evidence.

![Decision robustness profile](figures/robustness-profile.svg)

## Short Baseline leads on balanced value, not every dimension

**The preferred option earns its position through Worst historical day, Historical ES95 loss.** The comparison still exposes a trade-off on **no single modeled criterion**, so the decision should be presented as a transparent compromise rather than a universal optimum.

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

**Short Baseline has expected utility 0.808, but its worst-decile average falls to 0.778.** The widest criterion-level uncertainty for this option is associated with **Historical annualized return**, making it a priority for further evidence collection.

![Utility uncertainty and downside](figures/utility-uncertainty.svg)

The interval chart prevents a precise-looking average from obscuring overlap among alternatives. A close overlap means the practical decision may depend more on constraints, reversibility, and the cost of learning than on a small utility difference.

## Shared shocks change the uncertainty question

**The declared factor model gives Short Baseline P(best) 69%, versus 67% under independent residuals and 71% under the stronger correlation stress.** Its CVaR10 moves from 0.778 independently to 0.778 under declared dependence and 0.777 under stress.

![Correlation and tail-risk stress](figures/correlation-stress.svg)

The three states use matched seeds, stratified scenario counts, and the same marginal distributions. Differences therefore isolate the declared dependence structure as closely as this simulation design allows. The Gaussian copula remains an approximation: factor definitions, signs, and loadings must be replaced or approved using domain evidence.

## Scenario tests show when the preferred option is most exposed

**The weakest modeled environment is Adverse transfer to a new setting, where the preferred option's risk-adjusted utility is 0.797.** The same feasible alternative remains ahead in every modeled scenario.

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
2. **Reduce uncertainty in Historical annualized return.** Validate or replace the widest uncertainty input using experimental, quasi-experimental, observational, or engineering evidence appropriate to the domain.
3. **Monitor the Adverse transfer to a new setting trigger.** Specify leading indicators and a contingency response before rollout.
4. **Review distributional impacts with affected stakeholders.** Examine absolute group outcomes alongside disparity measures and document unresolved normative choices.

## Further questions

- Which empirical or elicited evidence would best validate the declared factor loadings?
- Which omitted externality or stakeholder could materially alter the criterion set?
- What evidence would justify replacing the current scenario probabilities?
- Is the preferred option reversible if early monitoring contradicts the model?

## Caveats and assumptions

- **Evidence type:** source-backed exploratory project evidence
- **Evidence as of:** 2026-07-27
- **Permitted decision use:** exploratory
- **Causal status:** No causal claim unless explicitly identified in the source design; the decision comparison is exploratory.
- **Dependence model:** latent_factor_gaussian_copula with 1 declared shared factor(s); the loading stress is ×1.35. Copula choice and loadings remain assumptions.
- **Parameter provenance:** 100% source coverage and 100% approval coverage for the declared decision use. Approval for exploratory use is not operational approval.
- **Zero-breach interpretation:** zero simulated events means either no event was observed in the finite run or the declared bounded input support excludes a breach. Neither statement establishes zero real-world risk.
- Approximate hypothetical portfolios omit convexity, security selection, bid–ask costs, taxes, financing, and investability.
- Weights, scales, scenarios, and correlation loadings are analyst judgments without external approval.

<details>
<summary><strong>Detailed numerical appendix and reproducibility</strong></summary>

### Ranked alternatives

| Rank | Alternative | Feasible | Value score | Expected utility | CVaR10 | P(best feasible) | P(best all) | Breach evidence | Feasible Pareto |
|---:|---|:---:|---:|---:|---:|---:|---:|---|:---:|
| 1 | Short Baseline | Yes | 80.0 | 0.808 | 0.778 | 69.3% | 69.3% | 0/10,000 observed; U95 0.00%; declared support excludes breach | Yes |
| 2 | Intermediate | Yes | 77.1 | 0.782 | 0.739 | 14.6% | 14.6% | 0/10,000 observed; U95 0.00%; declared support excludes breach | No |
| 3 | Barbell | Yes | 76.7 | 0.777 | 0.734 | 12.5% | 12.5% | 0/10,000 observed; U95 0.00%; declared support excludes breach | No |
| 4 | Long Duration | Yes | 73.0 | 0.746 | 0.685 | 3.6% | 3.6% | 0/10,000 observed; U95 0.00%; declared support excludes breach | No |

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

#### Short Baseline

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Historical annualized return | 30.0% | 0.015 return fraction | -0.005 return fraction–0.037 return fraction | 0.522 | 0.0% |
| Historical ES95 loss | 45.0% | 0.004 daily loss fraction | 0.004 daily loss fraction–0.005 daily loss fraction | 0.944 | 0.0% |
| Worst historical day | 25.0% | 0.009 daily loss fraction | 0.007 daily loss fraction–0.011 daily loss fraction | 0.906 | 0.0% |

#### Intermediate

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Historical annualized return | 30.0% | 0.01 return fraction | -0.018 return fraction–0.037 return fraction | 0.501 | 0.0% |
| Historical ES95 loss | 45.0% | 0.006 daily loss fraction | 0.006 daily loss fraction–0.007 daily loss fraction | 0.920 | 0.0% |
| Worst historical day | 25.0% | 0.013 daily loss fraction | 0.01 daily loss fraction–0.015 daily loss fraction | 0.870 | 0.0% |

#### Barbell

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Historical annualized return | 30.0% | 0.008 return fraction | -0.021 return fraction–0.041 return fraction | 0.491 | 0.0% |
| Historical ES95 loss | 45.0% | 0.006 daily loss fraction | 0.006 daily loss fraction–0.007 daily loss fraction | 0.921 | 0.0% |
| Worst historical day | 25.0% | 0.014 daily loss fraction | 0.01 daily loss fraction–0.015 daily loss fraction | 0.864 | 0.0% |

#### Long Duration

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Historical annualized return | 30.0% | 0.004 return fraction | -0.037 return fraction–0.046 return fraction | 0.474 | 0.0% |
| Historical ES95 loss | 45.0% | 0.009 daily loss fraction | 0.008 daily loss fraction–0.01 daily loss fraction | 0.889 | 0.0% |
| Worst historical day | 25.0% | 0.019 daily loss fraction | 0.013 daily loss fraction–0.021 daily loss fraction | 0.814 | 0.0% |

### Correlation sensitivity

| Dependence state | Modeled winner | Recommended option P(best) | CVaR10 | Breach U95 |
|---|---|---:|---:|---:|
| Independent residuals | Short Baseline | 67.5% | 0.778 | 0.00% |
| Declared factor model | Short Baseline | 69.3% | 0.778 | 0.00% |
| Loading stress ×1.35 | Short Baseline | 70.8% | 0.777 | 0.00% |

### Parameter provenance and approval

Coverage: **57/57 parameters sourced** and **57/57 approved for the declared use**. Every expanded JSON path is recorded in `decision-results.json` under `parameter_provenance.records`.

| Source ID | Source type | Owner | Approved uses | Approval chain |
|---|---|---|---|---|
| `treasury-risk-engineering-analysis-output` | reproducible_project_output | Original publisher and repository analysis author | exploratory | 1. model_author (approved) |
| `portfolio-author-governance-assumptions` | analyst_judgment_not_externally_approved | Repository analysis author | exploratory | 1. self_review (approved) |
### Sources and reproducibility

- U.S. Department of the Treasury. Daily Treasury Par Yield Curve Rates. Accessed 2026-07-27.
- projects/treasury-risk-engineering/outputs/results.json
- Engine version: `7.0.0`
- Samples: `10000`
- Random seed: `20260727`
- Sampling design: Stratified scenario allocation with a declared latent-factor Gaussian copula, shared shocks across alternatives, marginal-preserving inverse transforms, and matched independent/correlation-stress counterfactuals.
- Case SHA-256: `560e97bcaec27b9bfed1206430146a2f237a641d666148a2fd512dae7ff98d36`

### Decision notes

- The comparison selects a candidate for further review, not an operational action.
- No institutional, clinical, financial, engineering, or policy approval is represented.

</details>

> Source-backed exploratory analysis, not an authorization to act. Domain review and current local evidence remain required.
