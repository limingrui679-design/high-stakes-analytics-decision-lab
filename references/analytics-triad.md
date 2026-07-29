# Analytics Triad

## The three primary lenses

| Lens | Core question | Evidence role | Typical output |
|---|---|---|---|
| Descriptive | What is happening? | Establish the observed baseline, trends, segments, denominators, and data limitations. | Scorecard, trend, distribution, cohort, funnel, or segment view |
| Predictive | What is likely to happen? | Estimate future outcomes or risks with out-of-sample validation and uncertainty. | Forecast, risk score, interval, calibration view, or scenario distribution |
| Prescriptive | What should be done—and how? | Combine evidence with alternatives, objectives, constraints, risk tolerance, and stakeholder values. | Feasible ranking, allocation, policy recommendation, monitoring plan |

Prescriptive analytics is the “how” layer. It does not follow automatically
from the highest prediction. A recommendation requires an authorized decision
owner, an actionable choice set, explicit values, feasibility constraints,
uncertainty, and material group impacts.

## Optional diagnostic bridge

Diagnostic analysis asks why an observed pattern occurred. Use decomposition,
segment contribution, funnel analysis, process tracing, and testable
hypotheses. Treat these as explanations to investigate. Claim causation only
when a credible experimental or quasi-experimental design supports it.

## Automatic routing

For one broad decision question, use all three lenses in order:

1. describe the baseline and data quality;
2. predict outcomes under the status quo and alternatives;
3. prescribe a feasible action and state reversal conditions.

For a narrow request, use only the requested lens and its prerequisites:

- descriptive → descriptive;
- diagnostic → descriptive + diagnostic;
- predictive → descriptive + predictive;
- prescriptive → descriptive + predictive + prescriptive.

Never manufacture later-stage results when earlier-stage evidence is missing.
With only a question, generate an analysis blueprint and minimum data contract.

## Evidence boundaries

- Descriptive difference is not causal effect.
- Predictive accuracy is not intervention effectiveness.
- A causal estimate is not a policy recommendation.
- A recommendation is not value-free; it depends on objectives, constraints,
  risk tolerance, and distributional judgments.

## Completion gates

Before moving from description to prediction, require a defined target,
horizon, data grain, and evaluation split. Before moving from prediction to
prescription, require alternatives, constraints, outcome distributions, and an
explicit value model. Stop with “not decision-ready” when these are absent.
