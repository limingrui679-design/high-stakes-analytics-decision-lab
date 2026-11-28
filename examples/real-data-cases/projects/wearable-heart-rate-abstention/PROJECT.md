# When Should a Wrist Monitor Withhold a Heart Rate Reading?

When can a wrist monitor's quality gate reduce error without leaving users without readings for too long?

Estimate wrist rate from the strongest physiological-frequency spectral peak. Compare movement-only gating to spectral concentration penalized by movement. Tune on complete DaLiA participants, freeze a threshold and test on unseen DaLiA people and the separate WESAD cohort. Check equivalent coverage, per-person and per-activity error, rejected ECG windows, and sustained gaps.

With the DaLiA threshold frozen, WESAD retained 85.2% of 5,544 eligible windows. Subject-averaged absolute error among reported ECG-readable windows was 6.83 bpm.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
