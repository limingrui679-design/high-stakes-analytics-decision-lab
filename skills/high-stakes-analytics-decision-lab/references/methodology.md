# Methodology

## Purpose

Use the engine as a transparent decision layer after the relevant statistical, causal, predictive, financial, engineering, or policy analysis. It compares explicit alternatives; it does not discover causal effects from raw observational data.

## Value model

For criterion \(j\), transform an outcome \(x_j\) to a bounded value \(v_j\) between 0 and 1 using a user-specified worst and best reference point.

- Maximize: `v = (x - worst) / (best - worst)`
- Minimize: `v = (worst - x) / (worst - best)`

Clamp values to `[0, 1]`. Normalize nonnegative weights to sum to one, then calculate additive utility:

`U = sum(weight_j * value_j)`

An additive model assumes preferential independence. If interactions are material—for example, a safety threshold below which all economic benefit becomes irrelevant—represent them as hard constraints or extend the engine rather than hiding the interaction in weights.

## Uncertainty and correlated shocks

The engine draws one common scenario and one vector of shared latent-factor
shocks per Monte Carlo iteration. Every alternative is evaluated against that
same modeled world. This alignment is essential for interpreting
probability-of-best as a paired comparison rather than a comparison of
unrelated simulations.

Supported input distributions:

- `fixed`: known or intentionally held constant;
- `normal`: symmetric uncertainty, optionally truncated;
- `uniform`: only defensible lower and upper bounds are known;
- `triangular`: lower, most likely, and upper estimates are available.

Dependence uses a latent-factor Gaussian copula. For criterion \(j\), define:

`z_j = sum(loading_jk × factor_k) + sqrt(1 - sum(loading_jk²)) × residual_j`

Map `z_j` through the standard-normal CDF and the inverse CDF of the declared
marginal distribution. This preserves fixed, normal, uniform, and triangular
marginals while allowing signed shared shocks across criteria and alternatives.
Squared loadings must sum to less than one.

Every run includes three matched dependence states:

1. an independent-residual baseline with loadings set to zero;
2. the declared factor model;
3. a stronger-dependence stress using the declared loading multiplier.

Recompute P(best), CVaR10, breach U95, feasibility, ranking, and the preferred
option in every state. Do not infer the effect of correlation from a variance
formula alone. The Gaussian copula has no special lower- or upper-tail
dependence, so domain evidence may justify another dependence model.

Scenario draws use stratified allocation: each positive-probability scenario
receives at least one draw and the full sample approximates the declared
scenario probabilities. Matched seeds and sampling order support controlled
comparison of the three dependence states.

## Parameter provenance and approval

The case file contains a parameter governance registry. It maps each parameter
family to a traceable source with:

- citation, source type, as-of date, and owner;
- permitted decision uses;
- an ordered approval chain with role, actor, status, date, and scope.

The engine expands those rules into an individual record for every criterion
weight and scale value, distribution field, scenario probability and
adjustment, constraint threshold, risk parameter, weight stress, factor
loading, and correlation stress parameter. Both source coverage and approval
coverage must be complete for the declared use. Approval for an illustrative
demonstration is not approval for exploratory or operational use.

## Risk

For each alternative:

- expected utility summarizes average modeled value;
- P05 and P95 describe simulation uncertainty;
- CVaR10 is the average utility in the worst 10% of iterations;
- risk-adjusted utility equals expected utility minus risk aversion times the gap between expected utility and CVaR10.

Risk aversion is a value judgment. Show the unadjusted and adjusted result.
The reader-facing `value_score` equals risk-adjusted utility multiplied by 100;
it is a value-model score, not a probability or observed performance metric.

## Constraints

A hard constraint is evaluated in every iteration. The engine reports the
observed breach count and rate, then calculates a one-sided 95% upper bound for
the breach frequency. For zero observed events the exact upper bound is:

`1 - 0.05 ** (1 / samples)`

For nonzero counts, the engine uses the one-sided Wilson upper bound. An
alternative is decision-feasible when this conservative upper bound does not
exceed `max_constraint_violation_rate`.

The engine also propagates the declared distribution support through every
scenario adjustment. It labels each constraint:

- `declared_support_excludes_breach` when no value permitted by the input
  bounds can cross the threshold;
- `modeled_tail_crosses_threshold` when a bounded tail can cross it;
- `unbounded_tail` when a declared tail is unbounded.

Report the aggregate estimate and each constraint's event count, observed rate,
upper bound, support range, mean signed margin, and P05–P95 margin. A
bounded-support zero describes the model specification, not real-world
impossibility. Feasibility is evaluated before ranking.

Do not encode soft preferences as constraints merely to force a preferred answer.

## Pareto efficiency

An alternative is Pareto dominated when another alternative is at least as good on every expected criterion and strictly better on at least one. Pareto efficiency does not identify a unique recommendation; it only removes clearly inferior choices under the specified criteria.

## Weight sensitivity

The engine decreases and increases one criterion weight at a time using the
configured multiplier and its reciprocal, then renormalizes all weights.
Every stressed ranking is recomputed from the simulation draws using the same
expected-utility, CVaR10, and risk-aversion formula as the baseline ranking.
Report which alternative wins in each run. This is a local stress test, not a
substitute for structured stakeholder elicitation.

## Probability of being best

`probability_best` is the Monte Carlo win share among alternatives that pass
the ex-ante feasibility rule. It is not a posterior probability that the
decision is correct. The engine also preserves
`probability_best_unconstrained`, which compares all alternatives and reveals
whether an attractive but infeasible option drives the unconstrained result.

## Scenario stability

Within each scenario, compare feasible alternatives using scenario-specific
risk-adjusted utility. Probability-weighted scenario stability is the total
declared scenario probability for which the baseline preferred option remains
the winner, with ties split equally.

## Robustness and decision status

The robustness score is:

`100 × (0.30 × P(best) + 0.25 × weight stability + 0.25 × scenario stability + 0.20 × constraint headroom)`

Constraint headroom measures how far the preferred option's aggregate
one-sided 95% breach upper bound sits below the allowed breach rate. The
formula is deliberately visible and must not be described as confidence that
the decision is correct.

Decision status is separate:

- `illustrative_preference`: a modeled preference based on illustrative evidence;
- `provisional`: real exploratory or operational evidence with at least one failed readiness check;
- `decision_ready`: operational evidence and every configured readiness check passes;
- `no_feasible_option`: no alternative passes the feasibility rule.

Numerical robustness cannot upgrade illustrative evidence into an operational
recommendation.

## Scale diagnostics

Normalization uses fixed worst-to-best reference scales and bounds value at
zero and one. Report the pre-bounding scale-clipping rate for each criterion.
Frequent clipping indicates that reference scales may be poorly calibrated or
that scenarios extend beyond the intended value range.

## Group impacts

Group metrics are summarized using:

- absolute gap: maximum minus minimum group value;
- parity ratio: minimum divided by maximum group value.

The direction of fairness is domain-specific. A small gap in benefit or access may be desirable, while equal error rates can conflict with other fairness goals. Treat these metrics as prompts for sociotechnical review, not proof of justice.

## Evidence hierarchy

Keep the following distinct:

1. Descriptive evidence says what was observed.
2. Predictive evidence estimates what is likely.
3. Causal evidence estimates what would change under an intervention.
4. Decision analysis combines evidence with choices, constraints, uncertainty, and values.

When causal estimates matter, document identification assumptions, estimand, population, uncertainty interval, and robustness checks outside the decision engine and pass the resulting estimate into the case file.
