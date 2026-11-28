# Maintaining Earliest Arrival Routes Across Timetable Revisions

Can a router repair a revised timetable and still return exactly the same earliest arrivals as rebuilding?

Apply calendar and date exceptions for one Friday to ten consecutive archived feeds. Extract trunk rail, selected bus lines and shuttles. A timetable connection scan handles remaining on board, boarding restrictions, transfer waiting, and times beyond midnight. Retain unaltered time prefixes and compare with full invalidation and a fresh oracle for all reachable stops.

Across 10 timetable versions, all 300 route-query results matched a full scan. Revisions changed 4,223 destination arrival labels; checkpoint repair visited 1,969,278 connections versus 8,903,454 for full recomputation.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
