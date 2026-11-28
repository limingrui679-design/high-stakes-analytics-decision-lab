# How Much Departure Delay Can a Last-Mile Route Absorb?

How late can a dispatcher release a route while still honoring its published windows and a stated end of shift?

Select six UUID-ordered high-rated routes of 45–145 stops from each of four depots before inspecting time windows. Evaluate the driver order and two classical route-improvement searches at the same move budget. Use backward time propagation for feasible witnesses and independent relaxation bounds for the largest possible delay. Report a station held out of design and a common zone disruption.

On 24 complete published routes, window-focused relocation produced 10 nonnegative departure-delay witnesses; the recorded sequences produced 10. 14 routes remained inconclusive under the search budget.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
