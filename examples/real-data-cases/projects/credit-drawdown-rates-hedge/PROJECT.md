# Cut Credit Exposure or Hedge Rates During a Corporate Bond Drawdown?

During a credit drawdown, how does reducing corporate exposure compare with matching its expected rate sensitivity using a Treasury hedge?

Form weekly total returns from NAV plus distributions on ex-dates. At each week, use prior returns to estimate rate-factor betas and a lagged drawdown trigger. Compare static credit, a partial move to bills, and a self-financing Treasury overlay at similar expected rate sensitivity. Include costs, turnover, peak-to-trough loss and crisis subperiods.

Over 1097 held-out weeks, the rule triggered 143 times. The modeled net maximum drawdown was -17.02% after cutting credit and -19.21% under the matched-rate hedge.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
