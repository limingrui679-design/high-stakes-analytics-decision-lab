#!/usr/bin/env python3
"""Public-disclosure and spatial-planning analysis modules."""

from __future__ import annotations

from portfolio_core import *

GOVERNANCE_FIELDS = [
    "Predeployment Testing Indicator",
    "AI Impact Assessment Indicator",
    "Independent Review Indicator",
    "Ongoing Monitoring Indicator",
    "Operator Training Indicator",
    "Fail Safe Indicator",
    "Appeal Process Indicator",
]


def _reported_yes(value: str) -> bool:
    return value.strip().casefold() in {"yes", "true", "completed", "in place"}


def analyze_ai_governance(project_root: Path) -> dict[str, Any]:
    rows = read_csv(project_root / "data/processed/analysis.csv")
    stages = Counter(row["Development Stage"] or "Unreported" for row in rows)
    high_impact = Counter(row["High Impact Indicator"] or "Unreported" for row in rows)
    all_fields = list(rows[0])
    information_families = {
        "identity and ownership": [
            "Use Case Identifier",
            "Use Case Name",
            "Agency",
            "Bureau",
        ],
        "lifecycle and operations": [
            "Development Stage",
            "Operation Date",
            "Contractor Indicator",
            "ATO Indicator",
        ],
        "purpose and outputs": [
            "Use Case Topic Area",
            "AI Classification",
            "Problem Description",
            "Benefit Description",
            "Output Description",
        ],
        "data and privacy": [
            "Training Data Description",
            "Enterprise Data Inventory URL",
            "PII Indicator",
            "PIA URL",
            "Demographic Variable Description",
        ],
        "code and transparency": [
            "Public Reporting Indicator",
            "Custom Code Indicator",
            "Open Source Code URL",
            "Vendor Name",
            "System Name",
        ],
        "assurance and recourse": [
            "High Impact Indicator",
            "High Impact Justification",
            "Predeployment Testing Indicator",
            "AI Impact Assessment Indicator",
            "Potential Impact Description",
            "Independent Review Indicator",
            "Ongoing Monitoring Indicator",
            "Operator Training Indicator",
            "Fail Safe Indicator",
            "Appeal Process Indicator",
            "End User Feedback Description",
        ],
    }
    classified_fields = [
        field for fields in information_families.values() for field in fields
    ]
    if set(classified_fields) != set(all_fields):
        raise ValueError(
            "AI inventory disclosure taxonomy must cover every processed field "
            f"exactly once: missing={set(all_fields) - set(classified_fields)}, "
            f"extra={set(classified_fields) - set(all_fields)}."
        )
    field_completeness = {
        field: mean(not is_missing_value(row.get(field)) for row in rows)
        for field in all_fields
    }
    family_completeness = {
        family: mean(field_completeness[field] for field in fields)
        for family, fields in information_families.items()
    }
    field_status = {
        "fully populated (95–100%)": sum(
            value >= 0.95 for value in field_completeness.values()
        ),
        "partially populated (>0–<95%)": sum(
            0 < value < 0.95 for value in field_completeness.values()
        ),
        "unavailable in snapshot (0%)": sum(
            value == 0 for value in field_completeness.values()
        ),
    }
    review_relevant_fields = [
        field
        for family, fields in information_families.items()
        if family != "identity and ownership"
        for field in fields
    ]
    readiness_by_stage: dict[str, dict[str, float]] = {}
    row_readiness: list[float] = []
    for row in rows:
        row_readiness.append(
            mean(
                not is_missing_value(row.get(field))
                for field in review_relevant_fields
            )
        )
    for stage in stages:
        stage_rows = [
            row
            for row in rows
            if (row["Development Stage"] or "Unreported") == stage
        ]
        readiness_by_stage[stage] = {
            family: mean(
                not is_missing_value(row.get(field))
                for row in stage_rows
                for field in fields
            )
            for family, fields in information_families.items()
        }
    evidence_rows = []
    family_for_field = {
        field: family
        for family, fields in information_families.items()
        for field in fields
    }
    for field in all_fields:
        evidence_rows.append(
            {
                "evidence_item": field,
                "source_field": field,
                "information_family": family_for_field[field],
                "observed_reporting_completeness": round(
                    field_completeness[field], 6
                ),
                "availability_status": (
                    "unavailable in snapshot"
                    if field_completeness[field] == 0
                    else "fully populated"
                    if field_completeness[field] >= 0.95
                    else "partially populated"
                ),
                "evidence_class": "public self-reported inventory field",
                "boundary": (
                    "Completeness measures external observability only; blank or "
                    "missing-coded reporting is not proof that a control is absent "
                    "or ineffective."
                ),
            }
        )
    write_csv(
        project_root / "outputs/evidence-table.csv",
        evidence_rows,
        [
            "evidence_item",
            "source_field",
            "information_family",
            "observed_reporting_completeness",
            "availability_status",
            "evidence_class",
            "boundary",
        ],
    )
    evidence_request_schema = [
        {
            "information_request": "system purpose, owner, users, and decision role",
            "why_needed": "defines the unit and responsibility boundary",
            "inventory_support": "partially observable",
        },
        {
            "information_request": "training and evaluation data lineage",
            "why_needed": "supports validity, privacy, and representativeness review",
            "inventory_support": "partially observable",
        },
        {
            "information_request": "predeployment test design and results",
            "why_needed": "supports performance and failure-mode evaluation",
            "inventory_support": "not observable in reviewed fields",
        },
        {
            "information_request": "impact assessment, monitoring, and incident triggers",
            "why_needed": "supports lifecycle assurance and escalation review",
            "inventory_support": "not observable in reviewed fields",
        },
        {
            "information_request": "notice, appeal, fallback, and remedy process",
            "why_needed": "supports contestability and recourse review",
            "inventory_support": "not observable in reviewed fields",
        },
    ]
    measurement_brief_lines = [
        "# Measurement brief · What the public AI inventory can and cannot show",
        "",
        "## Measurement question",
        "",
        "Which information is externally observable in the reviewed inventory, "
        "and which stronger evaluation questions remain unsupported?",
        "",
        "## Main result",
        "",
        (
            f"The reviewed DOT file contains {len(rows)} publicly reported use cases. "
            f"Across {len(all_fields)} processed public fields, "
            f"{field_status['unavailable in snapshot (0%)']} are missing under "
            "the declared rule for every record in this snapshot."
        ),
        "",
        "This is a disclosure and measurement-readiness result. It does not measure "
        "actual governance capability, control effectiveness, safety, ethics, or compliance.",
        "",
        "## Minimum evidence-request schema",
        "",
        "| Information request | Why it is needed | Support in the reviewed inventory |",
        "|---|---|---|",
    ]
    measurement_brief_lines.extend(
        f"| {item['information_request']} | {item['why_needed']} | {item['inventory_support']} |"
        for item in evidence_request_schema
    )
    measurement_brief_lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "Use the inventory to define additional evidence requests. Do not use "
            "completeness or the analyst-defined readiness score to rank systems, "
            "agencies, or governance maturity.",
        ]
    )
    (project_root / "outputs/measurement-brief.md").write_text(
        "\n".join(measurement_brief_lines) + "\n",
        encoding="utf-8",
    )
    result = {
        "project_id": "federal-ai-governance",
        "data": {"use_cases": len(rows), "as_of": "dataset modified 2026-02-01"},
        "development_stage": dict(stages),
        "high_impact_indicator": dict(high_impact),
        "public_fields_analyzed": len(all_fields),
        "missing_value_policy": MISSING_VALUE_POLICY,
        "information_families": information_families,
        "field_reporting_completeness": field_completeness,
        "family_reporting_completeness": family_completeness,
        "field_availability_status_counts": field_status,
        "family_completeness_by_stage": readiness_by_stage,
        "disclosure_readiness": {
            "definition": (
                "share of non-identity review-relevant public fields populated"
            ),
            "mean": mean(row_readiness),
            "median": statistics.median(row_readiness),
            "minimum": min(row_readiness),
            "maximum": max(row_readiness),
            "interpretation": (
                "external measurement readiness only; not governance maturity "
                "or control quality"
            ),
        },
        "evidence_request_schema": evidence_request_schema,
        "decision_support": {
            "question": (
                "What additional evidence is required before evaluating actual "
                "governance capability?"
            ),
            "recommended_next_diligence": (
                "request the evidence schema before any capability assessment"
            ),
            "reversal_conditions": [
                "Publisher documentation establishes that missing-coded fields are not part of the public reporting contract.",
                "A revised inventory materially changes field availability or definitions.",
                "Reviewed internal evidence supports a separately scoped capability evaluation.",
            ],
        },
        "evidence_artifacts": [
            "outputs/evidence-table.csv",
            "outputs/measurement-brief.md",
        ],
        "interpretation_boundary": (
            "A blank or missing-coded public-inventory field is a disclosure signal, "
            "not proof that a control is absent, ineffective, unethical, unsafe, "
            "or noncompliant."
        ),
    }
    source = "U.S. DOT AI Use Case Inventory, dataset anj8-k6f5, modified 2026-02-01"
    figures = project_root / "outputs/figures"
    svg_bar(
        figures / "stage-distribution.svg",
        "DOT AI use cases by development stage",
        "Public inventory snapshot; 70 use cases in the reviewed file",
        [(stage, float(count)) for stage, count in stages.most_common()],
        source,
    )
    stage_names = list(stages)
    svg_heatmap(
        figures / "governance-completeness.svg",
        "Public disclosure completeness by information family and stage",
        "Mean nonmissing share; NA and N/A are treated as missing",
        stage_names,
        list(information_families),
        [
            [
                readiness_by_stage[stage][family]
                for family in information_families
            ]
            for stage in stage_names
        ],
        source,
    )
    svg_bar(
        figures / "governance-reporting.svg",
        "Public reporting completeness by information family",
        "Mean nonmissing share; NA and N/A are treated as missing",
        [
            (family, value)
            for family, value in family_completeness.items()
        ],
        source,
        percent=True,
    )
    svg_bar(
        figures / "field-status.svg",
        "Availability status across all public inventory fields",
        "Every processed public field is counted exactly once",
        [(label, float(count)) for label, count in field_status.items()],
        source,
    )
    assurance_fields = information_families["assurance and recourse"]
    svg_bar(
        figures / "assurance-disclosure.svg",
        "Assurance and recourse field completeness",
        "A zero is a public-disclosure result, not evidence of control absence",
        [
            (field.replace(" Indicator", ""), field_completeness[field])
            for field in assurance_fields
        ],
        source,
        percent=True,
    )
    return result


def _haversine(left: tuple[float, float], right: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, left)
    lat2, lon2 = map(math.radians, right)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _standardize(values: list[float]) -> list[float]:
    center, spread = mean(values), sd(values) or 1
    return [(value - center) / spread for value in values]


def _select_hubs(
    tracts: list[dict[str, Any]],
    score_field: str,
    *,
    hub_count: int = 5,
    radius_km: float = 10.0,
) -> list[str]:
    candidates = sorted(tracts, key=lambda row: row[score_field], reverse=True)[:100]
    uncovered = {row["geoid"] for row in tracts}
    selected: list[str] = []
    for _ in range(hub_count):
        best_id, best_gain = None, -1.0
        for candidate in candidates:
            if candidate["geoid"] in selected:
                continue
            center = (candidate["latitude"], candidate["longitude"])
            gain = sum(
                row["population"] * max(row[score_field], 0)
                for row in tracts
                if row["geoid"] in uncovered
                and _haversine(center, (row["latitude"], row["longitude"])) <= radius_km
            )
            if gain > best_gain:
                best_id, best_gain = candidate["geoid"], gain
        if best_id is None:
            break
        selected.append(best_id)
        center_row = next(row for row in tracts if row["geoid"] == best_id)
        center = (center_row["latitude"], center_row["longitude"])
        uncovered = {
            geoid
            for geoid in uncovered
            if _haversine(
                center,
                (
                    next(row for row in tracts if row["geoid"] == geoid)["latitude"],
                    next(row for row in tracts if row["geoid"] == geoid)["longitude"],
                ),
            )
            > radius_km
        }
    return selected


def _evaluate_hubs(
    tracts: list[dict[str, Any]],
    hub_ids: list[str],
    radius_km: float,
    *,
    hub_coordinates: list[tuple[float, float]] | None = None,
) -> dict[str, float]:
    hubs = hub_coordinates or [
        (row["latitude"], row["longitude"])
        for row in tracts
        if row["geoid"] in hub_ids
    ]
    if not hubs:
        raise ValueError("At least one reviewed hub coordinate is required.")
    distances = [
        min(_haversine((row["latitude"], row["longitude"]), hub) for hub in hubs)
        for row in tracts
    ]
    need_total = sum(row["population"] * max(row["composite_need"], 0) for row in tracts)
    need_covered = sum(
        row["population"] * max(row["composite_need"], 0)
        for row, distance in zip(tracts, distances)
        if distance <= radius_km
    )
    high_poverty = [row for row in tracts if row["poverty_rate"] >= 0.20]
    high_covered = sum(
        row["population"]
        for row, distance in zip(tracts, distances)
        if row["poverty_rate"] >= 0.20 and distance <= radius_km
    )
    high_total = sum(row["population"] for row in high_poverty)
    population_total = sum(row["population"] for row in tracts)
    average_distance = sum(
        row["population"] * min(distance, 50.0)
        for row, distance in zip(tracts, distances)
    ) / population_total
    return {
        "need_coverage": need_covered / need_total if need_total else 0,
        "high_poverty_coverage": high_covered / high_total if high_total else 0,
        "population_weighted_distance_km": average_distance,
    }


def _morans_i(tracts: list[dict[str, Any]], field: str, neighbors: int = 5) -> float:
    values = [row[field] for row in tracts]
    center = mean(values)
    denominator = sum((value - center) ** 2 for value in values)
    numerator, weights = 0.0, 0
    for index, row in enumerate(tracts):
        distances = sorted(
            (
                _haversine(
                    (row["latitude"], row["longitude"]),
                    (other["latitude"], other["longitude"]),
                ),
                other_index,
            )
            for other_index, other in enumerate(tracts)
            if other_index != index
        )[:neighbors]
        for _, other_index in distances:
            numerator += (values[index] - center) * (values[other_index] - center)
            weights += 1
    return len(tracts) / weights * numerator / denominator if weights and denominator else 0


def _svg_map(path: Path, tracts: list[dict[str, Any]], hubs: list[str], source: str) -> None:
    lats = [row["latitude"] for row in tracts]
    lons = [row["longitude"] for row in tracts]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    body = []
    for row in tracts:
        x = 90 + 820 * (row["longitude"] - min_lon) / (max_lon - min_lon)
        y = 430 - 310 * (row["latitude"] - min_lat) / (max_lat - min_lat)
        opacity = 0.18 + 0.62 * max(0, min(1, (row["composite_need"] + 2) / 4))
        body.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" '
            f'fill="{PALETTE["blue"]}" fill-opacity="{opacity:.2f}"/>'
        )
        if row["geoid"] in hubs:
            body.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{PALETTE["paper"]}" '
                f'stroke="{PALETTE["gold"]}" stroke-width="3"/>'
            )
    path.write_text(
        _svg_shell(
            "Composite-need tract pattern and selected hubs",
            "Massachusetts tract internal points, EPSG:4326; circles are not tract polygons",
            "".join(body),
            source,
        ),
        encoding="utf-8",
    )


def analyze_spatial(project_root: Path) -> dict[str, Any]:
    source_rows = read_csv(project_root / "data/processed/analysis.csv")
    tracts = []
    for row in source_rows:
        values = {
            key: _safe_number(row.get(key))
            for key in (
                "population",
                "poverty_population",
                "poverty_count",
                "median_household_income",
                "workers",
                "public_transit_workers",
                "median_gross_rent",
                "latitude",
                "longitude",
            )
        }
        if any(
            values[key] is None
            for key in (
                "population",
                "poverty_population",
                "poverty_count",
                "workers",
                "public_transit_workers",
                "latitude",
                "longitude",
            )
        ):
            continue
        if values["population"] <= 0 or values["poverty_population"] <= 0:
            continue
        poverty_rate = values["poverty_count"] / values["poverty_population"]
        transit_share = (
            values["public_transit_workers"] / values["workers"]
            if values["workers"] and values["workers"] > 0
            else 0
        )
        rent_burden_proxy = (
            12 * values["median_gross_rent"] / values["median_household_income"]
            if values["median_household_income"]
            and values["median_household_income"] > 0
            and values["median_gross_rent"] is not None
            else 0
        )
        tracts.append(
            {
                "geoid": row["geoid"],
                "latitude": values["latitude"],
                "longitude": values["longitude"],
                "population": values["population"],
                "poverty_rate": poverty_rate,
                "transit_share": transit_share,
                "rent_to_income_proxy": rent_burden_proxy,
            }
        )
    poverty_z = _standardize([row["poverty_rate"] for row in tracts])
    transit_z = _standardize([row["transit_share"] for row in tracts])
    rent_z = _standardize([row["rent_to_income_proxy"] for row in tracts])
    for index, row in enumerate(tracts):
        row["poverty_need"] = poverty_z[index]
        row["transit_need"] = transit_z[index]
        row["composite_need"] = (
            0.5 * poverty_z[index] + 0.3 * transit_z[index] + 0.2 * rent_z[index]
        )
    radius = 10.0
    strategies = {}
    for name, field in (
        ("poverty-priority", "poverty_need"),
        ("transit-priority", "transit_need"),
        ("composite-equity", "composite_need"),
    ):
        hubs = _select_hubs(tracts, field, radius_km=radius)
        metrics = _evaluate_hubs(tracts, hubs, radius)
        hub_coordinates = [
            (row["latitude"], row["longitude"])
            for row in tracts
            if row["geoid"] in hubs
        ]
        rng = random.Random(71 + len(strategies))
        bootstrap = {key: [] for key in metrics}
        for _ in range(300):
            sample = [tracts[rng.randrange(len(tracts))] for _ in tracts]
            sampled = _evaluate_hubs(
                sample,
                hubs,
                radius,
                hub_coordinates=hub_coordinates,
            )
            for key, value in sampled.items():
                bootstrap[key].append(round(value, 7))
        strategies[name] = {"hub_geoids": hubs, **metrics, "bootstrap": bootstrap}
    radius_sensitivity = {}
    for sensitivity_radius in (5.0, 10.0, 15.0):
        hubs = _select_hubs(
            tracts,
            "composite_need",
            radius_km=sensitivity_radius,
        )
        radius_sensitivity[str(int(sensitivity_radius))] = {
            "radius_km": sensitivity_radius,
            "hub_geoids": hubs,
            **_evaluate_hubs(
                tracts,
                hubs,
                sensitivity_radius,
            ),
        }
    weight_scenarios = {
        "poverty-heavy": (0.7, 0.15, 0.15),
        "balanced": (0.5, 0.3, 0.2),
        "transit-heavy": (0.3, 0.5, 0.2),
    }
    weight_sensitivity = {}
    for name, weights in weight_scenarios.items():
        field = f"sensitivity_{name}"
        for index, row in enumerate(tracts):
            row[field] = (
                weights[0] * poverty_z[index]
                + weights[1] * transit_z[index]
                + weights[2] * rent_z[index]
            )
        hubs = _select_hubs(tracts, field, radius_km=radius)
        weight_sensitivity[name] = {
            "weights": {
                "poverty": weights[0],
                "transit": weights[1],
                "rent_pressure": weights[2],
            },
            "hub_geoids": hubs,
            **_evaluate_hubs(tracts, hubs, radius),
        }
    grid_groups: dict[tuple[float, float], list[dict[str, Any]]] = defaultdict(list)
    for row in tracts:
        grid_groups[
            (
                round(row["latitude"] / 0.25) * 0.25,
                round(row["longitude"] / 0.25) * 0.25,
            )
        ].append(row)
    grid_units = []
    for (latitude, longitude), group in grid_groups.items():
        population = sum(row["population"] for row in group)
        grid_units.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "poverty_rate": sum(
                    row["population"] * row["poverty_rate"] for row in group
                )
                / population,
            }
        )
    tract_moran = _morans_i(tracts, "poverty_rate")
    grid_moran = _morans_i(
        grid_units,
        "poverty_rate",
        neighbors=min(5, len(grid_units) - 1),
    )
    map_text = [
        "Composite-need tract pattern and selected hubs",
        "",
        (
            f"The analyzed dataset contains {len(tracts):,} Massachusetts census "
            "tract internal points. Higher composite need is concentrated rather "
            "than uniformly distributed."
        ),
        "",
        "Selected composite-equity hub tract GEOIDs:",
        *[
            f"- {geoid}"
            for geoid in strategies["composite-equity"]["hub_geoids"]
        ],
        "",
        (
            "The SVG uses tract internal points, not polygons or street-network "
            "travel times. Hub selection assumes a 10 km straight-line radius."
        ),
    ]
    (project_root / "outputs/figures/need-map.txt").write_text(
        "\n".join(map_text) + "\n",
        encoding="utf-8",
    )
    result = {
        "project_id": "spatial-equity-planning",
        "data": {
            "tracts_in_source": len(source_rows),
            "tracts_analyzed": len(tracts),
            "crs": "EPSG:4326",
            "acs_period": "2019-2023 5-year",
        },
        "spatial_autocorrelation": {
            "metric": "poverty_rate",
            "neighbors": 5,
            "morans_i": tract_moran,
        },
        "location_allocation": {
            "hub_count": 5,
            "coverage_radius_km": radius,
            "strategies": strategies,
        },
        "robustness": {
            "coverage_radius_sensitivity": radius_sensitivity,
            "need_weight_sensitivity": weight_sensitivity,
            "maup_grid_proxy": {
                "tract_units": len(tracts),
                "coarse_quarter_degree_grid_units": len(grid_units),
                "tract_poverty_morans_i": tract_moran,
                "grid_poverty_morans_i": grid_moran,
                "poverty_rate_sd_ratio_grid_to_tract": (
                    sd(row["poverty_rate"] for row in grid_units)
                    / sd(row["poverty_rate"] for row in tracts)
                ),
                "boundary": (
                    "The coarse grid is a sensitivity proxy, not an official "
                    "planning geography; it demonstrates scale dependence."
                ),
            },
            "spatial_spillover": (
                "Moran's I documents local dependence; the allocation model does "
                "not identify causal spillovers across tract boundaries."
            ),
        },
        "planning_delivery": {
            "planning_intervention": "screen candidate areas for five service hubs",
            "affected_population": "Massachusetts residents represented by ACS tract estimates",
            "implementing_authority": (
                "Not specified by the dataset; state, regional, municipal, land-use, "
                "funding, and service-owner authority require local review."
            ),
            "constraints_not_observed": [
                "parcel availability and zoning",
                "street-network travel time",
                "capital and operating budgets",
                "delivery lead times",
                "community priorities and displacement risk",
            ],
            "monitoring": [
                "real travel time and utilization",
                "service access by income and race/ethnicity where lawfully measured",
                "housing pressure and displacement indicators",
                "delivery cost and schedule",
            ],
            "reversal_conditions": [
                "Network travel times reverse straight-line accessibility rankings.",
                "Local land-use or ownership makes selected hubs infeasible.",
                "Alternative weights or geographic aggregation materially change priorities.",
            ],
        },
        "measurement_boundary": (
            "Gazetteer points approximate tract locations; the analysis is not a "
            "street-network travel-time model. ACS estimates carry sampling error."
        ),
    }
    source = "U.S. Census Bureau 2019–2023 ACS 5-year and 2023 Gazetteer"
    figures = project_root / "outputs/figures"
    _svg_map(
        figures / "need-map.svg",
        tracts,
        strategies["composite-equity"]["hub_geoids"],
        source,
    )
    svg_bar(
        figures / "strategy-coverage.svg",
        "Need-weighted coverage by hub strategy",
        "Five hubs; 10 km straight-line radius; Massachusetts census tracts",
        [
            (name.replace("-", " ").title(), value["need_coverage"])
            for name, value in strategies.items()
        ],
        source,
        percent=True,
    )
    svg_line(
        figures / "radius-sensitivity.svg",
        "Need-weighted coverage by service radius",
        "Composite-need hub plan re-optimized at each straight-line radius",
        [
            (
                "Coverage",
                [
                    (
                        value["radius_km"],
                        value["need_coverage"],
                    )
                    for value in radius_sensitivity.values()
                ],
            )
        ],
        source,
        y_percent=True,
    )
    return result

__all__ = [name for name in globals() if not name.startswith("__")]
