# R8 · Spatial Equity and Service-Hub Planning

**Portfolio role:** urban planning, spatial policy, public analytics, and location allocation  
**Decision boundary:** pre-feasibility screening for local review—not a siting or funding decision.

## Analytical question

How spatially clustered is tract-level need in Massachusetts, and how do poverty-, transit-, and composite-priority strategies compare when selecting five candidate service hubs?

## Evidence and methods

- Official 2019–2023 ACS five-year tract tables and 2023 Census Gazetteer points.
- Reproducible poverty, transit, and rent-to-income proxy definitions.
- Five-nearest-neighbor Moran’s I.
- Greedy maximum coverage under a common hub count and ten-kilometre radius.
- Tract bootstrap for strategy metrics.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

Inspect the [technical report](outputs/report.md), [map and figures](outputs/figures), [results](outputs/results.json), [value judgments](config.json), and [source manifest](source-manifest.json).

## Transferable methods

The case demonstrates rate construction, spatial clustering, need-weighted
location allocation, and sensitivity to radius, weights, uncertainty, and
geographic aggregation.

## Non-negotiable limitation

Centroid straight-line distances are not travel times; ACS estimates have sampling error; weights express unelicited value judgments. Local network, capacity, parcel, and stakeholder evidence is required.
