# Which State Unemployment Claims Alerts Survive the Next Release?

Which state-level claims alerts survive the switch from first publication to claimant-residence reporting?

Extract consecutive dated weekly releases and verify each printed state change. Rank anomalies after state-specific scale and seasonality adjustment. Compare a seasonal prior, the raw release and a shrunk historical revision adjustment against the residence-based top-K in the next publication. Hold out late dates and respect label publication.

Across 68 held-out weekly releases at 5 review slots, 83.2% of first-release alerts and 89.7% of revision-adjusted alerts appeared in the next release's residence-based list.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
