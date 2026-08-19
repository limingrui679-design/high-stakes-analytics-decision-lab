# Parameter Provenance and Approval Contract

Top-level citations are insufficient for a consequential model. Every governed
input must resolve to a parameter-level record.

## Required fields

For each parameter path, store:

| Field | Meaning |
|---|---|
| `parameter_path` | Stable JSON or analytical path |
| `label` | Reader-facing description |
| `value_or_distribution` | Exact value, bounds, values, or fitted distribution |
| `unit` | Physical, financial, temporal, or index unit |
| `uncertainty_type` | `none`, `parameter`, `process`, or `scenario` |
| `source_id` | Link to a registered source |
| `source_fact` | Exact observed fact or elicited statement |
| `transformation` | Formula or method from source fact to model input |
| `owner` | Accountable evidence owner |
| `reviewer` | Independent or domain reviewer; `not_assigned` if absent |
| `review_date` | ISO date or `null` |
| `approval_status` | Approved, provisional, rejected, or not obtained |
| `approval_scope` | Illustrative, exploratory, or operational use |
| `evidence_strength` | Observed, estimated, elicited, assumed, or policy value |
| `notes` | Known boundary or unresolved question |

## Parameter families

At minimum, expand:

- criterion weights and external scales;
- every alternative-metric distribution;
- scenario probabilities and adjustments;
- constraint thresholds;
- risk-aversion and tolerated-breach parameters;
- weight-sensitivity multipliers;
- dependence loadings and stress multipliers;
- predictive thresholds, capacity levels, calibration choices, and time splits
  used by the upstream analysis.

One source may govern a family, but the release output must still contain a
separate resolved record for every path. Family-level approval never authorizes
a stronger decision use than the source explicitly permits.

## Provenance coverage

Report both:

1. **source coverage**: governed parameter paths with a resolved source divided
   by all governed paths;
2. **decision-use approval coverage**: paths whose approval scope covers the
   declared use divided by all governed paths.

Coverage is a traceability measure, not evidence quality. A complete register
of weak assumptions remains weak evidence.

## Missing approval

Do not fill a missing reviewer with the model author. Use `not_assigned`,
`not_obtained`, and `null` explicitly. A missing domain review downgrades the
decision-use status; it does not block an honestly labeled exploratory study.
