# R7 · Public AI Inventory Disclosure and Measurement Readiness

**Skill coverage:** public-data measurement, missingness analysis, responsible AI, and technology-policy evidence design  
**Decision boundary:** assess what an external reviewer can observe—not certify governance capability, compliance, safety, ethics, or control effectiveness.

## Analytical question

Which information is and is not observable in the public DOT AI inventory, how does disclosure vary across information families and lifecycle stages, and which governance questions remain unmeasurable from this source?

## Evidence and methods

- Official U.S. DOT AI Use Case Inventory, 70 public records in the reviewed snapshot, U.S. government work.
- Completeness for every public field, not a hand-picked subset.
- Six transparent information families, field-status classification, and stage-by-family disclosure patterns.
- A disclosure-readiness measure explicitly limited to external observability.
- A minimum evidence-request schema that is analyst-designed rather than inferred from the inventory.
- Explicit suppression of the public contact email before processed data is written.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

The last command intentionally creates no action-ranking case: public completeness is insufficient for a defensible enforcement, procurement, deployment, or maturity decision. See the [report](outputs/report.md), [results](outputs/results.json), [privacy rule](config.json), and [source manifest](source-manifest.json).

## Transferable methods

The case demonstrates how to convert a negative finding into a defensible measurement result: enumerate the observable schema, quantify missingness, preserve a claim boundary, and specify the additional evidence required before stronger evaluation.

## Non-negotiable limitation

Blank fields are disclosure signals only. They are never proof that controls are absent, ineffective, unethical, unsafe, or noncompliant.
