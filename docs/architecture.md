# Architecture

High-Stakes Analytics & Decision Lab is an evidence-gated orchestration system,
not a fixed report template. It separates what is observed, what is modeled,
what is valued, and what can responsibly be recommended.

## Design principles

| Principle | System behavior |
|---|---|
| Evidence before method | Define the question, population, grain, target quantity, horizon, lineage, and claim boundary before selecting a model |
| Data readiness before analysis | Preserve the source, profile quality and privacy, and pause on material transformations |
| Adaptive routes | Add diagnostic, predictive, causal, spatial, risk, or optimization work only when the question and evidence require it |
| Honest terminal states | Allow evidence requests, negative validation, `do_not_deploy`, and no recommendation |
| Dependent uncertainty | Preserve shared time, market, participant, campaign, operational, or spatial shocks |
| Reproducible communication | Link narrative claims and accessible figures to machine-readable results, hashes, and rerunnable code |

## Evidence-to-decision lifecycle

![Adaptive reporting routes a question through evidence gates before a conditional decision layer](../assets/adaptive-reporting-system.svg)

The fixed evidence spine remains stable while the case-specific analytical
layer changes.

| Fixed evidence spine | Adaptive case layer |
|---|---|
| Question, population, unit, target quantity, and horizon | Route, fields, methods, and validation |
| Source lineage, quality status, and reproducibility | Figures, report sections, and decision criteria |
| Uncertainty, limitations, and claim boundary | Bounded action, evidence request, or stopping status |

## Data-readiness gate

Uploaded row-level data do not go directly into a model. The system preserves
the original, establishes a contract, checks grain and keys, profiles quality
and privacy, and produces a dry-run remediation plan.

| Gate status | Meaning | Permitted next step |
|---|---|---|
| `ready` | No material failure under the declared contract | Continue |
| `ready_with_documented_limitations` | Localized issues remain | Continue with visible limits |
| `needs_user_confirmation` | A substantive cleaning, privacy, or intended-use choice remains | Pause for named approval or clarification |
| `blocked` | Grain, key, schema, leakage, or another critical failure invalidates the route | Stop and request corrected evidence |

Only safe normalization can run without approval. The post-cleaning gate binds
the approved action definition, source hash, raw path, processed path, and
transformation log so a changed input or plan fails closed.

## Four analytical routes

| Route | Primary question | Required discipline | Valid endpoint |
|---|---|---|---|
| Descriptive | What is happening? | Denominators, coverage, trends, segments, missingness | Baseline report or evidence request |
| Diagnostic | Why might it be happening? | Contributions, competing explanations, hypotheses, visible causal boundary | Prioritized explanations to test |
| Predictive | What is likely next? | Target, horizon, baseline, held-out validation, calibration, subgroup error, drift | Validated prediction, negative validation, or `do_not_deploy` |
| Prescriptive | What should be done, if justified? | Decision owner, alternatives, constraints, dependence, tail risk, sensitivity, reversal conditions | Bounded action or no decision-ready recommendation |

Routes can compose, but a later route cannot erase the evidence and quality
requirements of an earlier stage.

## Two products, one contract

![The Evidence Intelligence Report remains primary and the Decision Intelligence Brief is conditional](../assets/report-layers.svg)

The **Evidence Intelligence Report** is always the primary record. It contains
the source and quality contract, methods, validation, material figures,
uncertainty, limitations, claim boundary, and reproducibility instructions.

The **Decision Intelligence Brief** is conditional. It explains what action,
pilot, diligence, evidence request, or stop follows from the evidence. It never
replaces or abbreviates the primary evidence product.

## Decision engine

When a decision layer is justified, the case schema keeps alternatives,
criteria, fixed external scales, constraints, sources, approval scopes,
uncertainty classes, and shared shocks machine-readable. The engine examines:

- expected, tail, and risk-adjusted decision value;
- P(best), CVaR10, feasibility, and one-sided breach bounds;
- declared and stronger-correlation stress;
- scenario performance and winner changes;
- two-sided weight sensitivity and scale clipping;
- source and decision-use approval coverage;
- group-impact gaps and ratios;
- reversal conditions and the difference between numerical robustness and
  decision authorization.

The engine never treats the highest expected utility as sufficient on its own.

## Visual evidence system

The shared visual language is generated from
[`scripts/visual_system.py`](../scripts/visual_system.py) and defined in the
[`Editorial Evidence System`](../references/editorial-visual-system.md).
Every canonical SVG must include a title and description, use direct labels or
non-color cues, identify its analytical question, and sit beside the supported
interpretation and claim boundary.

Repository restructuring must preserve this system. Documentation can move;
canonical figure styles and generated analytical outputs must not be hand-edited
as decorative assets.

## Responsible-use boundary

The system is a public research and portfolio prototype. It does not establish
production readiness, institutional adoption, medical advice, investment
advice, a regulatory finding, an assurance opinion, or achieved real-world
impact. Domain review remains mandatory before operational use.

