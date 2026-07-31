# Which transparent portfolio rule should advance to a prospective paper-portfolio validation

*Asset allocation and financial risk · Research-only prospective validation · 10,000 modeled simulations*

## Executive Summary

- **Provisional preference — Baseline: Walk Forward Inverse Volatility.** It is the highest-ranked feasible option, with decision value score **74.3/100** and a modeled **100% probability of being best among decision-feasible alternatives**.
- **The lead is narrow rather than absolute.** It leads the next feasible option, Equal Weight Benchmark, by **0.017 utility points**.
- **Modeled robustness is 100/100.** The option remains preferred in **100%** of two-sided weight stresses and **100%** of probability-weighted scenario comparisons.
- **Shared-shock sensitivity is explicit.** Relative to independent residuals, the declared factor model changes this option's P(best) by **+0.0%** and CVaR10 by **+0.000**; the ×1.35 loading stress does not change the modeled winner.
- **Constraint-breach evidence — 0/10,000 observed; U95 0.00%; declared support excludes breach.** Feasibility uses the one-sided 95% upper bound against the **10.0% tolerance**; a zero event count is never presented as proof of zero real-world risk.
- **Decision status — Provisional—validate before action.** The current blockers are: evidence is not labeled for operational use.
- **Evidence boundary.** No causal claim unless explicitly identified in the source design; the decision comparison is exploratory.
- **Parameter lineage.** 48/48 governed parameters have a resolved source and approval-chain reference.

![Decision summary](figures/decision-scorecard.svg)

**Decision owner:** Hypothetical domain review panel; no real owner authorization  
**Decision question:** Which transparent portfolio rule should advance to a prospective paper-portfolio validation?

## Decision status and modeled robustness

**Status: Provisional—validate before action.** 7 of 8 configured readiness checks pass. The robustness score summarizes model behavior; it is not a posterior probability that the real-world decision is correct and cannot upgrade illustrative evidence into operational evidence.

![Decision robustness profile](figures/robustness-profile.svg)

## Baseline: Walk Forward Inverse Volatility leads on balanced value, not every dimension

**The preferred option earns its position through Historical maximum drawdown, Historical daily ES95 loss.** The comparison still exposes a trade-off on **Historical annualized return**, so the decision should be presented as a transparent compromise rather than a universal optimum.

![Alternative ranking](figures/alternative-ranking.svg)

The ranking combines expected value with downside performance and excludes options whose one-sided 95% breach-frequency upper bound exceeds **10%**. Probability-best remains visible because a lower-ranked option may still win in a material share of simulations.

## The conservative risk boundary determines feasibility

**The decision rule compares the one-sided 95% breach-frequency upper bound—not only the observed simulation rate—with the 10.0% tolerance.** This makes finite-sample uncertainty visible and prevents a zero event count from being presented as proof of zero risk.

![Constraint risk boundary](figures/constraint-risk.svg)

The dark circle is the observed breach rate; the diamond is its conservative upper bound. An option fails the modeled feasibility rule when that diamond crosses the red tolerance line. The test is conditional on the declared distributions and cannot cover omitted real-world hazards.

## The criterion profile reveals where the preferred option earns—and gives up—value

Each cell below places an outcome on its declared worst-to-best reference scale. This avoids recalibrating the chart around whichever alternatives happen to be present.

![Criterion scorecard](figures/criterion-scorecard.svg)

**The decision is therefore driven by an explicit value model.** A stakeholder who places substantially more weight on Historical annualized return may reasonably prefer another option; the two-sided weight-sensitivity section tests that possibility directly. The preferred option clips **0.0%** of criterion draws at the declared reference-scale bounds.

## Downside risk remains visible behind the average

**Baseline: Walk Forward Inverse Volatility has expected utility 0.743, but its worst-decile average falls to 0.742.** The widest criterion-level uncertainty for this option is associated with **Historical maximum drawdown**, making it a priority for further evidence collection.

![Utility uncertainty and downside](figures/utility-uncertainty.svg)

The interval chart prevents a precise-looking average from obscuring overlap among alternatives. A close overlap means the practical decision may depend more on constraints, reversibility, and the cost of learning than on a small utility difference.

## Shared shocks change the uncertainty question

**The declared factor model gives Baseline: Walk Forward Inverse Volatility P(best) 100%, versus 100% under independent residuals and 100% under the stronger correlation stress.** Its CVaR10 moves from 0.742 independently to 0.742 under declared dependence and 0.742 under stress.

![Correlation and tail-risk stress](figures/correlation-stress.svg)

The three states use matched seeds, stratified scenario counts, and the same marginal distributions. Differences therefore isolate the declared dependence structure as closely as this simulation design allows. The Gaussian copula remains an approximation: factor definitions, signs, and loadings must be replaced or approved using domain evidence.

## Scenario tests show when the preferred option is most exposed

**The weakest modeled environment is Adverse transfer to a new setting, where the preferred option's risk-adjusted utility is 0.742.** The same feasible alternative remains ahead in every modeled scenario.

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
2. **Reduce uncertainty in Historical maximum drawdown.** Validate or replace the widest uncertainty input using experimental, quasi-experimental, observational, or engineering evidence appropriate to the domain.
3. **Monitor the Adverse transfer to a new setting trigger.** Specify leading indicators and a contingency response before rollout.
4. **Review distributional impacts with affected stakeholders.** Examine absolute group outcomes alongside disparity measures and document unresolved normative choices.

## Further questions

- Which empirical or elicited evidence would best validate the declared factor loadings?
- Which omitted externality or stakeholder could materially alter the criterion set?
- What evidence would justify replacing the current scenario probabilities?
- Is the preferred option reversible if early monitoring contradicts the model?

## Caveats and assumptions

- **Evidence type:** source-backed exploratory project evidence
- **Evidence as of:** 2026-07-30
- **Permitted decision use:** exploratory
- **Causal status:** No causal claim unless explicitly identified in the source design; the decision comparison is exploratory.
- **Dependence model:** latent_factor_gaussian_copula with 1 declared shared factor(s); the loading stress is ×1.35. Copula choice and loadings remain assumptions.
- **Parameter provenance:** 100% source coverage and 100% approval coverage for the declared decision use. Approval for exploratory use is not operational approval.
- **Zero-breach interpretation:** zero simulated events means either no event was observed in the finite run or the declared bounded input support excludes a breach. Neither statement establishes zero real-world risk.
- The provider snapshot and ETF proxies omit taxes, bid–ask spreads, market impact, tracking error, investor liabilities, capacity, and future regimes. Historical adjusted prices do not establish future performance or suitability.
- Weights, scales, scenarios, and correlation loadings are analyst judgments without external approval.

<details>
<summary><strong>Detailed numerical appendix and reproducibility</strong></summary>

### Ranked alternatives

| Rank | Alternative | Feasible | Value score | Expected utility | CVaR10 | P(best feasible) | P(best all) | Breach evidence | Feasible Pareto |
|---:|---|:---:|---:|---:|---:|---:|---:|---|:---:|
| 1 | Baseline: Walk Forward Inverse Volatility | Yes | 74.3 | 0.743 | 0.742 | 100.0% | 100.0% | 0/10,000 observed; U95 0.00%; declared support excludes breach | Yes |
| 2 | Equal Weight Benchmark | Yes | 72.6 | 0.726 | 0.725 | 0.0% | 0.0% | 0/10,000 observed; U95 0.00%; declared support excludes breach | Yes |
| 3 | 60/40 Equity Treasury Benchmark | Yes | 68.7 | 0.688 | 0.686 | 0.0% | 0.0% | 0/10,000 observed; U95 0.00%; declared support excludes breach | Yes |

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

#### Baseline: Walk Forward Inverse Volatility

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Historical annualized return | 30.0% | 0.067 return fraction | 0.063 return fraction–0.069 return fraction | 0.557 | 0.0% |
| Historical daily ES95 loss | 40.0% | 0.011 loss fraction | 0.01 loss fraction–0.011 loss fraction | 0.894 | 0.0% |
| Historical maximum drawdown | 30.0% | -0.163 return fraction | -0.166 return fraction–-0.153 return fraction | 0.729 | 0.0% |

#### Equal Weight Benchmark

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Historical annualized return | 30.0% | 0.078 return fraction | 0.073 return fraction–0.079 return fraction | 0.592 | 0.0% |
| Historical daily ES95 loss | 40.0% | 0.013 loss fraction | 0.013 loss fraction–0.014 loss fraction | 0.870 | 0.0% |
| Historical maximum drawdown | 30.0% | -0.198 return fraction | -0.202 return fraction–-0.186 return fraction | 0.669 | 0.0% |

#### 60/40 Equity Treasury Benchmark

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Historical annualized return | 30.0% | 0.091 return fraction | 0.085 return fraction–0.093 return fraction | 0.636 | 0.0% |
| Historical daily ES95 loss | 40.0% | 0.017 loss fraction | 0.017 loss fraction–0.018 loss fraction | 0.826 | 0.0% |
| Historical maximum drawdown | 30.0% | -0.267 return fraction | -0.272 return fraction–-0.251 return fraction | 0.555 | 0.0% |

### Correlation sensitivity

| Dependence state | Modeled winner | Recommended option P(best) | CVaR10 | Breach U95 |
|---|---|---:|---:|---:|
| Independent residuals | Baseline: Walk Forward Inverse Volatility | 100.0% | 0.742 | 0.00% |
| Declared factor model | Baseline: Walk Forward Inverse Volatility | 100.0% | 0.742 | 0.00% |
| Loading stress ×1.35 | Baseline: Walk Forward Inverse Volatility | 100.0% | 0.742 | 0.00% |

### Parameter provenance and approval

Coverage: **48/48 parameters sourced** and **48/48 approved for the declared use**. Every expanded JSON path is recorded in `decision-results.json` under `parameter_provenance.records`.

| Source ID | Source type | Owner | Approved uses | Approval chain |
|---|---|---|---|---|
| `regime-aware-multi-asset-portfolio-analysis-output` | reproducible_project_output | Original publisher and repository analysis author | exploratory | 1. model_author (approved) |
| `portfolio-author-governance-assumptions` | analyst_judgment_not_externally_approved | Repository analysis author | exploratory | 1. self_review (approved) |
### Sources and reproducibility

- Yahoo Finance Chart API adjusted-price histories for SPY, TLT, VNQ, GLD, and BIL; reviewed fixed-period snapshot
- projects/regime-aware-multi-asset-portfolio/outputs/results.json
- Engine version: `7.0.0`
- Samples: `10000`
- Random seed: `20260726`
- Sampling design: Stratified scenario allocation with a declared latent-factor Gaussian copula, shared shocks across alternatives, marginal-preserving inverse transforms, and matched independent/correlation-stress counterfactuals.
- Case SHA-256: `adf70c0a59d902d671c813e364ddb8b605a2900f36d67d01046398ec09464534`

### Decision notes

- The comparison selects a candidate for further review, not an operational action.
- No institutional, clinical, financial, engineering, or policy approval is represented.

</details>

> Source-backed exploratory analysis, not an authorization to act. Domain review and current local evidence remain required.
