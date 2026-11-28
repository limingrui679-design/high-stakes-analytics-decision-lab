# Counterexamples or Direct Corrections for Novice Programmers?

Should a beginner receive an elicited counterexample or a direct correction after a repeatable misconception?

Use the 2019 challenge authors' public predictions and real first-correct, any-hint and attempt records. Hold out entire learners and mature earlier learners before fitting. Independently inspect real duplicate-removal attempts in the Refactory corpus. Build two runnable feedback designs and specify equal exposure, a new transfer item and a prospective learner-randomized evaluation.

The authors' public file contained 729 learner–problem records. On 584 matched out-of-time learner-held-out observations, first-correct F1 was 0.676 for the past-only model. In the independent code archive, 27 incorrect programs removed from the list being traversed.

[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)

## Reproduce

From this directory run the commands below with Python 3.11 or newer.

~~~sh
python prepare_data.py
python analyze.py
python build_decision_case.py
~~~

To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).
