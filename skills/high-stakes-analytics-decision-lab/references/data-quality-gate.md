# Data Quality Gate

Run this gate whenever a user supplies row-level data. It is part of the
analytical workflow, not a separate audit product. Its purpose is to determine
whether the dataset supports the declared use, identify the smallest safe
preprocessing step, and prevent silent transformations from changing the
estimand or decision.

## Required sequence

1. Preserve the uploaded source without modification and record its SHA-256.
2. Declare or cautiously infer the dataset grain, candidate key, time fields,
   target, required fields, units, allowed values, sensitive fields, and
   intended analytical route.
3. Profile completeness, uniqueness, validity, consistency, integrity,
   timeliness, volume, shape, privacy, distribution, and leakage risk.
4. Assign a gate status before fitting a model or comparing alternatives.
5. Produce a dry-run cleaning plan that separates safe automatic normalization
   from transformations requiring explicit approval.
6. Apply approved transformations only to a new processed file.
7. Re-run the complete quality gate and preserve a before/after transformation
   log.

The supplied command-line profiler is the inspectable single-file baseline.
For multi-file joins, experiments, late-arriving partitions, or historical
drift, extend the same gate with relationship, assignment, freshness, and
time-segment checks before continuing.

For XLSX, Parquet, database, or other unsupported inputs, preserve and hash the
original source, create a lossless tabular extract with a conversion receipt,
and profile that extract. Never present the extract hash as the original-file
hash, and never flatten multiple tables without declaring the resulting grain
and join logic.

## Bounded ingestion and privacy pause

The inspectable baseline rejects inputs above 128 MiB, more than 500,000 rows
or 256 columns, cells above 65,536 characters, and JSON nesting beyond 24
levels. JSON arrays are capped at 16 MiB; use JSONL for larger bounded extracts.
CSV, TSV, JSONL, and NDJSON rows are re-opened as streams instead of retaining
the complete row set in memory.

Privacy checks combine declared and named fields with value-level signals for
email addresses, telephone numbers, U.S. Social Security numbers, Chinese
resident identity numbers, IP addresses, postal addresses, common adult
birth-date formats, and common medical-information terms. Sensitive or
quasi-identifying fields and sensitive data in a sample below 50 rows produce a
high-severity finding and therefore `needs_user_confirmation` at minimum.
Reports never reproduce detected cell values; extrema and quantiles are also
suppressed for detected identifier and sensitive fields.

## Gate statuses

| Status | Meaning | Permitted next step |
|---|---|---|
| `ready` | No material problem was detected under the declared contract | Continue to route-specific analysis |
| `ready_with_documented_limitations` | Medium issues remain but do not invalidate the declared use | Continue with visible limitations and additional route checks |
| `needs_user_confirmation` | A high-severity issue or substantive cleaning choice remains | Pause analysis until specific action IDs are approved or the source is corrected |
| `blocked` | Grain, key, schema, leakage, or another critical failure invalidates the current evidence | Do not analyze; request corrected evidence or a revised contract |

The gate is necessary but not sufficient for a predictive or prescriptive
claim. A clean dataset can still have the wrong target, weak identification,
poor transport, or an invalid decision context.

## Safe automatic actions

Only transformations that are semantically unambiguous and reversible may run
without confirmation:

- trim surrounding whitespace;
- convert explicitly declared missing sentinels to one empty representation;
- canonicalize a contract-declared numeric column only after every observed
  value parses as a finite number, using decimal-safe output so large integers
  do not lose precision;
- canonicalize a contract-declared ISO-like date only after every observed
  value parses reliably, without collapsing year, month, date, or timestamp
  precision.

Record the number of affected cells for every action. Preserve internal text,
original source bytes, and the raw-file hash.

## Actions requiring confirmation

Require approval by cleaning-plan action ID before:

- deleting duplicate rows or resolving duplicate entities;
- dropping columns, including direct identifiers;
- excluding records;
- imputing missing values;
- capping, winsorizing, deleting, or transforming outliers;
- combining categories;
- converting units, currencies, timezones, or observation windows;
- correcting labels or redefining a target;
- changing the analytical grain.

Generic preprocessing must not execute a manual-review item merely because the
user says “clean the data.” The user must approve a concrete rule, and the
transformation log must state its scope and observed impact.

The cleaning plan is bound back to the reviewed quality report. A changed
source hash, modified action definition, unknown approval ID, attempted
approval of a safe action, or output path that resolves to the raw source must
fail closed.

## Minimum contract checks

- A missing intended use or grain pauses at `needs_user_confirmation`.
- Duplicate or blank headers and values without headers block the workflow.
- Predictive use requires a present target and present feature fields.
- A target cannot also be declared as a feature.
- Declared numeric, date, categorical, and inclusive numeric-range rules are
  checked before analysis.
- User-supplied missing sentinels are authoritative; undeclared values such as
  `NA` are not silently reclassified.

## Route-specific rules

### Descriptive

- preserve denominators and disclose every exclusion;
- compare missingness and coverage by relevant time and segment;
- distinguish a true zero from missing, not collected, not applicable, and
  withheld values;
- do not repair an apparent anomaly without source evidence.

### Predictive

- declare the target, horizon, prediction grain, and decision-time cutoff;
- remove forbidden or post-outcome fields from the feature set;
- fit imputers, encoders, scalers, and outlier rules on training data only;
- preserve ordered time splits and test period reliability;
- inspect class balance, subgroup coverage, sparsity, and drift after
  preprocessing.

### Prescriptive

- verify units, currency, direction, and scale for every criterion;
- trace constraints and thresholds to an approved source;
- test whether cleaning choices change feasibility, ranking, tail risk, or
  probability-best;
- stop if a material decision result depends on an unresolved data-quality
  choice.

## Required artifacts

```text
data-quality-report.md
data-quality-report.json
data-contract.json
cleaning-plan.json
figures/data-quality-overview.svg

processed/analysis.csv
transformation-log.json
post-cleaning/data-quality-report.md
post-cleaning/data-quality-report.json
post-cleaning/data-contract.json
post-cleaning/cleaning-plan.json
post-cleaning/figures/data-quality-overview.svg
```

The Markdown report is answer-first and includes the gate, dataset shape,
findings, analytical risks, and proposed transformations. The JSON artifacts
preserve the exact contract and machine-readable findings. The SVG is an
accessible decision visual; it must not display raw personal identifiers.

## Commands

Copy and complete `assets/data-contract-template.json`, then run:

```bash
python3 scripts/profile_dataset.py /absolute/path/to/input.csv \
  --contract /absolute/path/to/data-contract.json \
  --output-dir /absolute/path/to/readiness
```

Safe automatic normalization plus explicitly approved executable actions:

```bash
python3 scripts/prepare_dataset.py /absolute/path/to/input.csv \
  --quality-report /absolute/path/to/readiness/data-quality-report.json \
  --cleaning-plan /absolute/path/to/readiness/cleaning-plan.json \
  --approve clean-003 \
  --output-dir /absolute/path/to/prepared
```

Never approve a non-executable manual-review item. Correct the source or encode
a case-specific, reviewable rule instead.
