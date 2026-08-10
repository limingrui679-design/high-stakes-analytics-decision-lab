# Commercial Real Estate Diligence Decision Product

## Decision question

Which borough/property-type segments have enough public transaction evidence to
justify property-level diligence, and how does the income hurdle change under
alternative financing-rate scenarios?

## Adaptive analytical route

1. **Descriptive:** summarize transaction activity, pricing, and dispersion.
2. **Diagnostic:** identify thin segments and sensitivity to filtering.
3. **Predictive:** no property-price forecast is claimed without lease and condition data.
4. **Decision:** gate segments into further diligence and expose financing evidence needs.

The output is a market screen. It is not an appraisal, acquisition
recommendation, planning approval, or causal evaluation of regeneration.

## Run

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

## Evidence products

- `outputs/report.md`
- `outputs/results.json`
- `outputs/evidence-table.csv`
- `outputs/figures/`
- `outputs/decision/report/decision-report.md`

## Privacy and source boundary

Street addresses are excluded from the processed case. Public borough,
neighborhood, class, area, sale, and approximate geography fields are retained
only to support aggregate transaction and diligence analysis.
