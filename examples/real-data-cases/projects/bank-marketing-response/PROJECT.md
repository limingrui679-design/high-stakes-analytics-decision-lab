# R5 · Bank Marketing Response and Capacity Planning

**Portfolio role:** business analytics, marketing analytics, statistics, and decision analysis  
**Decision boundary:** compare which records to review under a fixed contact capacity—not claim causal campaign lift, customer value, or profitability.

## Analytical question

Can pre-contact information improve held-out response concentration, and how stable is that improvement when campaign-period dependence and capacity constraints are respected?

## Evidence and methods

- UCI Bank Marketing, 41,188 contacts from Portuguese bank direct-marketing campaigns, CC BY 4.0.
- Source-order train/validation/test split; the final 20% remains untouched until evaluation.
- Mixed numerical/categorical probabilistic classifier with validation-set threshold selection.
- Calibration, lift, subgroup error checks, adjacent-row block bootstrap, and capacity sensitivity.
- Explicit leakage control: post-contact call duration is excluded.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

Read the [technical report](outputs/report.md), [machine-readable results](outputs/results.json), and [decision analysis](outputs/decision-analysis.json).

## Transferable methods

The case demonstrates leakage control, chronological validation with an
imperfect time proxy, probability calibration, shared-block uncertainty, and
the difference between response prediction and causal campaign lift.

## Non-negotiable limitation

The observational campaign records support response prediction, not an estimate of incremental treatment effect. A randomized campaign test would be required for lift or ROI claims.
