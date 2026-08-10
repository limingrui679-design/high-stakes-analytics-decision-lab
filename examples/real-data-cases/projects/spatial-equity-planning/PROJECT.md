# Spatial Equity Planning with Transit and Site-Evidence Gates

**Analytical question:** Which tract-level service-hub priorities merit local review after observed rapid-transit proximity is added?

**Decision boundary:** No site recommendation until parcel, zoning, network, cost, and community evidence is supplied.

## Evidence and methods

- Source: U.S. Census Bureau and Massachusetts Bay Transportation Authority — 2019-2023 ACS tract estimates, 2023 Gazetteer, and MBTA rapid-transit stops accessed 2026-08-10.
- Analytical grain: one Massachusetts census tract.
- Methods: ACS need indicators, Moran's I, heuristic location allocation, bootstrap sensitivity, and nearest-MBTA-stop distance.
- Every bundled raw or minimized source file is hash-locked in `source-manifest.json`.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

Read the [technical report](outputs/report.md), [machine-readable results](outputs/results.json), [source manifest](source-manifest.json), and [data-quality report](data/quality-report.json).

## Non-negotiable limitation

No site recommendation until parcel, zoning, network, cost, and community evidence is supplied.
