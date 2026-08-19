# Adaptive Method Routing

Select methods from the question, evidence structure, and decision maturity.
Do not begin with a preferred report format or force every case through the
decision engine.

## Routing sequence

1. Identify the decision owner, analytical question, outcome, observation
   unit, time horizon, and permitted use.
2. When row-level data are supplied, run the data-quality gate and stop on
   `blocked` or unresolved `needs_user_confirmation`.
3. Choose the minimum required lens: descriptive, diagnostic, predictive, or
   prescriptive.
4. Match the data grain and estimand to one primary method family.
5. Add a second method only when it answers a distinct supporting question.
6. Choose output fields and figures after selecting the method.
7. Stop when the evidence gate for the next lens is not met.

## Method selection

| Question and evidence pattern | Primary route | Minimum case-specific output |
|---|---|---|
| Status, trend, distribution, cohort, funnel, or segment question | Descriptive baseline | Population, unit, window, metric, denominator, missingness, comparison, and source |
| “Why did this change?” without an identification strategy | Descriptive + diagnostic | Contribution or process decomposition, alternative hypotheses, tests needed, and non-causal boundary |
| Two-group binary or continuous outcome | Evidence analysis | Group definition, estimand, effect contrast, uncertainty interval, missingness, and assignment boundary |
| Time-to-event outcome with censoring | Survival evidence | Time origin, event, censoring rule, risk set, horizon, survival estimate, and proportional-hazards boundary if modeled |
| Held-out binary scores | Prediction validation | Target, horizon, split, baseline, AUC, Brier, calibration, threshold metrics, subgroup errors, drift, and deployment gate |
| Rare event under fixed review capacity | Prediction + operational validation | Cumulative gain, lift against random review, uncertainty interval, capacity constraint, and negative-result rule |
| Forecast feeding a resource decision | Forecast + allocation | Forecast horizon, time split, error distribution, decision variables, constraints, feasible set, and value-of-information boundary |
| Small discretized resource-allocation problem | Allocation optimizer | Variables, bounds, step sizes, objective, constraints, scenarios, regret, and grid-optimality boundary |
| Multiple feasible alternatives under material common shocks | Decision engine | Owner, alternatives, criteria, weights, constraints, shared factors, tail risk, P(best), sensitivity, and reversal conditions |
| Financial or operational panel comparison | Descriptive panel + scenario stress | Entity/time grain, comparability, common-size metrics, peer benchmark, persistence, stress definition, and follow-up diligence |
| Public inventory or disclosure file | Measurement-readiness analysis | Full field taxonomy, nonblank definition, completeness by family, unavailable fields, evidence request, and capability boundary |
| Spatial need and facility decision | Spatial analysis + allocation | Geographic unit, adjacency or distance, uncertainty, need measure, candidate sites, coverage radius, sensitivity, and aggregation boundary |

Use `scripts/profile_dataset.py` and `scripts/prepare_dataset.py` before the
analytical modules when row-level data are uploaded. Use
`scripts/evidence_analysis.py`, `scripts/prediction_validation.py`, and
`scripts/allocation_optimizer.py` only for the supported executable patterns.
Use `scripts/run_case.py` after the quality gate, alternatives, and decision
inputs are defensible.
For unsupported complex estimation, specify the required specialist method and
its output contract instead of substituting a simpler calculation.

## Dynamic output rule

All outputs share a common evidence spine:

- question and scope;
- data and source lineage;
- data-quality status;
- supported findings;
- limitations and claim boundary;
- next action.

Everything else is route-specific. A descriptive case should not contain empty
model-validation sections. A weak prediction should add a deployment gate and
may terminate with `do_not_deploy`. A disclosure analysis should request
missing evidence rather than score unobserved capability. A prescriptive case
should add decision fields only after prediction and feasibility gates pass.

## Transfer boundary

Reuse method contracts, not conclusions. Never carry over thresholds, weights,
subgroup definitions, causal wording, or operational recommendations without
source-specific review.

For complete worked implementations, use the
[real-data case index](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases). Select the case
by analytical pattern and evidence boundary, then inspect its full report,
source manifest, code, results, and figures before adapting the method.
