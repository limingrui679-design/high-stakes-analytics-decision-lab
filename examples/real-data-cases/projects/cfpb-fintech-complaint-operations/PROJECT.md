# R6C · Privacy-Preserving Complaint Monitoring and Negative Model Validation

**Skill coverage:** privacy-preserving administrative-data analysis, rare-event validation, model-risk gates, and time-aware monitoring  
**Decision boundary:** determine whether a public-data ranking model deserves further consideration—not rank consumers, firms, jurisdictions, or complaints.

## Analytical question

Do intake-time public fields provide reproducible later-period ranking gain for untimely responses, or should the ranking model be rejected while retaining the privacy and monitoring design?

## Evidence and methods

- Official CFPB Consumer Complaint Database, 13,534 closed-period 2022 complaints for money transfer, virtual currency, or money service.
- Privacy-minimized snapshot that excludes narratives, company names, ZIP codes, tags, and public-response text.
- Calendar train/validation/test split; validation-set capacity selection; untouched November–December evaluation.
- Rare-outcome discrimination, calibration, cumulative gain, capacity lift, seven-day block bootstrap, and label-permutation null benchmarking.
- Explicit deployment gates that can return a negative result; no forced “best capacity” when ranking gain is negligible.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

Read the [technical report](outputs/report.md), [machine-readable results](outputs/results.json), [model-validation decision](outputs/decision-analysis.json), and [privacy receipt](data/privacy-receipt.json).

## Transferable methods

The case demonstrates that a rigorous model study can end in non-deployment. Its contribution is the separation of privacy engineering, temporal validation, statistical signal, and operational usefulness.

## Non-negotiable limitation

Complaint publication and response outcomes are selective administrative records. The observed model has weak discrimination and essentially no gain at the smallest review capacity; it must not be presented as an effective triage system.
