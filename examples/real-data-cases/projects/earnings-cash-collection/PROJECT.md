# When Reported Earnings Outrun Cash Collections

When earnings outrun collections, do receivables and inventory changes improve next-year cash-flow forecasts?

Use a preselected set of 24 nonfinancial issuers. Retain filing dates and accessions, identify first original 10-K observations, and preserve later comparisons and amendments separately. Align annual income and CFO with point-in-time balances. Compare earnings/CFO persistence and a regularized working-capital decomposition using only matured prior labels. Include an issuer-held-out fit, annual falsification and a residual-income valuation sensitivity anchored to book value.

Across 89 out-of-time company-year forecasts, next-year operating-cash-flow MAE was 3.08% of opening assets for cash persistence and 3.07% for the accrual model.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
