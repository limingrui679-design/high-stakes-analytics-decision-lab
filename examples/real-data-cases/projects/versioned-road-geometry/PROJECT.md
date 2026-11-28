# Consistent Road Geometry During Interrupted Map Updates

Can an interrupted map update publish mutually consistent node positions and road geometry?

Start at snapshot sequence 4897, replay sequences 4898–4926, and compare geometry at every version with a full rebuild. Track backward node-to-way dependencies and publish versioned geometry through an atomic SQLite transaction. Independently verify the terminal state against the 1 October publisher extract. Exercise replay, skipped sequence, interrupted commit and reopening.

Across 29 consecutive real map releases, dependency-aware repair matched every full rebuild and the next independent snapshot (3,655 highway geometries). Updating only revised ways missed 1 geometry-version discrepancy.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
