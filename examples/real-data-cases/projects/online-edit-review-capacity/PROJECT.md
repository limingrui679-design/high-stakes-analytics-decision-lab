# The Last Review Slot in an Online Queue

When should an online reviewer spend the last daily slot on the current edit?

Replay real UTC arrivals in order. Use anonymized arrival-visible edit properties to estimate seven-day identity-revert risk on matured history. Compare a fixed threshold, time quota and marginal inventory-value policy with two hindsight bounds. Use the same finite daily capacity and examine burst days separately.

Across 366 held-out publication days, the inventory-value policy captured 308 seven-day identity reverts, versus 287 with a fixed threshold and 1095 for an outcome-aware upper bound.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
