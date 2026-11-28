# Knowing When to Fall Back After a Drive Fleet Changes

When monitoring signals disappear after a fleet change, is switching to an interpretable rule worth the lost warnings?

Keep the complete fleet's observation calendar. Train on earlier, disjoint serials and exclude one entire model. Evaluate fifteen daily alerts on unseen serials or the excluded model. Keep every observed candidate at allocation, then report unobservable follow-up separately; differentiate missing from zero. Compare a fixed pending-sector rule, a frozen empirical score and a fallback triggered by unavailable indicators or matured poor precision.

With 15 daily review slots across 139 held-out dates, event recall was 21.8% for the pending-sector rule and 9.8% for monitored fallback across 459 observable failures.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
