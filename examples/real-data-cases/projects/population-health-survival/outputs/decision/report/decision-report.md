# Which follow-up triage rule should advance to prospective clinical validation

*Population health and biostatistics · Prospective pilot design; no clinical deployment · 3,000 modeled simulations*

## Executive Summary

- **Provisional preference — Top 20% Review.** It is the highest-ranked feasible option, with decision value score **76.3/100** and a modeled **25% probability of being best among decision-feasible alternatives**.
- **The lead is narrow rather than absolute.** It leads the next feasible option, Top 30% Review, by **0.002 utility points**.
- **Modeled robustness is 46/100.** The option remains preferred in **50%** of two-sided weight stresses and **25%** of probability-weighted scenario comparisons.
- **Shared-shock sensitivity is explicit.** Relative to independent residuals, the declared factor model changes this option's P(best) by **+0.0%** and CVaR10 by **+0.000**; the ×1.35 loading stress does not change the modeled winner.
- **Constraint-breach evidence — 0/3,000 observed; U95 0.00%; declared support excludes breach.** Feasibility uses the one-sided 95% upper bound against the **10.0% tolerance**; a zero event count is never presented as proof of zero real-world risk.
- **Decision status — Provisional—validate before action.** The current blockers are: modeled preference separation is below threshold; the winner is sensitive to criterion weights; the winner changes across material scenarios; evidence is not labeled for operational use.
- **Evidence boundary.** No causal claim unless explicitly identified in the source design; the decision comparison is exploratory.
- **Parameter lineage.** 48/48 governed parameters have a resolved source and approval-chain reference.

![Decision summary](figures/decision-scorecard.svg)

**Decision owner:** Hypothetical domain review panel; no real owner authorization
**Decision question:** Which follow-up triage rule should advance to prospective clinical validation?

## Decision status and modeled robustness

**Status: Provisional—validate before action.** 4 of 8 configured readiness checks pass. The robustness score summarizes model behavior; it is not a posterior probability that the real-world decision is correct and cannot upgrade illustrative evidence into operational evidence.

![Decision robustness profile](figures/robustness-profile.svg)

## Top 20% Review leads on balanced value, not every dimension

**The preferred option earns its position through Follow-up workload, Recorded-sex selection gap.** The comparison still exposes a trade-off on **Observed event capture**, so the decision should be presented as a transparent compromise rather than a universal optimum.

![Alternative ranking](figures/alternative-ranking.svg)

The ranking combines expected value with downside performance and excludes options whose one-sided 95% breach-frequency upper bound exceeds **10%**. Probability-best remains visible because a lower-ranked option may still win in a material share of simulations.

## The conservative risk boundary determines feasibility

**The decision rule compares the one-sided 95% breach-frequency upper bound—not only the observed simulation rate—with the 10.0% tolerance.** This makes finite-sample uncertainty visible and prevents a zero event count from being presented as proof of zero risk.

![Constraint risk boundary](figures/constraint-risk.svg)

The dark circle is the observed breach rate; the diamond is its conservative upper bound. An option fails the modeled feasibility rule when that diamond crosses the red tolerance line. The test is conditional on the declared distributions and cannot cover omitted real-world hazards.

## The criterion profile reveals where the preferred option earns—and gives up—value

Each cell below places an outcome on its declared worst-to-best reference scale. This avoids recalibrating the chart around whichever alternatives happen to be present.

![Criterion scorecard](figures/criterion-scorecard.svg)

**The decision is therefore driven by an explicit value model.** A stakeholder who places substantially more weight on Observed event capture may reasonably prefer another option; the two-sided weight-sensitivity section tests that possibility directly. The preferred option clips **0.0%** of criterion draws at the declared reference-scale bounds.

## Downside risk remains visible behind the average

**Top 20% Review has expected utility 0.768, but its worst-decile average falls to 0.748.** The widest criterion-level uncertainty for this option is associated with **Observed event capture**, making it a priority for further evidence collection.

![Utility uncertainty and downside](figures/utility-uncertainty.svg)

The interval chart prevents a precise-looking average from obscuring overlap among alternatives. A close overlap means the practical decision may depend more on constraints, reversibility, and the cost of learning than on a small utility difference.

## Shared shocks change the uncertainty question

**The declared factor model gives Top 20% Review P(best) 25%, versus 25% under independent residuals and 25% under the stronger correlation stress.** Its CVaR10 moves from 0.748 independently to 0.748 under declared dependence and 0.748 under stress.

![Correlation and tail-risk stress](figures/correlation-stress.svg)

The three states use matched seeds, stratified scenario counts, and the same marginal distributions. Differences therefore isolate the declared dependence structure as closely as this simulation design allows. The Gaussian copula remains an approximation: factor definitions, signs, and loadings must be replaced or approved using domain evidence.

## Scenario tests show when the preferred option is most exposed

**The weakest modeled environment is Adverse transfer to a new setting, where the preferred option's risk-adjusted utility is 0.748.** At least one scenario changes the leading feasible alternative: Observed evidence base favors Top 30% Review.

![Scenario performance](figures/scenario-performance.svg)

The preferred option leads in **25%** of the probability-weighted scenario comparison. Scenario probabilities are assumptions, not forecasts with guaranteed calibration. They are useful because they reveal which external conditions deserve monitoring and which contingency plans should be prepared before implementation.

## Distributional effects remain an evidence gap

**No group-level outcomes were supplied for this case.** Before operational use, the analysis should add affected groups, absolute outcomes, disparity measures, and a qualitative review of harms that cannot be reduced to a numeric parity ratio.

## The result is sensitive to stakeholder priorities

**The baseline choice survives 50% of local weight stresses.** The following weight perturbation changes the winner: ↑ Observed event capture → Top 30% Review; ↓ Follow-up workload → Top 30% Review; ↓ Recorded-sex selection gap → Top 30% Review.

![Weight sensitivity](figures/weight-sensitivity.svg)

This test both increases and decreases each criterion weight while preserving risk adjustment. It remains a local stress test rather than a substitute for formal stakeholder elicitation. If the winner changes under a plausible emphasis, the next step is deliberation and better evidence—not hiding the sensitivity.

## Recommended next steps

1. **Resolve the failed readiness checks before acting.** modeled preference separation is below threshold; the winner is sensitive to criterion weights; the winner changes across material scenarios; evidence is not labeled for operational use.
2. **Reduce uncertainty in Observed event capture.** Validate or replace the widest uncertainty input using experimental, quasi-experimental, observational, or engineering evidence appropriate to the domain.
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
- Public linked mortality is observational and uses public-use linkage fields; the simple score is not a diagnostic model and variance estimates do not replace a full complex-survey analysis.
- Weights, scales, scenarios, and correlation loadings are analyst judgments without external approval.

<details>
<summary><strong>Detailed numerical appendix and reproducibility</strong></summary>

### Ranked alternatives

| Rank | Alternative | Feasible | Value score | Expected utility | CVaR10 | P(best feasible) | P(best all) | Breach evidence | Feasible Pareto |
|---:|---|:---:|---:|---:|---:|---:|---:|---|:---:|
| 1 | Top 20% Review | Yes | 76.3 | 0.768 | 0.748 | 25.0% | 25.0% | 0/3,000 observed; U95 0.00%; declared support excludes breach | Yes |
| 2 | Top 30% Review | Yes | 76.1 | 0.767 | 0.742 | 75.0% | 75.0% | 0/3,000 observed; U95 0.00%; declared support excludes breach | Yes |
| 3 | Baseline: Top 10% Review | Yes | 70.3 | 0.706 | 0.692 | 0.0% | 0.0% | 0/3,000 observed; U95 0.00%; declared support excludes breach | Yes |

### Readiness checks

| Check | Result |
|---|:---:|
| Feasible Alternative | Pass |
| Probability Best | Fail |
| Weight Stability | Fail |
| Scenario Stability | Fail |
| Scale Clipping | Pass |
| Parameter Provenance | Pass |
| Approval Scope | Pass |
| Operational Evidence | Fail |

### Constraint diagnostics

No hard constraints were supplied.

### Criterion outcomes

#### Top 20% Review

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Observed event capture | 45.0% | 0.625 share | 0.586 share–0.637 share | 0.625 | 0.0% |
| Follow-up workload | 30.0% | 0.204 share | 0.2 share–0.216 share | 0.796 | 0.0% |
| Recorded-sex selection gap | 25.0% | 0.003 absolute share | 0.003 absolute share–0.003 absolute share | 0.994 | 0.0% |

#### Top 30% Review

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Observed event capture | 45.0% | 0.708 share | 0.665 share–0.723 share | 0.708 | 0.0% |
| Follow-up workload | 30.0% | 0.306 share | 0.3 share–0.324 share | 0.694 | 0.0% |
| Recorded-sex selection gap | 25.0% | 0.019 absolute share | 0.019 absolute share–0.02 absolute share | 0.962 | 0.0% |

#### Baseline: Top 10% Review

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Observed event capture | 45.0% | 0.429 share | 0.402 share–0.437 share | 0.429 | 0.0% |
| Follow-up workload | 30.0% | 0.102 share | 0.1 share–0.108 share | 0.898 | 0.0% |
| Recorded-sex selection gap | 25.0% | 0.012 absolute share | 0.012 absolute share–0.013 absolute share | 0.976 | 0.0% |

### Correlation sensitivity

| Dependence state | Modeled winner | Recommended option P(best) | CVaR10 | Breach U95 |
|---|---|---:|---:|---:|
| Independent residuals | Top 20% Review | 25.0% | 0.748 | 0.00% |
| Declared factor model | Top 20% Review | 25.0% | 0.748 | 0.00% |
| Loading stress ×1.35 | Top 20% Review | 25.0% | 0.748 | 0.00% |

### Parameter provenance and approval

Coverage: **48/48 parameters sourced** and **48/48 approved for the declared use**. Every expanded JSON path is recorded in `decision-results.json` under `parameter_provenance.records`.

| Source ID | Source type | Owner | Approved uses | Approval chain |
|---|---|---|---|---|
| `population-health-survival-analysis-output` | reproducible_project_output | Original publisher and repository analysis author | exploratory | 1. model_author (approved) |
| `portfolio-author-governance-assumptions` | analyst_judgment_not_externally_approved | Repository analysis author | exploratory | 1. self_review (approved) |
### Sources and reproducibility

- U.S. Centers for Disease Control and Prevention, National Center for Health Statistics. NHIS 2016 and 2017 Sample Adult files linked to 2019 public-use mortality.
- projects/population-health-survival/outputs/results.json
- Engine version: `7.0.0`
- Samples: `3000`
- Random seed: `20260810`
- Sampling design: Stratified scenario allocation with a declared latent-factor Gaussian copula, shared shocks across alternatives, marginal-preserving inverse transforms, and matched independent/correlation-stress counterfactuals.
- Case SHA-256: `8526fe9a41beeb246509a268cb305e8dc6a5c3f4c4dc2ff3e810e2b858277a18`

### Decision notes

- The comparison selects a candidate for further review, not an operational action.
- No institutional, clinical, financial, engineering, or policy approval is represented.

</details>

> Source-backed exploratory analysis, not an authorization to act. Domain review and current local evidence remain required.
