# Wildfire Mitigation Evidence Allocation Under Uncertainty

**Analytical question:** Which exposure-weighted evidence-collection allocation is least fragile across historical, recent, and tail-fire scenarios?

**Decision boundary:** No fires-prevented or acres-prevented estimate; mitigation action blocked pending effectiveness and feasibility evidence.

## Evidence and methods

- Source: California Department of Forestry and Fire Protection — California Historic Fire Perimeters feature service, filtered to 2000-2025.
- Analytical grain: one fire-perimeter record.
- Methods: Observed exposure scenarios, allocation alignment, minimax regret, and evidence-request terminal gate.
- Every bundled raw or minimized source file is hash-locked in `source-manifest.json`.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

Read the [technical report](outputs/report.md), [machine-readable results](outputs/results.json), [source manifest](source-manifest.json), and [data-quality report](data/quality-report.json).

## Non-negotiable limitation

No fires-prevented or acres-prevented estimate; mitigation action blocked pending effectiveness and feasibility evidence.
