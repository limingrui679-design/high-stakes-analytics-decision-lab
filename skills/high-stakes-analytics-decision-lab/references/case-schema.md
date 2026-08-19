# Case Schema

## Top-level fields

| Field | Required | Meaning |
|---|---:|---|
| `schema_version` | yes | Use `"1.3"` for new cases. Version 1.2 remains readable only for fixture migration. |
| `case_id` | yes | Lowercase, hyphenated stable identifier. |
| `title` | yes | Reader-facing case title. |
| `domain` | yes | Domain or cross-domain context. |
| `decision_owner` | yes | Person or institution authorized to decide. |
| `decision_question` | yes | Concrete choice and time horizon. |
| `time_horizon` | yes | Human-readable evaluation window. |
| `evidence` | yes | Provenance, evidence type, causal status, limitations. |
| `criteria` | yes | Three or more evaluation criteria. |
| `alternatives` | yes | Two or more options, including a credible baseline. |
| `scenarios` | yes | Probabilities must sum to one within tolerance. |
| `uncertainty_model` | yes | Shared latent factors, signed criterion loadings, and correlation-stress multiplier. |
| `parameter_governance` | yes | Parameter-family sources, permitted uses, and ordered approval chains. |
| `constraints` | no | Hard decision constraints. |
| `risk_aversion` | no | Nonnegative tail-risk penalty; default `0.25`. |
| `max_constraint_violation_rate` | no | Allowed breach probability; default `0.10`. |
| `sensitivity_weight_multiplier` | no | Local weight stress; default `1.5`. |
| `readiness_thresholds` | no | Thresholds for preference separation, weight stability, scenario stability, and scale clipping. |
| `decision_notes` | no | Material context not captured elsewhere. |

## Evidence

```json
{
  "type": "observational cohort and analyst decision assumptions",
  "decision_use": "exploratory",
  "as_of": "2026-07-27",
  "sources": ["Source manifest, results file, and parameter register"],
  "causal_claim_status": "Association and prediction only; no treatment effect.",
  "limitations": ["Most decision-relevant limitation"]
}
```

`decision_use` must be:

- `illustrative` for synthetic demonstrations and teaching examples;
- `exploratory` for real but incomplete evidence that is not ready to authorize action;
- `operational` only when the evidence owner permits decision use.

The engine never upgrades illustrative or exploratory evidence to
decision-ready merely because the model is numerically stable.

## Correlated uncertainty model

```json
{
  "method": "latent_factor_gaussian_copula",
  "stress_multiplier": 1.35,
  "factors": [
    {
      "id": "systemic-adverse-shock",
      "label": "Systemic adverse demand and delivery shock",
      "description": "Shared shock across criteria and alternatives.",
      "loadings": {
        "net_benefit": -0.48,
        "cost": 0.48
      }
    }
  ]
}
```

A positive latent value moves a raw metric toward its upper quantiles. Use the
loading sign to represent the substantive direction of the shared shock.
Loadings can differ by criterion, and every factor is shared across
alternatives. For each criterion, the sum of squared loadings must be below one
both before and after applying `stress_multiplier`.

The engine runs independent, declared, and stronger-correlation states with
matched seeds. It recomputes P(best), CVaR10, breach U95, feasibility, and
ranking in every state.

## Parameter governance

```json
{
  "sources": [
    {
      "id": "case-parameter-register",
      "citation": "Traceable parameter register or elicitation record",
      "source_type": "expert_elicitation",
      "as_of": "2026-07-27",
      "owner": "Named evidence owner",
      "approved_decision_uses": ["exploratory"],
      "approval_chain": [
        {
          "sequence": 1,
          "role": "model_author",
          "actor": "Named analyst or accountable team",
          "status": "approved",
          "date": "2026-07-27",
          "scope": "Exploratory comparison"
        }
      ]
    }
  ],
  "rules": [
    {
      "parameter_type": "criterion_weight",
      "source_id": "case-parameter-register"
    }
  ]
}
```

Declare exactly one rule for each parameter type:

- `criterion_weight`
- `criterion_scale`
- `metric_distribution`
- `scenario_probability`
- `scenario_adjustment`
- `constraint_threshold`
- `risk_aversion`
- `maximum_violation_rate`
- `weight_sensitivity`
- `correlation_loading`
- `correlation_stress`

The engine resolves these rules to every individual JSON parameter path and
stores the expanded records in `parameter_provenance.records`. The underlying
parameter register must identify each parameter path, source fact, transformation,
units, uncertainty type, owner, reviewer, review date, approval status, scope,
and evidence strength. A source must explicitly approve the declared
`evidence.decision_use`; an illustrative approval cannot authorize exploratory
or operational use.

## Readiness thresholds

```json
{
  "minimum_probability_best": 0.5,
  "minimum_weight_stability": 0.75,
  "minimum_scenario_stability": 0.75,
  "maximum_scale_clipping_rate": 0.05
}
```

All values must be between zero and one. These are governance thresholds, not
empirical facts. Record why they are suitable for the decision.

## Criterion

```json
{
  "id": "net_benefit",
  "label": "Net benefit",
  "direction": "maximize",
  "weight": 0.35,
  "unit": "USD millions",
  "scale": {"worst": -5, "best": 20}
}
```

For `maximize`, require `best > worst`. For `minimize`, require `best < worst`.

## Alternative metric

Fixed:

```json
{"distribution": "fixed", "value": 12.5, "uncertainty_type": "none"}
```

Normal:

```json
{"distribution": "normal", "mean": 12.5, "sd": 2.0, "min": 0, "max": 20, "uncertainty_type": "parameter"}
```

Uniform:

```json
{"distribution": "uniform", "low": 8, "high": 15, "uncertainty_type": "scenario"}
```

Triangular:

```json
{"distribution": "triangular", "low": 8, "mode": 12, "high": 18, "uncertainty_type": "parameter"}
```

Empirical:

```json
{"distribution": "empirical", "values": [8.2, 9.1, 10.4, 12.0], "uncertainty_type": "process"}
```

Bootstrap:

```json
{"distribution": "bootstrap", "values": [0.22, 0.19, 0.31, 0.27], "uncertainty_type": "parameter"}
```

Schema 1.3 requires `uncertainty_type` for every alternative metric. Allowed
values are `none`, `parameter`, `process`, and `scenario`. A fixed distribution
must use `none`.

## Scenario

```json
{
  "id": "high-demand",
  "label": "High demand",
  "probability": 0.3,
  "adjustments": {
    "*": {
      "cost": {"multiply": 1.08}
    },
    "mobile-service": {
      "benefit": {"multiply": 1.15},
      "cost": {"add": 0.5}
    }
  }
}
```

Apply wildcard adjustments first and alternative-specific adjustments second. Each adjustment may contain `multiply` and/or `add`.

## Constraint

```json
{
  "criterion": "cost",
  "operator": "<=",
  "threshold": 10,
  "label": "Annual budget"
}
```

Supported operators: `<=`, `<`, `>=`, `>`.

## Group impacts

```json
{
  "groups": [
    {
      "id": "rural",
      "label": "Rural residents",
      "metrics": {
        "access_probability": 0.62,
        "expected_benefit": 4.1
      }
    }
  ]
}
```

Use the same group metric identifiers across alternatives. Do not include protected attributes or granular records when aggregated values are sufficient.

Parity ratios require nonnegative group metrics. If a supplied metric contains
negative values, the engine retains absolute group values and gaps but reports
the ratio as unavailable.

## Scoring outputs

- `value_score` is risk-adjusted utility multiplied by 100.
- `probability_best` compares only alternatives that satisfy the ex-ante
  feasibility rule.
- `probability_best_unconstrained` compares all alternatives and is retained
  for traceability.
- `constraint_diagnostics` reports each hard constraint's event count,
  observed rate, one-sided 95% upper bound, declared support, and signed
  margin; positive margin satisfies the constraint.
- `feasible` compares the aggregate one-sided 95% upper bound—not only the
  observed Monte Carlo frequency—with `max_constraint_violation_rate`.
- `scale_clipping_rate` reports how often a modeled outcome falls outside the
  declared worst-to-best scale before bounding.
- `robustness_score` is a transparent diagnostic, not confidence that the
  decision is correct.
- `correlation_sensitivity` contains matched independent, declared, and
  stronger-dependence results, including P(best), CVaR10, breach U95,
  feasibility, and winner changes.
- `parameter_provenance` records every governed parameter path, resolved
  source, ordered approval chain, source coverage, and approval coverage.
