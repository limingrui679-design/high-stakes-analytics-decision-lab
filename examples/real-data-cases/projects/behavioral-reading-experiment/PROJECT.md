# R2 · Small-Sample Repeated-Measures Inference

**Portfolio role:** advanced statistics, behavioral science, and experimental reasoning  
**Decision boundary:** prioritize a protocol for a larger preregistered validation study—not diagnose readers or infer educational outcomes.

## Analytical question

How does fixation duration change within participant between meaningful and pseudoword passages, and which measurement protocol balances group separation, stability, and burden?

## Evidence and methods

- Harvard Dataverse study, 57 paired participant records, V1, CC0.
- Participant-level paired contrasts for fixation duration, fixation count, and
  regression count with bootstrap confidence intervals.
- Sign-flip inference with Holm multiplicity adjustment; between-group
  randomization-style permutation.
- Counterbalancing, order-by-condition, attrition, and minimum-detectable-effect
  sensitivity.
- Protocol comparison retaining measurement burden and stability.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

Start with the [technical report](outputs/report.md), then inspect [machine-readable results](outputs/results.json), [parameter register](config.json), and [source manifest](source-manifest.json).

## Transferable methods

The case demonstrates within-participant estimands, randomization-style
inference, multiplicity control, order sensitivity, and the separation of
measurement validity from downstream impact.

## Non-negotiable limitation

The file is small and the exercise is not an intervention trial. Any diagnostic, causal, or policy-outcome interpretation would exceed the evidence.
