# R6A · Treasury Yield-Curve Portfolio Risk Engineering

**Portfolio role:** financial analytics, FinTech, risk management, and decision analysis  
**Decision boundary:** historical risk-engineering demonstration—not investment advice, a tradable backtest, or a return forecast.

## Analytical question

How do hypothetical duration profiles trade historical carry against volatility, expected shortfall, worst-day loss, and drawdown across the 2020–2025 Treasury yield environment?

## Evidence and methods

- Official U.S. Treasury daily par-yield curves, 1,500 business-day observations.
- First-order duration approximation with assumptions registered separately from source facts.
- Historical VaR, expected shortfall, drawdown, rolling 250-day VaR, Kupiec
  coverage, and Christoffersen exceedance-independence diagnostics.
- Dated shared shocks across portfolios, 5/20/60-day block sensitivity, and
  explicit 2020, 2022, and 2023–2025 regime comparisons.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

Review the [technical report](outputs/report.md), [risk results](outputs/results.json), [duration assumptions](config.json), and [source manifest](source-manifest.json).

## Transferable methods

The case demonstrates transparent duration-based return construction,
historical VaR and expected shortfall, rolling coverage and independence
backtests, regime analysis, and dependence-preserving block sensitivity.

## Non-negotiable limitation

The approximation omits convexity, security selection, implementation cost, financing, tax, and investability. All performance language remains historical.
