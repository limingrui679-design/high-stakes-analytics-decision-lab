# Reporting Standard

## Required order

1. Decision and owner
2. Recommendation or no-decision finding
3. Decision status and robustness decomposition
4. Ranked alternatives
5. Why the leading option wins
6. Criterion-level uncertainty and scale clipping
7. Scenario resilience
8. Constraint-level diagnostics
9. Group impacts
10. Two-sided weight sensitivity
11. Evidence provenance, permitted use, and limitations
12. Next evidence to collect

## Visual evidence

Use the generated SVG figures as the primary evidence path and keep exact tables
in the collapsed numerical appendix. Place an explanatory paragraph immediately
before or after every figure. State the takeaway, how to read the chart, and the
decision implication or caveat.

Use neutral chart titles. Put findings in surrounding narrative rather than in
the chart title. Keep direct numeric labels so charts remain interpretable
without color, and keep absolute outcomes alongside group parity ratios.

## Language

Use calibrated wording:

- Say “is estimated to” for modeled outcomes.
- Say “is associated with” for observational relationships.
- Say “caused” only when a defensible causal design supports it.
- Say “preferred under the stated assumptions and weights,” not “objectively best.”
- Say “modeled probability,” not “confidence,” for Monte Carlo frequencies.
- Say “illustrative preference” for synthetic evidence, not “recommendation.”
- Say “robustness score,” not “confidence score.”
- Define P(best) as a comparison among decision-feasible alternatives.
- Say “zero observed breaches,” never “zero risk.” Add the event count,
  one-sided 95% upper bound, and declared-support status.

## Decision-ready threshold

Issue no recommendation when:

- every alternative exceeds the allowed constraint-violation rate;
- the ranking changes under nearly every plausible weight stress;
- key alternatives are missing;
- the evidence source or population is materially mismatched;
- a critical harm is omitted because it is hard to quantify.

## Reproducibility

Always record:

- case-file hash;
- engine version;
- random seed;
- simulation count;
- timestamp;
- evidence labels and limitations.
- constraint event counts, one-sided 95% upper bounds, and support diagnostics.

Keep the machine-readable result beside the human-readable brief.
