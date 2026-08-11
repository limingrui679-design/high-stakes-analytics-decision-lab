---
name: high-stakes-analytics-decision-lab
description: Build or review source-backed descriptive, diagnostic, predictive, and prescriptive analysis for consequential decisions. Use when an agent must profile and safely prepare uploaded data, turn a real dataset or research question into a reproducible study, investigate drivers without overstating causality, validate a model, compare feasible actions under dependent uncertainty and tail risk, trace every parameter to evidence and approval, or produce an answer-first analytical report across health, business, finance, policy, engineering, operations, behavioral science, AI, or planning.
---

# High-Stakes Analytics & Decision Lab

Turn a real research question into a defensible path from source evidence to
prediction and, only when justified, action. Keep description, diagnosis,
prediction, causal inference, value judgments, and the final recommendation
visibly separate.

## Workflow

### 0. Route the question

Classify the analytical request:

| Lens | Question | Required output |
|---|---|---|
| Descriptive | What is happening? | Baseline, trends, segments, denominators, and data limitations |
| Diagnostic | Why might it be happening? | Contributions, competing explanations, testable hypotheses, and a visible causal boundary |
| Predictive | What is likely to happen? | Forecast or risk distribution with out-of-sample validation and uncertainty |
| Prescriptive | What should be done—and how? | Feasible alternatives, trade-offs, recommendation, and reversal conditions |

Select diagnostic analysis when the request asks why a pattern occurred or
which drivers warrant investigation. Do not convert a correlated driver into
a cause without an identification strategy.

When only a question is available, generate a visual analysis blueprint:

```bash
python3 scripts/route_question.py "How should we allocate limited capacity?" \
  --output-dir /absolute/path/to/blueprint
```

Use `--scope full` for the complete baseline-to-decision sequence. Use
`--scope auto` for the primary route and its prerequisites. Read
[analytics-triad.md](references/analytics-triad.md) before routing an ambiguous
or multi-stage question.

Do not fabricate results when data are absent. State the required data,
metrics, horizon, validation design, alternatives, constraints, and affected
groups.

### 1. Establish the real-evidence contract

Before analysis, prefer an official, academic, or otherwise authoritative
source whose redistribution terms permit the intended repository use. Record:

- landing and direct-download URLs, publisher, version, access date, citation,
  license, and redistribution rule;
- the exact raw file paths and SHA-256 hashes;
- source grain, expected row count, privacy treatment, exclusions, and
  permitted analytical use;
- a reproducible download receipt and a prepared-data quality report.

Never substitute a synthetic case for an empirical project. Synthetic data are
allowed only as clearly separated engineering fixtures for deterministic,
property, boundary, or extreme-input tests. Read
[real-evidence-workflow.md](references/real-evidence-workflow.md) before
starting a new project.

### 2. Gate uploaded data before analysis

Whenever a user supplies row-level data, preserve the source unchanged and run
the data-quality gate before calculating a descriptive result, fitting a model,
or comparing decisions. For a new dataset, initialize the complete review
workspace in one command:

```bash
python3 scripts/init_case.py /absolute/path/to/input.csv \
  --question "Which groups are most likely to need support next month?" \
  --output-dir /absolute/path/to/case-workspace
```

The initializer preserves and hash-checks the source, drafts the contract,
profiles quality, routes the question, and lists unresolved decisions. It must
not apply cleaning, fit a model, or generate a recommendation.

To run the gate separately, copy and complete
[data-contract-template.json](assets/data-contract-template.json), then run:

```bash
python3 scripts/profile_dataset.py /absolute/path/to/input.csv \
  --contract /absolute/path/to/data-contract.json \
  --output-dir /absolute/path/to/readiness
```

For XLSX, Parquet, database, or multi-table inputs, hash the original and create
a traceable tabular extract; retain the conversion receipt, table relationships,
join checks, and original-versus-extract hashes.

The gate checks grain, schema, completeness, uniqueness, type and domain
validity, temporal reliability, distributions, privacy, and declared leakage
rules. It produces a visual Data Readiness Report, machine-readable findings,
and a dry-run cleaning plan with one of four statuses:

- `ready`;
- `ready_with_documented_limitations`;
- `needs_user_confirmation`;
- `blocked`.

Treat an inferred contract as profiling assistance, not permission to analyze:
missing intended use or grain must pause at `needs_user_confirmation`.
Duplicate or blank headers, unlabelled extra fields, missing predictive
features or targets, target-as-feature overlap, broken keys, and declared
leakage block the workflow. Apply user-declared missing sentinels and numeric
ranges exactly; do not silently expand them.

Run only `safe_auto` actions without asking. Require approval by action ID for
row deletion, column removal, imputation, outlier treatment, category merging,
unit or timezone conversion, target correction, or grain changes. Never execute
a non-executable manual-review action generically.

```bash
python3 scripts/prepare_dataset.py /absolute/path/to/input.csv \
  --quality-report /absolute/path/to/readiness/data-quality-report.json \
  --cleaning-plan /absolute/path/to/readiness/cleaning-plan.json \
  --approve clean-003 \
  --output-dir /absolute/path/to/prepared
```

Use the processed copy only after the post-cleaning gate permits the intended
route. Do not continue when the gate is `blocked`, and do not continue past
`needs_user_confirmation` until the relevant issue or cleaning choice is
resolved. Fail closed if the source hash, reviewed action definition, approval
ID, or raw/processed path binding changes. Read
[data-quality-gate.md](references/data-quality-gate.md) for the complete policy
and route-specific requirements.

### 3. Establish the descriptive baseline

Before forecasting or recommending:

- define the population, unit of analysis, time window, metric, and denominator;
- inspect missingness, coverage, outliers, comparability, and segment gaps;
- separate observed patterns from explanations;
- record source provenance and exclusions.

For a narrow descriptive request, stop here. For diagnostic, predictive, or
prescriptive work, carry the baseline and data-quality findings into the next
stage.

### 4. Build or review the predictive layer

Define the target, horizon, prediction grain, and information available at
decision time. Compare against a simple baseline and use a time-aware or
otherwise defensible validation design. Report calibration, uncertainty,
subgroup error, leakage risk, and drift.

A prediction of outcomes under an intervention is not automatically the causal
effect of that intervention. When the decision depends on intervention effects,
require experimental, quasi-experimental, or otherwise defensible causal
evidence.

When row-level evidence is supplied, select an executable method module before
building the decision case:

- use `scripts/evidence_analysis.py` for two-group binary, continuous, and
  time-to-event evidence;
- use `scripts/prediction_validation.py` for held-out score validation,
  calibration, subgroup errors, and drift;
- use `scripts/allocation_optimizer.py` for a small discrete resource-allocation
  problem with linear constraints and scenarios.

Read [method-modules.md](references/method-modules.md) for commands, output
contracts, and method boundaries. Do not use a method merely because the
columns exist; match the estimand and decision. Read
[advanced-method-boundaries.md](references/advanced-method-boundaries.md) when
using survival, repeated-measures, financial-risk, spatial, or responsible-AI
methods.

### 5. Frame the decision

Identify:

- the decision owner and affected stakeholders;
- the decision that must be made now;
- a status-quo alternative plus at least one feasible intervention;
- the time horizon and scope;
- evaluation criteria, their units, directions, weights, and defensible scales;
- hard constraints;
- material uncertainties and scenarios;
- shared shock factors, signed loadings, and a stronger-correlation stress;
- a source and approval-chain rule for every governed parameter family;
- groups that may experience different benefits or harms.

Do not begin simulation while the alternatives or decision owner remain ambiguous. Ask only for information that materially changes the model.

### 6. Classify the evidence

Label every quantitative input as one of:

- observed descriptive evidence;
- experimental or quasi-experimental estimate;
- predictive-model output;
- expert elicitation;
- policy target;
- analyst assumption or value judgment.

Never relabel an association, prediction, or scenario assumption as a causal effect. Read [methodology.md](references/methodology.md) before analyzing causal, clinical, financial, or safety-critical claims.

### 7. Build the case file

Copy [case-template.json](assets/case-template.json) and replace every placeholder. Follow [case-schema.md](references/case-schema.md). Keep criterion identifiers and alternative identifiers stable and machine-readable.

Use fixed external scales rather than the observed minimum and maximum across current alternatives. This reduces rank reversal when an alternative is added.

Require criterion weights to be nonnegative. Normalize them during analysis.
Use schema `1.3`. Represent marginal uncertainty with fixed, normal, uniform,
triangular, empirical, or bootstrap distributions and declare whether each
term is parameter, process, scenario, or no uncertainty. Preserve repeated,
temporal, market, campaign, participant, and geographic dependence through
shared resampling units or latent factors. Never leave material common shocks
independent merely for convenience.

Map every weight, scale, distribution field, scenario input, constraint
threshold, dependence loading, and model parameter to a traceable source and
approval chain. Read
[provenance-contract.md](references/provenance-contract.md).

Migrate a legacy 1.2 fixture without changing it in place:

```bash
python3 scripts/migrate_case_v12_to_v13.py old-case.json \
  --output migrated-case.json
```

The migration conservatively labels every non-fixed legacy distribution as
parameter uncertainty. Review those labels before using the result.

### 8. Validate before running

Run from the skill directory:

```bash
python3 scripts/validate_case.py /absolute/path/to/case.json
```

Resolve every error. Treat warnings as disclosure requirements; do not silently suppress them.

### 9. Analyze uncertainty and trade-offs

Run:

```bash
python3 scripts/run_case.py /absolute/path/to/case.json \
  --output-dir /absolute/path/to/output \
  --samples 10000 \
  --seed 20260726
```

The engine produces:

- expected, tail, and risk-adjusted decision value scores;
- matched independent, declared-correlation, and stronger-correlation results
  for P(best), CVaR10, breach U95, feasibility, and winner changes;
- aggregate and constraint-level violation events, observed rates, one-sided
  95% upper bounds, declared-support diagnostics, and signed margins;
- probability of being best among decision-feasible alternatives;
- expected criterion values and uncertainty intervals;
- scenario-specific risk-adjusted performance and stability;
- feasible and unconstrained Pareto frontiers;
- two-sided, risk-consistent weight sensitivity;
- scale-clipping diagnostics;
- parameter-level source coverage and decision-use approval coverage;
- a transparent four-component robustness score;
- decision status separated from numerical robustness;
- group-impact gaps and ratios;
- a machine-readable result and an executive decision brief;
- GitHub-native SVG scorecards, ranking, constraint-risk, uncertainty,
  correlation-stress, criterion, scenario, sensitivity, and group-impact
  figures.

Use at least 10,000 samples for a shareable analysis. Use fewer only for a quick draft and label it accordingly.

### 10. Interpret, challenge, and communicate

Check whether:

- the recommendation remains stable under criterion-weight sensitivity;
- the winner and tail-risk result survive a stronger shared-shock stress;
- P(best) changes materially when residual independence is removed;
- every governed parameter has a resolved source and approval scope matching
  the declared decision use;
- a different alternative wins in a plausible adverse scenario;
- feasibility depends on an optimistic assumption;
- distributional harms are hidden by average outcomes;
- the status quo is dominated;
- the evidence supports the strength of the wording.

Read [reporting-standard.md](references/reporting-standard.md) before finalizing
a brief. Read [visual-report-system.md](references/visual-report-system.md)
and [editorial-visual-system.md](references/editorial-visual-system.md) before
producing a shareable visual report. The **Evidence Intelligence Report** is
the primary evidence product. A **Decision Intelligence Brief** is a
conditional downstream layer and must never replace, abbreviate, or hide the
primary evidence product. Read
[domain-playbooks.md](references/domain-playbooks.md) for domain-specific
criteria and failure modes. To select the smallest defensible analytical path
from the question and available data, read
[method-routing.md](references/method-routing.md).

Compose shareable reports as an evidence sequence, not as a chart gallery
followed by a text wall. Alternate a bounded result, its full-width visual,
the adjacent interpretation and claim boundary, then the next relevant
source, design, quality, or method block. Use compact tables for exact metrics
and contracts. Parameter-level registers and reproducibility receipts may be
placed in `<details>` blocks, but never hide the bottom line, methods,
validation result, uncertainty, limitations, or decision status. Every visual
must answer a stated analytical question; do not add decorative graphics merely
to break up prose.

Do not recommend an alternative merely because it has the highest expected utility. Prefer a feasible option with acceptable tail performance and disclose any robustness or equity trade-off.

If a simulation observes zero constraint breaches, never write “zero risk.”
Report the event count, the one-sided 95% upper bound, and whether the declared
input support mathematically excluded a breach. A bounded-support zero is an
assumption diagnosis, not evidence that real-world risk is impossible.

## Bundled real-data projects

Use [the fifteen-project case index](examples/real-data-cases/README.md) when a
worked precedent would improve method selection or reporting. The bundle
contains fifteen complete, reproducible projects across operations, urban
information systems, marketing, responsible AI, financial risk, fintech,
real estate, wildfire decision analysis, regulatory filings, field
experiments, population health, public policy, repeated measures,
transportability, and spatial planning.

Each project includes its reviewed raw source snapshot, source manifest and
hashes, configuration, preparation and analysis code, Evidence Intelligence
Report, all figures, and machine-readable results. Ten of the fifteen projects
also include an evidence-matched Decision Intelligence Brief. The Evidence
Intelligence Report is the primary project record. A Decision Intelligence
Brief is added only when a separate decision layer is justified; otherwise the
analytical result itself records the bounded terminal status. Decision
Intelligence Briefs may
end in a bounded comparison, `do_not_deploy`, a randomized-pilot requirement,
targeted diligence, or an evidence request. Use
`examples/real-data-cases/cases.json` as the machine-readable case index.

Treat the projects as method precedents, not answer templates. Copy neither a
saved empirical result nor a threshold, weight, subgroup definition, causal
claim, or recommendation into a new case without new evidence and review.

## Output contract

Do not force every case into one report template. Keep a stable evidence spine,
then add only the fields, sections, methods, and figures required by the
selected route:

| Route | Case-specific additions | Valid terminal output |
|---|---|---|
| Descriptive | Cohort, denominator, coverage, trend, distribution, segment, and missingness fields | Baseline report or evidence request |
| Diagnostic | Contribution, process, comparison, and hypothesis fields | Prioritized explanations to test; causal boundary retained |
| Predictive | Target, horizon, split, baseline, discrimination, calibration, error, drift, and uncertainty fields | Validated prediction, negative validation, or do-not-deploy result |
| Prescriptive | Decision owner, alternatives, criteria, constraints, dependence, tail risk, sensitivity, and reversal fields | Bounded recommendation or no decision-ready recommendation |

Every route must still include the question, scope, source lineage, data-quality
status, supported findings, limitations, and next action. Dynamic fields must
be machine-readable and mirrored in the narrative; omit inapplicable sections
instead of filling them with generic prose.

For question routing, deliver:

1. `analysis-blueprint.md` explaining the selected routes, methods, required data,
   validity checks, and handoffs.
2. `analysis-blueprint.json` preserving the routing decision and data contract.
3. `figures/analytics-lifecycle.svg` visualizing the question-to-decision path.

For uploaded row-level data, deliver before analytical results:

1. `data-quality-report.md` and `figures/data-quality-overview.svg` as the
   answer-first readiness decision.
2. `data-quality-report.json`, `data-contract.json`, and `cleaning-plan.json`
   as the machine-readable gate and dry-run remediation plan.
3. When preparation runs, `processed/analysis.csv`,
   `transformation-log.json`, and a complete `post-cleaning/` quality bundle.

The source file must remain unchanged. A blocked or confirmation-required
quality gate is a valid terminal output and must not be hidden by a downstream
analysis.

For every source-backed analytical project, deliver:

1. `report.md` as the **Evidence Intelligence Report**, including the
   question, evidence and data-quality contract, methods, validation, every
   material figure with adjacent interpretation, uncertainty, limitations,
   claim boundary, and reproducibility.
2. `results.json` containing the complete machine-readable analytical result.
3. `figures/*.svg` and `chart-map.json` covering every material visual,
   not only a representative chart.

When a real decision layer is requested and justified, additionally deliver:

1. `decision-results.json` containing assumptions, scores, sensitivity results, and provenance.
2. `decision-report.md` as the **Decision Intelligence Brief**, containing an
   answer-first executive summary, adjacent interpretation for every visual,
   recommendation, ranking, uncertainty, scenario resilience, group impacts,
   next steps, further questions, and caveats.

- Decision-layer figures must remain accessible, directly labeled, and
  GitHub-renderable.
- The decision-layer `figures/chart-map.json` must record each figure's analytical question,
  supported takeaway, benchmark, chart family, source, palette policy,
  accessibility treatment, and report section.
- Link the Decision Intelligence Brief back to the Evidence Intelligence
  Report (`report.md`) and `results.json`.

State “no decision-ready recommendation” when all alternatives breach hard constraints or when evidence limitations make the ranking misleading.
Use “illustrative preference,” not “recommendation,” when
`evidence.decision_use` is `illustrative`. Numerical stability must never
upgrade the permitted use of the evidence.

## Guardrails

- Treat weights as values, not empirical facts.
- Preserve every uploaded source unchanged and verify its hash before applying
  a cleaning plan.
- Never silently deduplicate, impute, delete outliers, merge categories, drop
  columns, change units, or redefine a target or grain.
- Fit learned preprocessing only on training data and carry it unchanged into
  validation and test data.
- Preserve the status quo or a credible do-nothing baseline.
- Never use synthetic examples as real medical, financial, or policy advice.
- Never count test fixtures as public research projects or empirical evidence.
- Never invent descriptive findings, forecast accuracy, or recommendations when
  the required data or decision inputs are absent.
- Never treat predictive accuracy as evidence that an intervention will work.
- Do not hide missing stakeholders, unmodeled externalities, or conflicting fairness definitions.
- Do not convert model precision into unwarranted decision confidence.
- Require domain review before operational deployment.
