# Executable Method Demonstrations

These three synthetic demonstrations show how upstream evidence can be
estimated, validated, or optimized before entering the decision engine.

| Module | Input | Human-readable output | Machine-readable output |
|---|---|---|---|
| Statistical evidence | `examples/clinical-evidence-design/study-data.csv` | [Evidence report](evidence-analysis/evidence-report.md) | [Evidence JSON](evidence-analysis/evidence-results.json) |
| Prediction validation | `examples/ai-model-validation/predictions.csv` | [Prediction report](prediction-validation/prediction-report.md) | [Prediction JSON](prediction-validation/prediction-results.json) |
| Resource optimization | `examples/health-resource-allocation/optimization-config.json` | [Optimization report](resource-optimization/optimization-report.md) | [Optimization JSON](resource-optimization/optimization-results.json) |

Every module also creates a directly labeled SVG. The input data and
coefficients are synthetic; the reports demonstrate method and communication
structure, not real empirical findings.
