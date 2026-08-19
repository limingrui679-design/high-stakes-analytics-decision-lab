---
name: high-stakes-analytics-decision-lab
description: Build or review source-backed descriptive, diagnostic, predictive, and prescriptive analysis for consequential decisions. Use when an agent must profile and safely prepare uploaded data, turn a real dataset or research question into a reproducible study, investigate drivers without overstating causality, validate a model, compare feasible actions under dependent uncertainty and tail risk, trace every parameter to evidence and approval, or produce an answer-first analytical report across health, business, finance, policy, engineering, operations, behavioral science, AI, or planning.
---

# High-Stakes Analytics & Decision Lab

Turn a real question into a defensible path from source evidence to analysis and,
only when justified, bounded action. Keep observation, diagnosis, prediction,
causal evidence, value judgments, and recommendation visibly separate.

## Start here

Run the environment audit before an executable workflow:

```bash
python3 scripts/hsadl.py doctor
```

For a safe end-to-end setup example:

```bash
python3 scripts/hsadl.py demo --output-dir /absolute/path/to/demo
```

The demo is a synthetic engineering fixture. Never cite its values as empirical
evidence.

## Route before choosing a method

| Route | Primary question | Valid endpoint |
|---|---|---|
| Descriptive | What is happening? | Baseline report or evidence request |
| Diagnostic | Why might it be happening? | Explanations to test with a visible causal boundary |
| Predictive | What is likely next? | Validated prediction, negative validation, or `do_not_deploy` |
| Prescriptive | What should be done, if justified? | Bounded action, pilot, diligence, evidence request, or no recommendation |

When only a question is available, generate a blueprint instead of inventing
results:

```bash
python3 scripts/hsadl.py route "How should limited review capacity be allocated?" \
  --scope full --output-dir /absolute/path/to/blueprint
```

Read `references/analytics-triad.md` and `references/method-routing.md` when a
request is ambiguous or spans several routes.

## Evidence-gated workflow

1. **Define the contract.** State the decision or research question,
   population, analytical unit, target quantity, horizon, intended use,
   stakeholders, and claim boundary.
2. **Establish lineage.** Prefer official, academic, or otherwise authoritative
   sources. Record publisher, version, access date, license, redistribution
   rule, grain, exclusions, file paths, and SHA-256 hashes.
3. **Gate the data.** Preserve every supplied source unchanged. Profile grain,
   keys, schema, completeness, type and domain validity, time reliability,
   privacy signals, and target leakage before calculating a result.
4. **Build the baseline.** Define denominators, coverage, missingness, trends,
   segments, and comparability before diagnosis, prediction, or action.
5. **Add only justified modules.** Select methods from the question, estimand,
   data-generating structure, and decision; never from column availability
   alone.
6. **Validate and challenge.** Use a defensible holdout or identification
   strategy, baseline comparisons, calibration or uncertainty, subgroup or
   distribution checks, dependence-aware stress, sensitivity, and reversal
   conditions as applicable.
7. **Communicate the strongest supported claim—no stronger.** The Evidence
   Intelligence Report is primary. Add a Decision Intelligence Brief only when
   a real decision, feasible alternatives, and sufficient evidence exist.

Read `references/real-evidence-workflow.md`,
`references/data-quality-gate.md`, and `references/methodology.md` for the full
contract.

## Start from a real dataset

Create a reviewable workspace in one command:

```bash
python3 scripts/hsadl.py start /absolute/path/to/input.csv \
  --question "Which groups are likely to need support next month?" \
  --output-dir /absolute/path/to/workspace
```

The initializer copies and hash-checks the source, drafts or accepts a data
contract, profiles readiness, routes the question, and records unresolved
decisions. It must not clean data, fit a model, or generate a recommendation.

The gate returns exactly one of:

- `ready`;
- `ready_with_documented_limitations`;
- `needs_user_confirmation`;
- `blocked`.

Continue only when the gate permits the intended route. Run only `safe_auto`
normalization without approval. Deletion, column removal, imputation, outlier
treatment, category merging, unit or timezone conversion, target correction,
and grain changes require approval by the exact action ID. Fail closed if the
source hash, reviewed action, approval, or raw/processed binding changes.

Direct gate and preparation commands:

```bash
python3 scripts/hsadl.py profile input.csv \
  --contract data-contract.json --output-dir readiness

python3 scripts/hsadl.py prepare input.csv \
  --quality-report readiness/data-quality-report.json \
  --cleaning-plan readiness/cleaning-plan.json \
  --approve clean-003 --output-dir prepared
```

## Select an executable module

| Need | Command | Required boundary |
|---|---|---|
| Two-group binary, continuous, or time-to-event evidence | `hsadl.py evidence` | Match the estimand and study design |
| Held-out scores, calibration, subgroup error, or drift | `hsadl.py predict` | Prediction is not intervention effect |
| Small discrete allocation with constraints and scenarios | `hsadl.py allocate` | Inputs and objectives are not empirical facts by default |
| Multi-criterion decision under dependent uncertainty | `hsadl.py validate` then `hsadl.py run` | Require owner, alternatives, constraints, provenance, approval, tails, sensitivity, and affected groups |

Read `references/method-modules.md` for command contracts and
`references/advanced-method-boundaries.md` before survival, repeated-measures,
financial-risk, spatial, or responsible-AI work.

## Decision layer

Do not begin simulation while the owner, decision, alternatives, horizon, or
hard constraints are ambiguous. Keep the status quo. Classify each input as
observed evidence, causal estimate, predictive output, expert elicitation,
policy target, analyst assumption, or value judgment.

Use fixed external scales, nonnegative weights, explicit marginal uncertainty,
shared shock factors or resampling units, tail metrics, plausible scenarios,
two-sided sensitivity, source coverage, decision-use approval, group impacts,
and reversal conditions. The highest expected score alone is not a
recommendation.

If zero breaches are observed, report the event count and one-sided 95% upper
bound. Never write “zero risk.” Numerical stability cannot upgrade evidence or
permission.

Read `references/case-schema.md`, `references/provenance-contract.md`, and
`references/reproducibility-contract.md` before running a decision case.

## Output contract

For question routing, produce `analysis-blueprint.md`,
`analysis-blueprint.json`, and `figures/analytics-lifecycle.svg`.

For row-level data, produce the readiness report and SVG, machine-readable
quality result, data contract, and cleaning plan before analytical results.
Preserve the source unchanged.

For every complete empirical project, produce:

```text
report.md                    # primary Evidence Intelligence Report
results.json                 # machine-readable result
chart-map.json               # figure-to-question and source contract
figures/*.svg                # all material, accessible analytical figures
```

A justified decision layer additionally produces `decision-report.md`,
`decision-results.json`, and a separate decision figure contract. State “no
decision-ready recommendation” when constraints or evidence invalidate the
ranking. Read `references/reporting-standard.md` and
`references/visual-report-system.md` before finalizing a report.

## Worked precedents

Read `references/case-precedents.md` to choose among fifteen school-neutral,
real-data precedents. Reuse the method contract, never a saved empirical
result, threshold, weight, subgroup definition, causal claim, or
recommendation. A new source, population, time window, objective, or owner
requires a new evidence and validation path.

## Non-negotiable guardrails

- Never fabricate data, findings, accuracy, causal effects, or impact.
- Never silently transform, overwrite, deduplicate, impute, drop, merge, or
  redefine supplied data.
- Never fit learned preprocessing outside the training data.
- Never treat predictive accuracy as evidence that an intervention will work.
- Never hide missing stakeholders, externalities, fairness conflicts, or weak
  transportability.
- Never count synthetic fixtures as public research projects or empirical
  evidence.
- Never present a prototype, public-data case, test result, or reproducibility
  check as production deployment, institutional adoption, external review, or
  achieved real-world impact.
- Require domain review before operational use.
