# R1 · Heart-Failure Follow-up Risk and Survival

**Portfolio role:** population health, biostatistics, and health-data science  
**Decision boundary:** choose a triage rule for prospective validation—not a clinical treatment or deployment rule.

## Analytical question

What can an observational follow-up cohort establish about survival, subgroup risk, and the workload–capture trade-off of candidate follow-up protocols?

## Evidence and methods

- UCI Heart Failure Clinical Records, 299 patient records, CC BY 4.0.
- Kaplan–Meier survival estimates and patient-level bootstrap intervals.
- Multivariable Cox proportional-hazards model with Breslow ties, hazard-ratio
  intervals, discrimination, 180-day calibration, and proportional-hazards
  diagnostics.
- Observational risk differences for an explicitly labeled exploratory threshold.
- Three triage protocols compared on observed event capture, workload, and recorded-sex selection gap.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

The first command verifies committed source hashes by default; `--refresh` attempts a guarded re-download. Read the [technical report](outputs/report.md), [results](outputs/results.json), [data dictionary](data/data-dictionary.json), and [source manifest](source-manifest.json).

## Transferable methods

The case demonstrates censoring-aware estimation, multivariable survival
modeling, calibration, resampling uncertainty, and the separation of observed
risk from treatment or operational authorization.

## Non-negotiable limitation

The cohort is small and observational. Hazard associations are not treatment
effects. The rule comparison requires prospective validation, clinical review,
and local governance before any real use.
