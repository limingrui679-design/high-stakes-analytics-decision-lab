# 15 · Spatial Equity Planning with Transit and Site-Evidence Gates

**Technical summary.** Across 1,597 analyzed tracts and 265 rapid-transit stop records, the high-poverty weighted nearest-stop distance is 40.65 km.

## Evidence products

- [Open the Evidence Intelligence Report](../projects/spatial-equity-planning/outputs/report.md)
- [Review the project design](../projects/spatial-equity-planning/PROJECT.md)
- [Inspect the source manifest](../projects/spatial-equity-planning/source-manifest.json)
- [Inspect the machine-readable results](../projects/spatial-equity-planning/outputs/results.json)
- [Open the Decision Intelligence Brief](../projects/spatial-equity-planning/outputs/decision/report/decision-report.md)

![Representative evidence figure for Spatial Equity Planning with Transit and Site-Evidence Gates](../figures/15-spatial-equity-planning.svg)

The figure is the representative visual for this case. Its interpretation is
limited by the evidence boundary stated below.

## Case route

| Field | Case-specific value |
|---|---|
| Domain | Urban Planning |
| Adaptive route | descriptive → prescriptive |
| Analytical question | Which tract-level service-hub priorities merit local review after observed rapid-transit proximity is added? |
| Prepared rows | 1,620 |
| Valid terminal output | claim-bounded decision review |

## Capability path

| Role | Capability |
|---|---|
| Primary | **Spatial equity and planning** — Connect place-based evidence, access, distribution, uncertainty and feasibility without turning a screening model into a site or policy decision. |
| Supporting | Behavior and policy evidence, Analytics to action |

### Reviewer-visible signals

- complete-case route
- missingness sensitivity
- observed transit proximity
- site evidence gate

Capability labels help readers find a relevant precedent. They do not upgrade
the evidence, permitted use, or empirical result of this case.

## Evidence-backed findings

- **Analyzed Massachusetts tracts:** 1,597
- **Composite-need complete cases:** 1,495; missing proxy: 102
- **MBTA rapid-transit stop records:** 265
- **High-poverty weighted nearest-stop distance:** 40.65 km
- **Site decision:** blocked pending land and feasibility evidence

## Methods selected for this case

- ACS need indicators
- Moran's I
- heuristic location allocation
- bootstrap sensitivity
- and nearest-MBTA-stop distance.

These methods were selected from the question, data grain, and evidence
maturity. Other cases in this gallery use different fields, checks, figures,
and endpoints.

## Interpretation boundary

No site recommendation until parcel, zoning, network, cost, and community evidence is supplied.

## Source identity

- **Dataset:** [Spatial Equity Planning with Transit and Site-Evidence Gates](https://www.census.gov/data/developers/data-sets/acs-5year/2023.html)
- **Publisher:** U.S. Census Bureau and Massachusetts Bay Transportation Authority
- **Version:** 2019-2023 ACS tract estimates, 2023 Gazetteer, and MBTA rapid-transit stops accessed 2026-08-10
- **Accessed:** 2026-08-10
- **License:** U.S. Government open data and MBTA open data
- **Analytical grain:** one Massachusetts census tract

### Reviewed source-snapshot hashes

- `acs-b01003-ma.dat` — `cdcd4d9ff65e09e8b25f8da38acf982d33b9d734758b0fa157c8211ced21886f`
- `acs-b17001-ma.dat` — `f80278da8a45a97119d5235836dd72e178d87a29aeed8a151dc67234966b8ec0`
- `acs-b19013-ma.dat` — `81447fabb88ca284fc556b5aea116cb61af6dd25e19306d894d9ecf1ad87f7ce`
- `acs-b08301-ma.dat` — `228d3906b990878f0df15f935c5acbb0443b0b07aea885929fab6491d61f30c2`
- `acs-b25064-ma.dat` — `cdfbcb46e9c5d81c0bd902d54f246a29becc31c0c8124ad838077b7337e0b2d4`
- `2023_Gaz_tracts_national.zip` — `d97f27a434fb9f7b9994ec15ea5bbe41f7b7f4c2aabb3dfe437448bf4e1bc93c`
- `mbta-rapid-transit-stops.json` — `22d2bfb9023dca4d261c149d1665e15f35d8f3e3406e947a60f34f327997ca6a`

The reviewed raw source files are bundled inside the complete project directory.
The build script verifies each file against both this case index and the
project source manifest.

## Reuse boundary

Reuse the analytical pattern, not the empirical conclusion. A new population,
time window, source version, objective, or decision owner requires a new
evidence contract and validation path.
