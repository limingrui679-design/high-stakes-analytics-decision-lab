# How Reliable Are Model Comparisons With Overlapping Evaluation Windows?

How wide should a forecast-comparison interval be when adjacent scores reuse six days of observations?

For each full UTC date compute the paired difference in daily demand-normalized absolute errors. Average seven consecutive calendar dates; join six authorities by date. Compare independent, non-overlapping weekly, Bartlett HAC and moving-block intervals. In a separate controlled experiment run the identical procedures against a known population mean. Read both scores against a common reported-load screen; preserve the unfiltered replay and identify the influential dates.

Across 1,520 shared dates after the source-quality screen and 6 balancing authorities, the day-ahead minus seasonal-naive score averaged -5.14 percentage points. The 95% HAC interval spanned 0.943 points versus 0.304 under independence.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
