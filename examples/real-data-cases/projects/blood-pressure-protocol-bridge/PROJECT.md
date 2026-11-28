# When a Blood Pressure Survey Changes Its Measurement Protocol

How much does replacing a blood-pressure measurement protocol change a survey threshold count?

Pair each adult's first three available-position readings (at least two per protocol). Compare the signed differences and both threshold directions using MEC weights and stratified PSU linearization. Fit pooled and partially pooled age-band offsets on other PSUs only.

Across 4,614 paired adults, the survey-weighted automatic-minus-manual mean was -1.50 mmHg. At 130 mmHg, 5.32% moved above and 8.15% moved below the cutoff.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
