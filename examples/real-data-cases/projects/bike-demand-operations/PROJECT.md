# R4 · Bike-Demand Forecasting and Robust Service Allocation

**Portfolio role:** operations research, systems engineering, forecasting, and prescriptive analytics  
**Decision boundary:** compare a hypothetical time-block allocation for a pilot—not operate a bike-share system.

## Analytical question

How much demand structure is predictable out of time, and how should a fixed pool of service resources be distributed across six-hour blocks under ordinary and wet-day demand?

## Evidence and methods

- UCI Bike Sharing hour-level data, 17,379 system-hours, CC BY 4.0.
- Time-respecting train on 2011 and test on 2012.
- Forecast benchmark with out-of-time error metrics.
- Exhaustive evaluation of all 6,545 feasible integer allocations under a
  fixed budget and minimum-coverage constraint.
- Held-out Pareto frontier, binding constraints, 38–42-unit shadow-value
  sensitivity, and a perfect-information upper bound.
- Shared-day bootstrap and adverse-weather comparison.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

See the [technical report](outputs/report.md), [optimization results](outputs/results.json), [scenario parameters](config.json), and [decision-case input](outputs/decision-case.json).

## Transferable methods

The case demonstrates an out-of-time forecast handoff into exhaustive feasible
allocation, binding-constraint analysis, Pareto screening, shadow values,
perfect-information bounds, and dependent day resampling.

## Non-negotiable limitation

System totals omit station imbalance, routing, labor, service time, and causal effects. Resource units are explicit hypothetical scalers.
