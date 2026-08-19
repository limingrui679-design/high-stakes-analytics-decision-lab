# Visual Report System

Use this reference whenever an output will be shared as a report, decision
artifact, or GitHub-rendered analytical brief.

## Design objective

Create an executive analytical report, not a decorative dashboard. The visual
system must make the decision, comparison, risk boundary, and next action
faster to understand while preserving uncertainty and evidence limits.

## Information hierarchy

1. State the decision status and preferred modeled option before method detail.
2. Give each visual one central analytical question.
3. Put the most decision-relevant comparison in the largest visual region.
4. Place the benchmark, tolerance, target, or status-quo reference inside the
   chart when the conclusion depends on it.
5. Label values and identities directly whenever space permits.
6. Follow every visual with a reader-facing interpretation and implication.
7. Keep detailed calculations in the numerical appendix.

## Report rhythm

Do not place every figure in an opening gallery and leave methods,
provenance, limitations, and next steps as one long text tail. Interleave the
evidence in reading order:

1. bounded result;
2. full-width figure;
3. interpretation and claim boundary;
4. compact source, design, quality, or method block;
5. next material figure.

Use tables for exact values and evidence contracts. Collapse only detailed
parameter registers, secondary numerical appendices, and reproducibility
receipts. Keep the bottom line, analytical method, validation result,
uncertainty, limitations, and decision status visible. A diagram must explain a
real workflow or relationship; it is not a substitute for decorative spacing.

## Visual grammar

- Use a dark navy report header, near-white analytical canvas, deep charcoal
  text, quiet grid lines, and one domain accent.
- Use the domain accent for the preferred option or principal finding. Use
  additional categorical roots only when alternatives must retain identity
  across a scenario comparison.
- Do not use a rainbow scale, ornamental 3D effects, or gradients inside data
  marks.
- Do not encode status through color alone. Pair color with labels, rank
  numbers, marker shapes, outlines, or line styles.
- Prefer horizontal labels. Avoid legends when direct labels are feasible.
- Use small multiples for repeated scenario comparisons.
- Use dot-and-interval displays for uncertainty, bullet bars for targets and
  thresholds, and heatmaps only when repeated cell comparison is the question.
- Keep chart axes honest and consistent. The 0–1 decision-value scale starts at
  zero; constraint-risk plots start at zero and show the tolerance.

## Accessibility contract

Every SVG must include:

- a `<title>` naming what is plotted;
- a `<desc>` summarizing the analytical relationship;
- directly visible numeric labels for the primary comparison;
- redundant status encoding beyond color;
- source and synthetic-demonstration notes;
- sufficient text/background contrast.

The Markdown report must retain a textual summary and detailed table so the
decision does not depend on reading the chart image.

## Chart narrative contracts

| Figure | Central question | Required visual evidence |
|---|---|---|
| Decision summary | What is the headline result? | preferred option, value, P(best), robustness, breach U95 versus tolerance |
| Robustness profile | Why is the decision status what it is? | four component scores, weights, thresholds, readiness status |
| Alternative ranking | Which feasible option leads? | rank, value, feasibility, P(best), breach status |
| Constraint risk | Which options pass the risk boundary? | observed breach, one-sided U95, tolerance line, feasible marker |
| Criterion profile | Where are the trade-offs? | fixed-scale scores, weights, preferred-option emphasis |
| Utility uncertainty | How much overlap and downside remain? | P05–P95, expected utility, CVaR10 |
| Correlation stress | How do shared shocks change P(best), tail value, and feasibility? | independent, declared, and stronger-dependence states with winner, P(best), CVaR10, and breach U95 |
| Scenario resilience | What conditions change the answer? | comparable small multiples, scenario probability, winning option |
| Weight sensitivity | Which stakeholder priorities can change the winner? | two-sided stresses, score, winner outline and marker |
| Group impacts | Where might distributional review be needed? | parity ratio, direct value, distance from parity, non-fairness caveat |

## External design benchmarks

The system applies, without copying a proprietary house style:

- the Financial Times Visual Vocabulary principle of matching visual form to
  the analytical relationship;
- the World Bank emphasis on chart-purpose fit, strategic color, direct
  labeling, hierarchy, and source context;
- the U.S. Web Design System principles of one central idea, controlled color,
  and equivalent accessible text;
- the narrative sequencing, small multiples, and direct annotation visible in
  leading consulting reports.

These are design principles only. The generated findings and evidence remain
those in the case file and `decision-results.json`.
