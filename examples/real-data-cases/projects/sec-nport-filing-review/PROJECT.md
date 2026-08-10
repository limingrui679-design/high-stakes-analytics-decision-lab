# SEC N-PORT Liquidity and Crowding Filing Review

**Analytical question:** Which transparent concentration, liquidity, and redemption indicators should trigger targeted filing review?

**Decision boundary:** Filing review only; no expected-return, suitability, fund-quality, or investment recommendation.

## Evidence and methods

- Source: U.S. Securities and Exchange Commission — Form N-PORT Data Set 2025 Q4, minimized to fund-level review indicators.
- Analytical grain: one fund filing snapshot.
- Methods: Filing extraction, percentile indicators, transparent composite score, and review-capacity trade-offs.
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

Filing review only; no expected-return, suitability, fund-quality, or investment recommendation.
