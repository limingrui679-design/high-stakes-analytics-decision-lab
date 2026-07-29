# Community Screening Resource Allocation

*Biostatistics, population health, public policy, and operations · 12 months · 10,000 modeled simulations*

## Executive Summary

- **Illustrative preference — Targeted hybrid.** It is the highest-ranked feasible option, with decision value score **57.9/100** and a modeled **95% probability of being best among decision-feasible alternatives**.
- **The lead is meaningful rather than absolute.** It leads the next feasible option, Expand fixed clinics, by **0.086 utility points**.
- **Modeled robustness is 91/100.** The option remains preferred in **100%** of two-sided weight stresses and **100%** of probability-weighted scenario comparisons.
- **Shared-shock sensitivity is explicit.** Relative to independent residuals, the declared factor model changes this option's P(best) by **+2.3%** and CVaR10 by **-0.011**; the ×1.35 loading stress does not change the modeled winner.
- **Constraint-breach evidence — 3.5% (355/10,000); U95 3.9%.** Feasibility uses the one-sided 95% upper bound against the **10.0% tolerance**; a zero event count is never presented as proof of zero real-world risk.
- **Decision status — Illustrative preference.** The current blockers are: evidence is not labeled for operational use.
- **Evidence boundary.** No causal claim; health gains are scenario inputs that would require trial or quasi-experimental evidence in a real deployment.
- **Parameter lineage.** 112/112 governed parameters have a resolved source and approval-chain reference.

![Decision summary](figures/decision-scorecard.svg)

**Decision owner:** Regional public health authority  
**Decision question:** Choose a 12-month screening-delivery strategy under a USD 10 million budget while improving access and limiting implementation risk.

## Decision status and modeled robustness

**Status: Illustrative preference.** 7 of 8 configured readiness checks pass. The robustness score summarizes model behavior; it is not a posterior probability that the real-world decision is correct and cannot upgrade illustrative evidence into operational evidence.

![Decision robustness profile](figures/robustness-profile.svg)

## Targeted hybrid leads on balanced value, not every dimension

**The preferred option earns its position through High- versus low-access gap, Expected health gain.** The comparison still exposes a trade-off on **Annual program cost**, so the decision should be presented as a transparent compromise rather than a universal optimum.

![Alternative ranking](figures/alternative-ranking.svg)

The ranking combines expected value with downside performance and excludes options whose one-sided 95% breach-frequency upper bound exceeds **10%**. Probability-best remains visible because a lower-ranked option may still win in a material share of simulations.

## The conservative risk boundary determines feasibility

**The decision rule compares the one-sided 95% breach-frequency upper bound—not only the observed simulation rate—with the 10.0% tolerance.** This makes finite-sample uncertainty visible and prevents a zero event count from being presented as proof of zero risk.

![Constraint risk boundary](figures/constraint-risk.svg)

The dark circle is the observed breach rate; the diamond is its conservative upper bound. An option fails the modeled feasibility rule when that diamond crosses the red tolerance line. The test is conditional on the declared distributions and cannot cover omitted real-world hazards.

## The criterion profile reveals where the preferred option earns—and gives up—value

Each cell below places an outcome on its declared worst-to-best reference scale. This avoids recalibrating the chart around whichever alternatives happen to be present.

![Criterion scorecard](figures/criterion-scorecard.svg)

**The decision is therefore driven by an explicit value model.** A stakeholder who places substantially more weight on Annual program cost may reasonably prefer another option; the two-sided weight-sensitivity section tests that possibility directly. The preferred option clips **0.0%** of criterion draws at the declared reference-scale bounds.

## Downside risk remains visible behind the average

**Targeted hybrid has expected utility 0.607, but its worst-decile average falls to 0.512.** The widest criterion-level uncertainty for this option is associated with **Expected health gain**, making it a priority for further evidence collection.

![Utility uncertainty and downside](figures/utility-uncertainty.svg)

The interval chart prevents a precise-looking average from obscuring overlap among alternatives. A close overlap means the practical decision may depend more on constraints, reversibility, and the cost of learning than on a small utility difference.

## Shared shocks change the uncertainty question

**The declared factor model gives Targeted hybrid P(best) 95%, versus 92% under independent residuals and 97% under the stronger correlation stress.** Its CVaR10 moves from 0.523 independently to 0.512 under declared dependence and 0.504 under stress.

![Correlation and tail-risk stress](figures/correlation-stress.svg)

The three states use matched seeds, stratified scenario counts, and the same marginal distributions. Differences therefore isolate the declared dependence structure as closely as this simulation design allows. The Gaussian copula remains an approximation: factor definitions, signs, and loadings must be replaced or approved using domain evidence.

## Scenario tests show when the preferred option is most exposed

**The weakest modeled environment is Clinical staff shortage, where the preferred option's risk-adjusted utility is 0.529.** The same feasible alternative remains ahead in every modeled scenario.

![Scenario performance](figures/scenario-performance.svg)

The preferred option leads in **100%** of the probability-weighted scenario comparison. Scenario probabilities are assumptions, not forecasts with guaranteed calibration. They are useful because they reveal which external conditions deserve monitoring and which contingency plans should be prepared before implementation.

## Distributional effects require a separate judgment

**Average utility does not establish equitable impact.** The weakest descriptive parity ratio is **0.86** for **access probability**, between Rural residents and Urban higher-income residents. The ratios below are descriptive diagnostics; they cannot resolve questions about rights, need, historical disadvantage, or acceptable error asymmetry.

![Group-impact parity overview](figures/group-impact.svg)

Use the visual to locate disparities that require subgroup analysis and stakeholder review. Do not optimize the ratios mechanically or treat similarity as proof of fairness.

## The result is stable to stakeholder priorities

**The baseline choice survives 100% of local weight stresses.** No single criterion emphasis changes the preferred feasible alternative.

![Weight sensitivity](figures/weight-sensitivity.svg)

This test both increases and decreases each criterion weight while preserving risk adjustment. It remains a local stress test rather than a substitute for formal stakeholder elicitation. If the winner changes under a plausible emphasis, the next step is deliberation and better evidence—not hiding the sensitivity.

## Recommended next steps

1. **Replace every synthetic input before any pilot or operational use.** Re-estimate outcomes from traceable descriptive, predictive, causal, financial, policy, or engineering evidence.
2. **Reduce uncertainty in Expected health gain.** Replace the widest synthetic or elicited input with experimental, quasi-experimental, observational, or engineering evidence appropriate to the domain.
3. **Monitor the Clinical staff shortage trigger.** Specify leading indicators and a contingency response before rollout.
4. **Review distributional impacts with affected stakeholders.** Examine absolute group outcomes alongside disparity measures and document unresolved normative choices.

## Further questions

- Which empirical or elicited evidence would best validate the declared factor loadings?
- Which omitted externality or stakeholder could materially alter the criterion set?
- What evidence would justify replacing the current scenario probabilities?
- Is the preferred option reversible if early monitoring contradicts the model?

## Caveats and assumptions

- **Evidence type:** Synthetic demonstration assumptions informed by a hypothetical needs assessment
- **Evidence as of:** Synthetic demonstration; no production as-of date
- **Permitted decision use:** illustrative
- **Causal status:** No causal claim; health gains are scenario inputs that would require trial or quasi-experimental evidence in a real deployment.
- **Dependence model:** latent_factor_gaussian_copula with 1 declared shared factor(s); the loading stress is ×1.35. Copula choice and loadings remain assumptions.
- **Parameter provenance:** 100% source coverage and 100% approval coverage for the declared decision use. Approval for illustrative use is not operational approval.
- **Zero-breach interpretation:** zero simulated events means either no event was observed in the finite run or the declared bounded input support excludes a breach. Neither statement establishes zero real-world risk.
- Health gains are aggregate and do not model disease-specific survival outcomes.
- Geographic travel times are summarized rather than optimized on a road network.
- The Gaussian copula and factor loadings are synthetic assumptions; tail dependence may differ in real data and requires domain approval.

<details>
<summary><strong>Detailed numerical appendix and reproducibility</strong></summary>

### Ranked alternatives

| Rank | Alternative | Feasible | Value score | Expected utility | CVaR10 | P(best feasible) | P(best all) | Breach evidence | Feasible Pareto |
|---:|---|:---:|---:|---:|---:|---:|---:|---|:---:|
| 1 | Targeted hybrid | Yes | 57.9 | 0.607 | 0.512 | 94.6% | 54.7% | 3.5% (355/10,000); U95 3.9% | Yes |
| 2 | Expand fixed clinics | Yes | 49.3 | 0.527 | 0.414 | 5.0% | 1.5% | 9.2% (916/10,000); U95 9.6% | Yes |
| 3 | Status quo | Yes | 48.8 | 0.506 | 0.446 | 0.4% | 0.1% | 0/10,000 observed; U95 0.03%; declared support excludes breach | Yes |
| 4 | Mobile-first network | No | 56.9 | 0.601 | 0.495 | n/a | 43.6% | 15.6% (1,564/10,000); U95 16.2% | No |

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

| Alternative | Constraint | Events | Observed | U95 | Declared support | Mean signed margin | P05–P95 margin |
|---|---|---:|---:|---:|---|---:|---:|
| Targeted hybrid | Annual budget ceiling | 355/10,000 | 3.5% | 3.87% | 7.8–10.6; tail crosses threshold | 0.995 | 0.088–1.821 |
| Targeted hybrid | Operational risk tolerance | 0/10,000 | 0.0% | 0.03% | 28–65; excludes breach | 20.928 | 9.030–31.815 |
| Expand fixed clinics | Annual budget ceiling | 831/10,000 | 8.3% | 8.78% | 7.2–11.2; tail crosses threshold | 1.112 | -0.201–2.248 |
| Expand fixed clinics | Operational risk tolerance | 135/10,000 | 1.4% | 1.55% | 30–71; tail crosses threshold | 17.222 | 4.211–28.960 |
| Status quo | Annual budget ceiling | 0/10,000 | 0.0% | 0.03% | 4.8–6.48; excludes breach | 4.470 | 3.907–4.970 |
| Status quo | Operational risk tolerance | 0/10,000 | 0.0% | 0.03% | 16–43; excludes breach | 37.651 | 28.600–45.561 |
| Mobile-first network | Annual budget ceiling | 750/10,000 | 7.5% | 7.94% | 7.5–10.9; tail crosses threshold | 0.929 | -0.159–1.963 |
| Mobile-first network | Operational risk tolerance | 1,057/10,000 | 10.6% | 11.09% | 36–77; tail crosses threshold | 10.222 | -3.185–22.808 |

### Criterion outcomes

#### Targeted hybrid

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Expected health gain | 32.0% | 648.7 QALY-equivalent points | 512.3 QALY-equivalent points–788.1 QALY-equivalent points | 0.665 | 0.2% |
| Annual program cost | 18.0% | 9.005 USD millions | 8.179 USD millions–9.912 USD millions | 0.374 | 0.0% |
| High- versus low-access gap | 20.0% | 0.11 probability points | 0.075 probability points–0.15 probability points | 0.686 | 0.0% |
| Implementation risk | 15.0% | 44.1 index points | 33.2 index points–56.0 index points | 0.513 | 0.0% |
| Evidence quality | 15.0% | 0.79 score | 0.79 score–0.79 score | 0.754 | 0.0% |

#### Expand fixed clinics

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Expected health gain | 32.0% | 577.8 QALY-equivalent points | 419.5 QALY-equivalent points–731.0 QALY-equivalent points | 0.570 | 0.0% |
| Annual program cost | 18.0% | 8.888 USD millions | 7.752 USD millions–10.2 USD millions | 0.389 | 0.0% |
| High- versus low-access gap | 20.0% | 0.177 probability points | 0.137 probability points–0.22 probability points | 0.494 | 0.0% |
| Implementation risk | 15.0% | 47.8 index points | 36.0 index points–60.8 index points | 0.460 | 0.0% |
| Evidence quality | 15.0% | 0.76 score | 0.76 score–0.76 score | 0.708 | 0.0% |

#### Status quo

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Expected health gain | 32.0% | 345.5 QALY-equivalent points | 281.6 QALY-equivalent points–411.8 QALY-equivalent points | 0.261 | 0.0% |
| Annual program cost | 18.0% | 5.53 USD millions | 5.03 USD millions–6.093 USD millions | 0.809 | 0.0% |
| High- versus low-access gap | 20.0% | 0.273 probability points | 0.236 probability points–0.312 probability points | 0.219 | 0.0% |
| Implementation risk | 15.0% | 27.3 index points | 19.4 index points–36.4 index points | 0.752 | 0.0% |
| Evidence quality | 15.0% | 0.82 score | 0.82 score–0.82 score | 0.800 | 0.0% |

#### Mobile-first network

| Criterion | Weight | Mean | P05–P95 | Normalized score | Scale clipping |
|---|---:|---:|---:|---:|---:|
| Expected health gain | 32.0% | 701.2 QALY-equivalent points | 542.9 QALY-equivalent points–895.8 QALY-equivalent points | 0.732 | 4.8% |
| Annual program cost | 18.0% | 9.071 USD millions | 8.037 USD millions–10.2 USD millions | 0.366 | 0.0% |
| High- versus low-access gap | 20.0% | 0.08 probability points | 0.045 probability points–0.121 probability points | 0.771 | 0.0% |
| Implementation risk | 15.0% | 54.8 index points | 42.2 index points–68.2 index points | 0.360 | 0.0% |
| Evidence quality | 15.0% | 0.7 score | 0.7 score–0.7 score | 0.615 | 0.0% |

### Correlation sensitivity

| Dependence state | Modeled winner | Recommended option P(best) | CVaR10 | Breach U95 |
|---|---|---:|---:|---:|
| Independent residuals | Targeted hybrid | 92.3% | 0.523 | 3.92% |
| Declared factor model | Targeted hybrid | 94.6% | 0.512 | 3.87% |
| Loading stress ×1.35 | Targeted hybrid | 96.8% | 0.504 | 4.11% |

### Parameter provenance and approval

Coverage: **112/112 parameters sourced** and **112/112 approved for the declared use**. Every expanded JSON path is recorded in `decision-results.json` under `parameter_provenance.records`.

| Source ID | Source type | Owner | Approved uses | Approval chain |
|---|---|---|---|---|
| `health-resource-allocation-synthetic-parameter-register` | synthetic_demonstration_register | Repository maintainer (synthetic example) | illustrative | 1. case_author (approved) → 2. independent_domain_reviewer (not_obtained) |
### Sources and reproducibility

- Synthetic demand forecast by district
- Illustrative expert elicitation on capacity and implementation risk
- Engine version: `5.0.0`
- Samples: `10000`
- Random seed: `20260726`
- Sampling design: Stratified scenario allocation with a declared latent-factor Gaussian copula, shared shocks across alternatives, marginal-preserving inverse transforms, and matched independent/correlation-stress counterfactuals.
- Case SHA-256: `7c04a08608fe9a60863ad6684f25e4caa1d4fc7f4d3e8f6b72c07a4e6cd75905`

### Decision notes

- A real analysis should estimate health outcomes by condition and validate transportability across districts.
- The authority should pre-register an evaluation plan before rollout.

</details>

> Synthetic demonstration only. This report is not medical, financial, legal, engineering-safety, or public-policy advice.
