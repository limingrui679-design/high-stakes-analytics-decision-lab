# Advanced Method Boundaries

Use methods because the design requires them, not because a column permits them.

## Survival analysis

- Define time zero, event, censoring, horizon, cohort flow, and estimand.
- Kaplan–Meier estimates describe observed survival under independent-censoring
  assumptions.
- A Cox model requires convergence checks, coefficient uncertainty, an
  interpretable tie method, discrimination, calibration, and a
  proportional-hazards diagnostic.
- A predictive hazard association is not a treatment effect.

## Repeated measures and experiments

- Preserve participant or unit pairing.
- Use paired estimands and resampling that retains the pair.
- Report counterbalancing, order effects, attrition, noncompliance, spillover,
  multiplicity, and a design-sensitivity or detectable-effect calculation.
- Observed group status is not randomized treatment.

## Prediction

- Validate labels as binary, scores as finite and bounded, bins as sensible,
  thresholds in range, and time fields with reliable chronological ordering.
- Keep model selection, calibration, threshold selection, and final evaluation
  on separate data.
- Compare a simple baseline; report discrimination, calibration, confusion
  metrics, subgroup performance, drift, and abnormal-input behavior.
- A fixed threshold that predicts no positives can be an honest result. Do not
  replace it silently; use ranked capacity only when that matches the decision.

## Operations and systems

- Define decision variables, objective, constraints, units, and system boundary.
- For a small finite feasible set, enumerate it and report the count.
- Evaluate out of time; show binding constraints, Pareto trade-offs, local
  shadow-value sensitivity, and a perfect-information or regret boundary.
- Forecast improvement does not imply operational feasibility.

## Financial risk

- Separate observed yields or prices from the return approximation.
- Report empirical tails, VaR, expected shortfall, drawdown, coverage, and
  exceedance independence.
- Preserve temporal dependence with dated shared shocks or block resampling;
  stress block length and historical regimes.
- State omitted convexity, liquidity, financing, tax, cost, and implementability.

## Spatial analysis

- State geography, coordinate reference system, neighbor definition, and
  distance approximation.
- Report measurement error, missing geographies, spatial autocorrelation,
  radius and value-weight sensitivity, and an aggregation or MAUP check.
- Centroid distance is not travel time; candidate coverage is not a siting
  authorization.

## Responsible AI and policy

- Separate model performance, deployment process, organizational control, and
  normative legitimacy.
- Use sensitive fields for error analysis only when justified.
- Public reporting completeness is not proof that a control exists or is absent.
- No benchmark score authorizes consequential deployment.
