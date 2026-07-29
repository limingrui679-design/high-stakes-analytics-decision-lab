# 10 · Spatial Equity and Service-Hub Planning

**Technical summary.** Need is spatially clustered, and a composite allocation balances poverty, transit dependence, and housing pressure better than a single-indicator rule.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/spatial-equity-planning/outputs/report.md)
- [Review the project design](../projects/spatial-equity-planning/PROJECT.md)
- [Inspect the source manifest](../projects/spatial-equity-planning/source-manifest.json)
- [Inspect the machine-readable results](../projects/spatial-equity-planning/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/spatial-equity-planning/outputs/decision/report/decision-report.md)

![Massachusetts tract-level need and selected service hubs](../figures/10-spatial-planning.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Urban planning |
| Adaptive route | descriptive → prescriptive |
| Analytical question | Where is need spatially clustered, and how do alternative hub strategies change modeled coverage under a fixed radius and capacity? |
| Prepared rows | 1,620 |
| Analyzed rows | 1,597 |
| Valid terminal output | Planning-screen allocation with radius, weight, and geography reversal tests |

## Evidence-backed findings

- **Analyzed tracts:** 1,597
- **Poverty-rate Moran's I:** 0.491
- **Composite-plan need coverage:** 78.1%
- **High-poverty population coverage:** 65.6%

## Methods selected for this case

- ACS rate construction
- z-score composite need
- five-nearest-neighbor Moran's I
- greedy maximum coverage
- radius and weight sensitivity
- tract bootstrap

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

Straight-line centroid distance and tract aggregates are screening approximations; travel time, site feasibility, capacity, and ACS uncertainty require local review.

## Source identity

- **Dataset:** [2019–2023 ACS 5-Year Estimates and 2023 Census Gazetteer](https://www.census.gov/data/developers/data-sets/acs-5year/2023.html)
- **Publisher:** U.S. Census Bureau
- **Version:** 2019–2023 ACS 5-year estimates; 2023 Gazetteer
- **Accessed:** 2026-07-27
- **License:** U.S. Government work / Census open data
- **Analytical grain:** one Massachusetts 2020-vintage census tract

### Reviewed source-snapshot hashes

- `acs-b01003-ma.dat` — `cdcd4d9ff65e09e8b25f8da38acf982d33b9d734758b0fa157c8211ced21886f`
- `acs-b17001-ma.dat` — `f80278da8a45a97119d5235836dd72e178d87a29aeed8a151dc67234966b8ec0`
- `acs-b19013-ma.dat` — `81447fabb88ca284fc556b5aea116cb61af6dd25e19306d894d9ecf1ad87f7ce`
- `acs-b08301-ma.dat` — `228d3906b990878f0df15f935c5acbb0443b0b07aea885929fab6491d61f30c2`
- `acs-b25064-ma.dat` — `cdfbcb46e9c5d81c0bd902d54f246a29becc31c0c8124ad838077b7337e0b2d4`
- `2023_Gaz_tracts_national.zip` — `d97f27a434fb9f7b9994ec15ea5bbe41f7b7f4c2aabb3dfe437448bf4e1bc93c`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
