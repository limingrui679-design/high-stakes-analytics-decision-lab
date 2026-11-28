# How Much Inspection Capacity Should a City Reserve for Random Audits?

How much of a city's finite inspection capacity should be reserved for random exploration?

Reconstruct dated permit eligibility and use only earlier restaurant records for classification, risk and geography. Compare calendar ordering, risk prioritization and stratified random exploration under one slot budget. Evaluate reordering on historically inspected premises; report worst/best bounds for missing outcomes on the full eligible roster. Supply exact inclusion probabilities for a future audit.

The 25% exploration policy allocated 960 slots over 8 quarters. Historical results were observable for 197 selections, giving full-roster critical-finding bounds of 4.9% to 84.4%.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
