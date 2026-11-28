# Where Should a Marketplace Spend Its Delivery Improvement Budget?

Should a marketplace direct an equal number of review slots to seller handoffs or to post-handoff delivery?

Separate final lateness by whether handoff met the seller timestamp. Adjust for destination and within-state delivery, shrink seller rates, and freeze priorities before each future quarter. Use only outcomes known at that decision date. Compare identical numbers of review slots, with explicit cost and effectiveness break-even.

Across 4 future quarters and 2,000 equal review slots per policy, adjusted seller targeting found 86 late deliveries following a missed handoff deadline. Carrier-focused targeting found 225 late deliveries after on-time handoff.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
