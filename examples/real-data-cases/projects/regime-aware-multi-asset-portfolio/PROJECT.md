# Regime-Aware Multi-Asset Portfolio Construction

## Decision question

Can a transparent, bounded, walk-forward allocation improve the historical
risk–return trade-off relative to equal-weight and 60/40 references without
breaking turnover, tail-risk, or evidence constraints?

## Adaptive analytical route

1. **Descriptive:** align five adjusted-price histories and show common regimes.
2. **Diagnostic:** compare volatility, turnover, drawdown, tail loss, and stress periods.
3. **Predictive:** use trailing volatility only as a forward allocation input.
4. **Decision:** compare bounded portfolios under shared market shocks and explicit costs.

The route deliberately stops at a research-only paper portfolio. It does not
produce financial advice, a security recommendation, or a claim of future
outperformance.

## Run

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

Use `python3 download_data.py --refresh` only to test whether the upstream
reviewed snapshot changed. A changed hash requires source and result review
before the manifest is updated.

## Evidence products

- `outputs/report.md`
- `outputs/results.json`
- `outputs/evidence-table.csv`
- `outputs/figures/`
- `outputs/decision/report/decision-report.md`

## Claim boundary

The market-data provider's terms apply independently of this repository's code
license. Adjusted prices omit executable quotes, market impact, investor taxes,
liabilities, capacity, and future regimes.
