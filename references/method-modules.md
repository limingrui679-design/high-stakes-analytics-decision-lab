# Executable Method Modules

The decision engine is the integration layer. Use the smallest upstream method
module that can produce defensible evidence for a case, and preserve the method
output beside the decision report.

## Data readiness and controlled preprocessing

Use `scripts/profile_dataset.py` before every row-level analytical module. It
supports CSV, TSV, JSON arrays, JSON objects with a `rows` array, JSONL, and
NDJSON. Supply a completed `assets/data-contract-template.json` whenever the
grain, required fields, key, time fields, numeric fields, allowed values,
target, feature timing, or privacy boundary is known.

```bash
python3 scripts/profile_dataset.py /path/to/input.csv \
  --contract /path/to/data-contract.json \
  --output-dir /path/to/readiness
```

The module writes a visual and machine-readable gate plus a dry-run cleaning
plan. It never reproduces detected identifier values in the report.

Apply reversible safe actions and any specifically approved executable action
to a new file:

```bash
python3 scripts/prepare_dataset.py /path/to/input.csv \
  --quality-report /path/to/readiness/data-quality-report.json \
  --cleaning-plan /path/to/readiness/cleaning-plan.json \
  --approve clean-003 \
  --output-dir /path/to/prepared
```

The source hash must match the reviewed report. Manual-review actions cannot be
executed by the generic preparer. Continue only from
`processed/analysis.csv` when the post-cleaning gate permits the intended
analytical route. See [data-quality-gate.md](data-quality-gate.md).

## Statistical evidence analysis

Use `scripts/evidence_analysis.py` for a transparent two-group descriptive
analysis of individual-level CSV data:

- data completeness by required column;
- binary risks, risk difference, risk ratio, odds ratio, and approximate
  confidence intervals;
- continuous-outcome group summaries and mean difference;
- optional Kaplan–Meier survival at a declared horizon.

Example:

```bash
python3 scripts/evidence_analysis.py /path/to/study-data.csv \
  --group arm \
  --outcome adverse_event_180d \
  --exposed adaptive \
  --reference standard \
  --continuous health_score_change \
  --time followup_days \
  --event event \
  --horizon 180 \
  --output-dir /path/to/evidence-output
```

The module does not determine whether a comparison is causal. Before using
causal language, document assignment, estimand, interference, missing-data,
adherence, multiplicity, and transportability assumptions. Use a specialist
statistical package for covariate adjustment, clustered designs, complex
survival models, or production clinical analysis.

## Prediction validation

Use `scripts/prediction_validation.py` for held-out binary prediction scores:

- AUC and Brier score;
- calibration bins and expected calibration error;
- threshold confusion metrics;
- subgroup discrimination and error rates;
- score-distribution drift between the verified earliest and latest supplied
  periods.

Example:

```bash
python3 scripts/prediction_validation.py /path/to/predictions.csv \
  --label label \
  --score score \
  --group group \
  --period period \
  --threshold 0.5 \
  --output-dir /path/to/validation-output
```

Validate that the rows are genuinely out of sample and that all predictors were
available at decision time. Prediction validation does not estimate the effect
of acting on a prediction. Thresholds must be finite and within `[0, 1]`.
Calibration bins must be an integer from 2 to 100 and cannot exceed the number
of complete observations. Scores must be finite probabilities and labels must
be exactly 0 or 1. When `--period` is supplied, every analyzed row must have a
period and ordering must be numeric, ISO-8601 chronological, or one of the
supported lifecycle labels; ambiguous lexical sorting is rejected.

## Resource-allocation optimization

Use `scripts/allocation_optimizer.py` for exact enumeration of small,
discretized linear allocation problems with:

- resource bounds and step sizes;
- a budget and additional linear constraints;
- scenario-specific benefit coefficients;
- expected value, worst-case value, a transparent risk-adjusted objective, and
  maximum regret.

Example:

```bash
python3 scripts/allocation_optimizer.py /path/to/optimization-config.json \
  --output-dir /path/to/optimization-output
```

The result is exactly optimal only on the declared grid. Use a production
linear, mixed-integer, nonlinear, or stochastic optimizer when the decision is
large, continuous, nonlinear, or operationally consequential.

## Handoff into the decision engine

1. Preserve the upstream JSON, Markdown, and SVG outputs.
2. Convert only decision-relevant estimates into case distributions.
3. Record the source module and its limitations in `evidence.sources` and
   `evidence.limitations`.
4. Keep estimation uncertainty distinct from scenario uncertainty and
   stakeholder weights.
5. Never claim that the downstream ranking validates the upstream model.
