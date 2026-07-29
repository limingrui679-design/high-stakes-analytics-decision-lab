# Editorial Evidence System

Use this visual system for every reader-facing analytical or decision report.
The goal is not decoration. The goal is to make the question, comparison,
uncertainty, claim boundary, and next action understandable before the reader
opens the underlying JSON or code.

## Design premise

High-quality corporate research combines three qualities:

1. **Editorial hierarchy.** A reader can scan the title, subtitle, key number,
   focal mark, annotation, and source in that order.
2. **Analytical honesty.** The chart family, denominator, scale, uncertainty,
   benchmark, and validation boundary match the claim.
3. **Visual authorship.** Typography, spacing, direct labels, domain accents,
   and report-level composition feel intentional rather than like plotting
   library defaults.

This system draws general lessons from public research published by
[McKinsey Global Publishing](https://www.mckinsey.com/featured-insights/year-in-review/year-in-charts),
[McKinsey Global Institute](https://www.mckinsey.com/mgi/our-research/mckinsey-global-institute-2025-in-charts),
[BCG](https://www.bcg.com/publications/2026/global-wealth-growth-in-an-era-of-reordering),
[IBM Institute for Business Value](https://www.ibm.com/thought-leadership/institute-business-value/en-us/report/business-trends-2025),
[Accenture Research](https://www.accenture.com/us-en/insights/pulse-of-change-january-2025),
and
[Deloitte CFO Insights](https://www2.deloitte.com/content/dam/Deloitte/us/Documents/finance/us-cfo-insights-data-visualization.pdf).
It does not reproduce their brand assets, layouts, or proprietary artwork.

## Two intelligence products

The **Evidence Intelligence Report** is the primary evidence product. The
**Decision Intelligence Brief** is a conditional downstream product.

| Layer | Required visual job | Typical figures |
|---|---|---|
| Evidence Intelligence Report | Establish what was measured, what changed, how reliable it is, and what the evidence cannot establish | Trend, comparison, distribution, relationship, calibration, interval, heatmap, spatial view, sensitivity |
| Decision Intelligence Brief | Show the evidence gates, feasible alternatives, constraints, downside, robustness, terminal status, and reversal conditions | Decision scorecard, alternative ranking, risk boundary, scenario matrix, tail distribution, weight sensitivity |

A Decision Intelligence Brief never replaces the Evidence Intelligence
Report. Link back to the evidence report and analytical results from every
decision brief.

## Chart contract

Before drawing a figure, record:

- analytical question;
- one-sentence supported takeaway;
- observation grain, cohort, period, denominator, and units;
- chart family and reason;
- focal mark and comparison or benchmark;
- uncertainty or validation element;
- palette policy and non-color distinction;
- source and claim boundary;
- report section and adjacent interpretation.

If any item is unknown, the chart is not ready to publish.

## Editorial frame

Every shipped SVG uses:

- a deep-navy title band with a domain accent;
- a neutral chart surface with generous margins;
- one descriptive title and one contextual subtitle;
- direct values, endpoints, or interval labels where they improve reading;
- a quiet source footer and a visible claim-boundary cue;
- accessible `<title>` and `<desc>` elements;
- one font family and tabular numerals for values.

Decorative geometry may establish identity in the title band or outer canvas.
It must never obscure marks, encode a variable, or imply extra precision.

## Domain themes

Use one root accent plus neutrals for a single-series chart. Use no more than
five roots when category identity is the point.

| Domain | Root accent | Supporting tint |
|---|---|---|
| Health and population | teal | pale teal |
| AI and model validation | blue | pale blue |
| Behavior and policy | gold | pale gold |
| Operations and systems | olive | pale olive |
| Finance and risk | violet | pale violet |
| Spatial planning | coral | pale coral |
| Marketing | magenta | pale magenta |

Do not use red and green as the only success/failure distinction. Pair every
state color with direct text, shape, line style, or ordering.

## Chart-family patterns

### Trend

- Use eight or more ordered observations when possible.
- Highlight one focal series; keep comparators visually quieter.
- Mark endpoints and important discontinuities.
- Use small multiples when more than four lines compete.
- Show forecast, baseline, or target with a different line style.

### Comparison and ranking

- Sort when order has no semantic meaning.
- Use horizontal bars for long labels.
- Add an explicit benchmark line when the comparison depends on a target.
- Label values directly; avoid a redundant legend.
- Highlight the decision-relevant item without hiding the rest.

### Distribution and uncertainty

- Use intervals, histograms, box plots, or tail views based on the question.
- Draw the null, tolerance, or policy threshold when it governs interpretation.
- Pair the point estimate with the interval rather than presenting precision
  as a single number.
- State the resampling or interval basis in the subtitle or nearby narrative.

### Relationship

- Use one observation grain throughout.
- Retain sample size or volume context.
- Label only decision-relevant points or outliers.
- Do not draw a causal arrow from an observational association.

### Matrix, cohort, and spatial views

- Use a perceptually ordered scale and print values when cells are large enough.
- Include a legend that says what dark and light mean.
- For maps, state whether marks are points, polygons, or approximations.
- Never let color intensity stand in for an unstated quality judgment.

### Decision and sensitivity

- Put the modeled decision and terminal status first.
- Show the constraint or risk boundary explicitly.
- Separate expected value, downside, feasibility, and robustness.
- Use the same sampled shock across alternatives when the case declares shared
  exposure.
- Label robustness as model behavior, not real-world confidence.

## Report composition

For every important figure:

1. Start the section with the supported takeaway.
2. State how to read the figure.
3. Render the figure at a readable width.
4. Explain the implication and the caveat immediately after it.
5. Preserve the source and chart contract in the chart map.

Use large-number cards only for true headline measures. Do not convert every
metric into a card. Vary chart families when sections ask different questions.

## Prohibited shortcuts

Do not:

- use plotting-library defaults as a finished visual identity;
- fill every report with the same chart family;
- use gradients inside analytical marks;
- add three-dimensional bars, perspective, or decorative area that changes
  perceived magnitude;
- use a cropped axis to exaggerate ordinary bar comparisons;
- force a recommendation so the final graphic appears decisive;
- hide weak validation behind attractive styling;
- omit the Evidence Intelligence Report because a Decision Intelligence Brief
  exists.

## Final visual QA

Before release, inspect every SVG in its real Markdown context and confirm:

- the title and subtitle fit;
- labels, values, legends, and annotations do not collide or clip;
- the visual remains understandable without color;
- the scale and baseline are honest;
- the source is visible;
- the figure supports the nearby sentence;
- the Decision Intelligence Brief links back to the Evidence Intelligence
  Report;
- the README exposes both products and makes Evidence Intelligence primary.
