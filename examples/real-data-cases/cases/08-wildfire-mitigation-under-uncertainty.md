# 08 · Wildfire Mitigation Evidence Allocation Under Uncertainty

**Technical summary.** No fires-prevented or acres-prevented estimate; mitigation action blocked pending effectiveness and feasibility evidence.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/wildfire-mitigation-under-uncertainty/outputs/report.md)
- [Review the project design](../projects/wildfire-mitigation-under-uncertainty/PROJECT.md)
- [Inspect the source manifest](../projects/wildfire-mitigation-under-uncertainty/source-manifest.json)
- [Inspect the machine-readable results](../projects/wildfire-mitigation-under-uncertainty/outputs/results.json)

![Representative evidence figure for Wildfire Mitigation Evidence Allocation Under Uncertainty](../figures/08-wildfire-mitigation-under-uncertainty.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Decision Analysis |
| Adaptive route | descriptive → diagnostic → decision |
| Analytical question | Which exposure-weighted evidence-collection allocation is least fragile across historical, recent, and tail-fire scenarios? |
| Prepared rows | 8,892 |
| Valid terminal output | evidence request before mitigation allocation |

## Evidence-backed findings

- **Valid mapped perimeters:** 8,892
- **90th-percentile perimeter size:** 1,648 acres
- **Lowest-regret proxy allocation:** recent acres
- **Terminal status:** request effectiveness and feasibility evidence

## Methods selected for this case

- Observed exposure scenarios
- allocation alignment
- minimax regret
- and evidence-request terminal gate.

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

No fires-prevented or acres-prevented estimate; mitigation action blocked pending effectiveness and feasibility evidence.

## Source identity

- **Dataset:** [Wildfire Mitigation Evidence Allocation Under Uncertainty](https://www.arcgis.com/home/item.html?id=c3c10388e3b24cec8a954ba10458039d)
- **Publisher:** California Department of Forestry and Fire Protection
- **Version:** California Historic Fire Perimeters feature service, filtered to 2000-2025
- **Accessed:** 2026-08-10
- **License:** California open data / public information
- **Analytical grain:** one fire-perimeter record

### Reviewed source-snapshot hashes

- `calfire-fire-perimeters-2000-2025.csv` — `03ac2df8ca6004dc4ce83cddcf8671ed4192597b198fb25a74bd873c881e1a75`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
