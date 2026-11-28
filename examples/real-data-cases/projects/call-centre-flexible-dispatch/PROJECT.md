# When Should a Call Centre Reallocate Staff After a Demand Shock?

When, within a fixed staffing budget, should a manager release temporary service capacity?

Estimate censored patience and service by call type from January–July. Select base staffing against both waiting and abandonment in August–September. Replay October–December arrivals under fixed, queue-triggered and receding-horizon dispatch. Calls already in service continue after a flexible staffing interval ends.

Across 65 held-out mornings, mean simulated abandonment was 17.23% with a fixed reserve and 18.48% under receding-horizon dispatch. Observed abandonment averaged 13.91%.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
