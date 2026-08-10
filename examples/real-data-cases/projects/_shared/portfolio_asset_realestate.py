#!/usr/bin/env python3
"""Multi-asset allocation and real-estate transaction case modules."""

from __future__ import annotations

from portfolio_core import *


ASSET_SYMBOLS = ("SPY", "TLT", "VNQ", "GLD", "BIL")
ASSET_LABELS = {
    "SPY": "US equity",
    "TLT": "long Treasury",
    "VNQ": "listed real estate",
    "GLD": "gold",
    "BIL": "Treasury bills",
}


def _number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def prepare_multi_asset(
    project_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_path = project_root / "data/raw/yahoo-adjusted-close-2015-2025.json"
    payload = load_json(raw_path)
    source_symbols = payload.get("symbols", {})
    if set(source_symbols) != set(ASSET_SYMBOLS):
        raise ValueError(
            "The reviewed multi-asset snapshot must contain exactly "
            f"{', '.join(ASSET_SYMBOLS)}."
        )

    by_symbol: dict[str, dict[str, float]] = {}
    for symbol in ASSET_SYMBOLS:
        item = source_symbols[symbol]
        timestamps = item.get("timestamp", [])
        adjusted = item.get("adjusted_close", [])
        if len(timestamps) != len(adjusted):
            raise ValueError(f"Timestamp/price length mismatch for {symbol}.")
        observations: dict[str, float] = {}
        for timestamp, price in zip(timestamps, adjusted):
            if price is None:
                continue
            date = datetime.utcfromtimestamp(int(timestamp)).date().isoformat()
            observations[date] = float(price)
        if len(observations) < 2000:
            raise ValueError(f"Insufficient reviewed price history for {symbol}.")
        by_symbol[symbol] = observations

    common_dates = sorted(
        set.intersection(*(set(values) for values in by_symbol.values()))
    )
    rows = [
        {
            "date": date,
            **{symbol: by_symbol[symbol][date] for symbol in ASSET_SYMBOLS},
        }
        for date in common_dates
    ]
    write_csv(
        project_root / "data/processed/analysis.csv",
        rows,
        ["date", *ASSET_SYMBOLS],
    )
    dictionary = {
        "project_id": "sec-nport-filing-review",
        "primary_key": "date",
        "fields": {
            "date": "common US trading date in ISO format",
            **{
                symbol: (
                    f"reviewed adjusted closing-price series for {symbol}; "
                    f"case label: {ASSET_LABELS[symbol]}"
                )
                for symbol in ASSET_SYMBOLS
            },
        },
        "interpretation_boundary": (
            "Adjusted-price histories are an educational market-data snapshot. "
            "They do not establish tradability at the recorded price, future "
            "returns, suitability, or authorization to invest."
        ),
    }
    return rows, dictionary


def _real_estate_type(category: str) -> str:
    value = category.upper()
    if "OFFICE" in value:
        return "Office"
    if any(token in value for token in ("STORE", "RETAIL", "SHOPPING")):
        return "Retail"
    if any(token in value for token in ("FACTORY", "WAREHOUSE", "INDUSTRIAL")):
        return "Industrial"
    if any(token in value for token in ("MIXED", "MULTI")):
        return "Mixed-use"
    if any(token in value for token in ("HOTEL", "MOTEL")):
        return "Hotel"
    return "Other commercial"


def prepare_real_estate(
    project_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_path = project_root / "data/raw/nyc-commercial-sales-2021-2025.csv"
    raw_rows = read_csv(raw_path)
    borough_names = {
        "1": "Manhattan",
        "2": "Bronx",
        "3": "Brooklyn",
        "4": "Queens",
        "5": "Staten Island",
    }
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for raw in raw_rows:
        sale_price = _number(raw.get("sale_price"))
        gross_square_feet = _number(raw.get("gross_square_feet"))
        commercial_units = _number(raw.get("commercial_units"))
        sale_date = (raw.get("sale_date") or "")[:10]
        if (
            sale_price is None
            or gross_square_feet is None
            or commercial_units is None
            or sale_price < 100_000
            or gross_square_feet <= 0
            or commercial_units <= 0
            or not ("2021-01-01" <= sale_date < "2026-01-01")
        ):
            continue
        price_per_sqft = sale_price / gross_square_feet
        if not (20 <= price_per_sqft <= 5_000):
            continue
        key = (
            raw.get("borough", ""),
            raw.get("block", ""),
            raw.get("lot", ""),
            sale_date,
            f"{sale_price:.0f}",
        )
        if key in seen:
            continue
        seen.add(key)
        borough_code = raw.get("borough", "")
        rows.append(
            {
                "transaction_id": "-".join(key),
                "sale_date": sale_date,
                "sale_year": int(sale_date[:4]),
                "borough": borough_names.get(borough_code, borough_code),
                "neighborhood": (raw.get("neighborhood") or "Unreported").strip(),
                "property_type": _real_estate_type(
                    raw.get("building_class_category", "")
                ),
                "building_class_category": raw.get(
                    "building_class_category", ""
                ).strip(),
                "commercial_units": int(commercial_units),
                "total_units": int(_number(raw.get("total_units")) or 0),
                "gross_square_feet": gross_square_feet,
                "sale_price": sale_price,
                "price_per_sqft": price_per_sqft,
                "year_built": int(_number(raw.get("year_built")) or 0),
                "latitude": _number(raw.get("latitude")),
                "longitude": _number(raw.get("longitude")),
                "community_board": (raw.get("community_board") or "").strip(),
            }
        )
    rows.sort(
        key=lambda row: (
            row["sale_date"],
            row["borough"],
            row["transaction_id"],
        )
    )
    write_csv(
        project_root / "data/processed/analysis.csv",
        rows,
        [
            "transaction_id",
            "sale_date",
            "sale_year",
            "borough",
            "neighborhood",
            "property_type",
            "building_class_category",
            "commercial_units",
            "total_units",
            "gross_square_feet",
            "sale_price",
            "price_per_sqft",
            "year_built",
            "latitude",
            "longitude",
            "community_board",
        ],
    )
    dictionary = {
        "project_id": "commercial-real-estate-risk",
        "primary_key": "transaction_id",
        "fields": {
            "transaction_id": (
                "deterministic transaction key built from borough, block, lot, "
                "sale date, and price; street address is excluded"
            ),
            "sale_date": "recorded property sale date",
            "sale_year": "calendar year from sale_date",
            "borough": "NYC borough name",
            "neighborhood": "Department of Finance valuation neighborhood",
            "property_type": "analyst grouping from building_class_category",
            "building_class_category": "NYC Department of Finance class category",
            "commercial_units": "reported commercial-unit count",
            "total_units": "reported total-unit count",
            "gross_square_feet": "reported gross building area",
            "sale_price": "recorded sale price in nominal US dollars",
            "price_per_sqft": "sale_price divided by gross_square_feet",
            "year_built": "reported construction year; zero means unavailable",
            "latitude": "public approximate latitude when reported",
            "longitude": "public approximate longitude when reported",
            "community_board": "public community-board identifier when reported",
        },
        "filter_policy": {
            "period": "2021-01-01 through 2025-12-31",
            "commercial_units": "> 0",
            "sale_price": ">= 100,000 USD",
            "gross_square_feet": "> 0",
            "price_per_sqft": "20 to 5,000 USD for robust screening",
            "duplicates": "exact borough/block/lot/date/price duplicates removed",
        },
        "interpretation_boundary": (
            "Administrative sales records do not establish arm's-length status, "
            "property condition, lease income, operating expenses, financing "
            "terms, appraisal value, or investability."
        ),
    }
    return rows, dictionary


def _cap_weights(
    raw_weights: dict[str, float],
    *,
    minimum: float,
    maximum: float,
) -> dict[str, float]:
    count = len(raw_weights)
    if count == 0:
        raise ValueError("At least one asset weight is required.")
    if minimum < 0 or maximum <= 0 or minimum > maximum:
        raise ValueError("Weight bounds must satisfy 0 <= minimum <= maximum.")
    if count * minimum > 1 + 1e-12 or count * maximum < 1 - 1e-12:
        raise ValueError("Weight bounds do not contain a feasible unit-sum portfolio.")
    weights = {
        symbol: max(minimum, min(maximum, value))
        for symbol, value in raw_weights.items()
    }
    for _ in range(10):
        total = sum(weights.values())
        if math.isclose(total, 1.0, abs_tol=1e-12):
            break
        if total < 1:
            gaps = {
                symbol: maximum - value
                for symbol, value in weights.items()
                if value < maximum - 1e-12
            }
            available = sum(gaps.values())
            if available <= 0:
                raise ValueError("Weight cap leaves no room to reach unit sum.")
            increment = min(1 - total, available)
            for symbol, gap in gaps.items():
                weights[symbol] += increment * gap / available
        else:
            slack = {
                symbol: value - minimum
                for symbol, value in weights.items()
                if value > minimum + 1e-12
            }
            available = sum(slack.values())
            if available <= 0:
                raise ValueError("Weight floor leaves no room to reach unit sum.")
            reduction = min(total - 1, available)
            for symbol, room in slack.items():
                weights[symbol] -= reduction * room / available
    if not math.isclose(sum(weights.values()), 1.0, abs_tol=1e-9):
        raise ValueError("Bounded weight projection did not converge to unit sum.")
    return weights


def _portfolio_metrics(returns: list[float]) -> dict[str, float]:
    annual_return = (math.prod(1 + value for value in returns) ** (252 / len(returns))) - 1
    annual_volatility = statistics.stdev(returns) * math.sqrt(252)
    running = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in returns:
        running *= 1 + value
        peak = max(peak, running)
        max_drawdown = min(max_drawdown, running / peak - 1)
    losses = sorted(-value for value in returns)
    var95 = quantile(losses, 0.95)
    tail = [value for value in losses if value >= var95]
    es95 = mean(tail)
    return {
        "annualized_return": annual_return,
        "annualized_volatility": annual_volatility,
        "return_to_volatility": (
            annual_return / annual_volatility if annual_volatility else 0.0
        ),
        "maximum_drawdown": max_drawdown,
        "daily_var95_loss": var95,
        "daily_expected_shortfall95_loss": es95,
    }


def _period_return(
    dates: list[str],
    returns: list[float],
    start: str,
    end: str,
) -> float:
    selected = [
        value
        for date, value in zip(dates, returns)
        if start <= date <= end
    ]
    return math.prod(1 + value for value in selected) - 1 if selected else 0.0


def _monthly_compound(
    dates: list[str],
    returns: list[float],
) -> tuple[list[str], list[float]]:
    by_month: dict[str, list[float]] = defaultdict(list)
    for date, value in zip(dates, returns):
        by_month[date[:7]].append(value)
    months = sorted(by_month)
    return months, [
        math.prod(1 + value for value in by_month[month]) - 1
        for month in months
    ]


def analyze_multi_asset(project_root: Path) -> dict[str, Any]:
    source_rows = read_csv(project_root / "data/processed/analysis.csv")
    dates = [row["date"] for row in source_rows]
    prices = {
        symbol: [float(row[symbol]) for row in source_rows]
        for symbol in ASSET_SYMBOLS
    }
    asset_returns = {
        symbol: [
            prices[symbol][index] / prices[symbol][index - 1] - 1
            for index in range(1, len(source_rows))
        ]
        for symbol in ASSET_SYMBOLS
    }
    return_dates = dates[1:]
    config = load_json(project_root / "config.json")
    parameters = config["parameters"]
    lookback = int(parameters["volatility_lookback_days"])
    cost_rate = float(parameters["transaction_cost_bps"]) / 10_000
    minimum = float(parameters["minimum_weight"])
    maximum = float(parameters["maximum_weight"])
    bootstrap_samples = int(parameters["bootstrap_samples"])
    bootstrap_block_months = int(parameters["bootstrap_block_months"])

    strategy_returns = {
        "walk-forward inverse-volatility": [],
        "equal-weight benchmark": [],
        "60/40 equity-Treasury benchmark": [],
    }
    aligned_dates: list[str] = []
    current_weights = {symbol: 1 / len(ASSET_SYMBOLS) for symbol in ASSET_SYMBOLS}
    previous_weights = dict(current_weights)
    current_month = ""
    turnover_total = 0.0
    weight_history: list[dict[str, Any]] = []
    for index in range(lookback, len(return_dates)):
        date = return_dates[index]
        month = date[:7]
        cost = 0.0
        if month != current_month:
            raw = {}
            for symbol in ASSET_SYMBOLS:
                window = asset_returns[symbol][index - lookback : index]
                volatility = statistics.stdev(window)
                raw[symbol] = 1 / max(volatility, 1e-9)
            raw_total = sum(raw.values())
            proposed = {
                symbol: value / raw_total for symbol, value in raw.items()
            }
            current_weights = _cap_weights(
                proposed,
                minimum=minimum,
                maximum=maximum,
            )
            turnover = 0.5 * sum(
                abs(current_weights[symbol] - previous_weights[symbol])
                for symbol in ASSET_SYMBOLS
            )
            cost = turnover * cost_rate
            turnover_total += turnover
            previous_weights = dict(current_weights)
            current_month = month
            weight_history.append({"month": month, **current_weights})
        daily = {
            symbol: asset_returns[symbol][index]
            for symbol in ASSET_SYMBOLS
        }
        strategy_returns["walk-forward inverse-volatility"].append(
            sum(current_weights[symbol] * daily[symbol] for symbol in ASSET_SYMBOLS)
            - cost
        )
        strategy_returns["equal-weight benchmark"].append(
            mean(daily.values())
        )
        strategy_returns["60/40 equity-Treasury benchmark"].append(
            0.6 * daily["SPY"] + 0.4 * daily["TLT"]
        )
        aligned_dates.append(date)

    metrics = {
        name: _portfolio_metrics(values)
        for name, values in strategy_returns.items()
    }
    metrics["walk-forward inverse-volatility"]["annual_turnover"] = (
        turnover_total / max(1, len(weight_history) / 12)
    )
    stress_periods = {
        "pandemic selloff (2020-02-19 to 2020-03-23)": {
            name: _period_return(
                aligned_dates,
                values,
                "2020-02-19",
                "2020-03-23",
            )
            for name, values in strategy_returns.items()
        },
        "2022 inflation/rate regime": {
            name: _period_return(
                aligned_dates,
                values,
                "2022-01-01",
                "2022-12-31",
            )
            for name, values in strategy_returns.items()
        },
    }

    monthly_by_strategy: dict[str, list[float]] = {}
    months: list[str] = []
    for name, values in strategy_returns.items():
        strategy_months, monthly = _monthly_compound(aligned_dates, values)
        if not months:
            months = strategy_months
        elif strategy_months != months:
            raise ValueError("Strategy monthly return calendars must align.")
        monthly_by_strategy[name] = monthly

    rng = random.Random(int(config["analysis_seed"]))
    best_counts = Counter()
    block_starts = list(range(max(1, len(months) - bootstrap_block_months + 1)))
    for _ in range(bootstrap_samples):
        sampled_indices: list[int] = []
        while len(sampled_indices) < len(months):
            start = rng.choice(block_starts)
            sampled_indices.extend(
                range(start, min(len(months), start + bootstrap_block_months))
            )
        sampled_indices = sampled_indices[: len(months)]
        scores = {
            name: mean([values[index] for index in sampled_indices])
            for name, values in monthly_by_strategy.items()
        }
        best_counts[max(scores, key=scores.get)] += 1
    probability_best = {
        name: best_counts[name] / bootstrap_samples
        for name in strategy_returns
    }

    cumulative_series = []
    for name, values in strategy_returns.items():
        wealth = 1.0
        points = []
        for index, value in enumerate(values):
            wealth *= 1 + value
            if index % 21 == 0 or index == len(values) - 1:
                points.append((float(index), wealth))
        cumulative_series.append((name, points))
    figure_dir = project_root / "outputs/figures"
    source = "Yahoo Finance reviewed adjusted-price snapshot; analysis by repository"
    svg_line(
        figure_dir / "portfolio-growth.svg",
        "Walk-forward portfolio growth stays benchmarked",
        "Net of the declared transaction-cost sensitivity; no future-return claim",
        cumulative_series,
        source,
    )
    svg_bar(
        figure_dir / "risk-adjusted-performance.svg",
        "Return-to-volatility remains one metric, not a mandate",
        "Annualized return divided by annualized volatility",
        [
            (name, values["return_to_volatility"])
            for name, values in metrics.items()
        ],
        source,
    )
    svg_bar(
        figure_dir / "tail-loss.svg",
        "Historical tail loss remains material across strategies",
        "Daily expected shortfall at the 95% loss threshold",
        [
            (name, values["daily_expected_shortfall95_loss"])
            for name, values in metrics.items()
        ],
        source,
        percent=True,
    )
    svg_bar(
        figure_dir / "probability-best.svg",
        "Shared-block resampling avoids independent strategy shocks",
        "Probability of highest sampled mean monthly return",
        list(probability_best.items()),
        source,
        percent=True,
    )
    evidence_rows = []
    for name, values in metrics.items():
        evidence_rows.append(
            {
                "strategy": name,
                **values,
                "probability_best": probability_best[name],
                "pandemic_selloff_return": stress_periods[
                    "pandemic selloff (2020-02-19 to 2020-03-23)"
                ][name],
                "return_2022": stress_periods[
                    "2022 inflation/rate regime"
                ][name],
            }
        )
    write_csv(
        project_root / "outputs/evidence-table.csv",
        evidence_rows,
        list(evidence_rows[0]),
    )
    return {
        "project_id": "sec-nport-filing-review",
        "data": {
            "price_rows": len(source_rows),
            "evaluated_days": len(aligned_dates),
            "start": aligned_dates[0],
            "end": aligned_dates[-1],
            "assets": list(ASSET_SYMBOLS),
        },
        "study_design": {
            "unit": "common US trading day",
            "information_set": (
                f"trailing {lookback} trading days available before each "
                "monthly rebalance"
            ),
            "evaluation": "walk-forward daily returns after the initial lookback",
            "benchmarks": list(strategy_returns)[1:],
            "claim_class": "historical portfolio-design comparison",
        },
        "strategy_metrics": metrics,
        "decision_options": metrics,
        "stress_periods": stress_periods,
        "probability_best_shared_block_bootstrap": {
            "block_months": bootstrap_block_months,
            "samples": bootstrap_samples,
            "probability_best": probability_best,
            "dependence_boundary": (
                "Every strategy receives the same sampled month blocks, so "
                "common market shocks remain aligned."
            ),
        },
        "latest_walk_forward_weights": weight_history[-1],
        "decision_support": {
            "status": "research_only",
            "next_action": (
                "Use the walk-forward comparison to define a prospective paper "
                "portfolio; do not infer suitability or future outperformance."
            ),
            "reversal_conditions": [
                "Results reverse under a separately sourced total-return history.",
                "A realistic fee, tax, liquidity, or turnover model removes the observed advantage.",
                "A longer crisis regime changes drawdown or tail-loss ordering.",
                "The investor's horizon, liabilities, or fiduciary constraints reject the weight bounds.",
            ],
        },
    }


def _median_absolute_deviation(values: list[float]) -> float:
    center = statistics.median(values)
    return statistics.median(abs(value - center) for value in values)


def _annual_mortgage_factor(rate: float, years: int) -> float:
    monthly_rate = rate / 12
    periods = years * 12
    monthly = (
        monthly_rate * (1 + monthly_rate) ** periods
        / ((1 + monthly_rate) ** periods - 1)
    )
    return monthly * 12


def analyze_real_estate(project_root: Path) -> dict[str, Any]:
    source_rows = read_csv(project_root / "data/processed/analysis.csv")
    rows = [
        {
            **row,
            "sale_year": int(row["sale_year"]),
            "commercial_units": int(row["commercial_units"]),
            "gross_square_feet": float(row["gross_square_feet"]),
            "sale_price": float(row["sale_price"]),
            "price_per_sqft": float(row["price_per_sqft"]),
        }
        for row in source_rows
    ]
    config = load_json(project_root / "config.json")
    parameters = config["parameters"]
    minimum_segment_transactions = int(
        parameters["minimum_segment_transactions"]
    )
    ltv = float(parameters["loan_to_value"])
    amortization_years = int(parameters["amortization_years"])
    dscr_target = float(parameters["dscr_target"])
    interest_rates = [float(value) for value in parameters["interest_rates"]]
    bootstrap_samples = int(parameters["bootstrap_samples"])

    by_borough: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
    by_segment: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_borough[row["borough"]].append(row)
        by_year[row["sale_year"]].append(row)
        by_segment[(row["borough"], row["property_type"])].append(row)

    rng = random.Random(int(config["analysis_seed"]))
    borough_stats = {}
    for borough, items in sorted(by_borough.items()):
        values = [item["price_per_sqft"] for item in items]
        boot = []
        for _ in range(bootstrap_samples):
            sample = [rng.choice(values) for _ in values]
            boot.append(statistics.median(sample))
        borough_stats[borough] = {
            "transactions": len(items),
            "median_price_per_sqft": statistics.median(values),
            "median_absolute_deviation": _median_absolute_deviation(values),
            "median_bootstrap_95_interval": [
                quantile(boot, 0.025),
                quantile(boot, 0.975),
            ],
        }

    annual_activity = {
        str(year): {
            "transactions": len(items),
            "nominal_sale_value": sum(item["sale_price"] for item in items),
            "median_price_per_sqft": statistics.median(
                item["price_per_sqft"] for item in items
            ),
        }
        for year, items in sorted(by_year.items())
    }
    segment_stats = []
    for (borough, property_type), items in sorted(by_segment.items()):
        values = [item["price_per_sqft"] for item in items]
        segment_stats.append(
            {
                "borough": borough,
                "property_type": property_type,
                "transactions": len(items),
                "median_price_per_sqft": statistics.median(values),
                "median_absolute_deviation": _median_absolute_deviation(values),
                "data_sufficiency_gate": (
                    "advance_to_property_level_diligence"
                    if len(items) >= minimum_segment_transactions
                    else "insufficient_public_transactions"
                ),
            }
        )
    sufficiently_observed = [
        item
        for item in segment_stats
        if item["transactions"] >= minimum_segment_transactions
    ]
    decision_options = {}
    for borough, items in sorted(by_borough.items()):
        stats = borough_stats[borough]
        decision_options[borough] = {
            "transaction_share": len(items) / len(rows),
            "price_dispersion_ratio": (
                stats["median_absolute_deviation"]
                / stats["median_price_per_sqft"]
            ),
            "geocoded_share": mean(
                item["latitude"] is not None and item["longitude"] is not None
                for item in items
            ),
        }

    financing_stress = []
    for rate in interest_rates:
        annual_debt_service_factor = _annual_mortgage_factor(
            rate,
            amortization_years,
        )
        financing_stress.append(
            {
                "interest_rate": rate,
                "annual_debt_service_per_dollar_of_debt": annual_debt_service_factor,
                "break_even_cap_rate_for_target_dscr": (
                    ltv * annual_debt_service_factor * dscr_target
                ),
            }
        )

    figure_dir = project_root / "outputs/figures"
    source = "NYC Department of Finance annualized property sales; analyst scenarios"
    svg_bar(
        figure_dir / "borough-price-per-sqft.svg",
        "Commercial transaction pricing differs sharply by borough",
        "Median nominal sale price per reported gross square foot",
        [
            (borough, values["median_price_per_sqft"])
            for borough, values in borough_stats.items()
        ],
        source,
    )
    svg_line(
        figure_dir / "transaction-activity.svg",
        "Transaction activity changes across the observed rate regime",
        "Filtered commercial-property transactions by calendar year",
        [
            (
                "transactions",
                [
                    (float(year), float(values["transactions"]))
                    for year, values in annual_activity.items()
                ],
            )
        ],
        source,
    )
    svg_bar(
        figure_dir / "financing-stress.svg",
        "Higher debt costs require more property income",
        (
            f"Break-even cap rate at {ltv:.0%} LTV, "
            f"{dscr_target:.2f}× DSCR, {amortization_years}-year amortization"
        ),
        [
            (
                f"{item['interest_rate']:.1%} debt rate",
                item["break_even_cap_rate_for_target_dscr"],
            )
            for item in financing_stress
        ],
        source,
        percent=True,
    )
    svg_bar(
        figure_dir / "segment-observation.svg",
        "Public transaction depth determines what can be screened",
        "Segments meeting the declared minimum move only to property-level diligence",
        [
            (
                "segments meeting data gate",
                float(len(sufficiently_observed)),
            ),
            (
                "segments below data gate",
                float(len(segment_stats) - len(sufficiently_observed)),
            ),
        ],
        source,
    )
    write_csv(
        project_root / "outputs/evidence-table.csv",
        segment_stats,
        list(segment_stats[0]),
    )
    decision_product_contract = {
        "terminal_status": "targeted_diligence_only",
        "stakeholder_views": {
            "analyst": {
                "primary_artifacts": [
                    "segment-level transaction depth",
                    "robust price-per-square-foot summaries",
                    "source and filtering evidence",
                ],
                "permitted_action": "assemble a traceable property-level evidence request",
            },
            "risk_manager": {
                "primary_artifacts": [
                    "financing stress scenarios",
                    "thin-market and dispersion flags",
                    "reversal conditions",
                ],
                "permitted_action": "prioritize diligence under declared assumptions",
            },
            "audit_reviewer": {
                "primary_artifacts": [
                    "source manifest and raw hashes",
                    "filtering and parameter provenance",
                    "claim and redistribution boundaries",
                ],
                "permitted_action": "verify that every displayed claim resolves to public evidence",
            },
        },
        "required_next_evidence": [
            "property-level leases and net operating income",
            "operating expenses and capital expenditure",
            "physical condition and environmental review",
            "title, zoning, and planning constraints",
            "actual financing terms",
        ],
        "forbidden_outputs": [
            "appraisal value",
            "acquisition recommendation",
            "credit approval",
            "planning approval",
            "causal regeneration claim",
        ],
    }
    write_json(
        project_root / "outputs/decision-product-contract.json",
        {
            "schema_version": "1.0",
            "project_id": "commercial-real-estate-risk",
            **decision_product_contract,
        },
    )
    return {
        "project_id": "commercial-real-estate-risk",
        "data": {
            "transactions": len(rows),
            "period": [
                min(row["sale_date"] for row in rows),
                max(row["sale_date"] for row in rows),
            ],
            "boroughs": len(by_borough),
            "segments": len(segment_stats),
        },
        "study_design": {
            "unit": "filtered NYC commercial-property sale record",
            "observed_outcomes": "transaction count, nominal sale value, price per gross square foot",
            "financing_layer": "analyst break-even cap-rate scenario, not observed NOI or loan terms",
            "claim_class": "market-screen and diligence-prioritization evidence",
        },
        "borough_statistics": borough_stats,
        "annual_activity": annual_activity,
        "segment_statistics": segment_stats,
        "decision_options": decision_options,
        "financing_stress": {
            "loan_to_value": ltv,
            "amortization_years": amortization_years,
            "target_dscr": dscr_target,
            "scenarios": financing_stress,
            "boundary": (
                "The source contains sale records, not lease-level NOI, expenses, "
                "debt terms, property condition, or appraisal evidence."
            ),
        },
        "decision_product_contract": decision_product_contract,
        "planning_delivery": {
            "status": "diligence_screen_only",
            "sufficiently_observed_segments": len(sufficiently_observed),
            "next_action": (
                "Use sufficiently observed segments to request property-level "
                "lease, expense, condition, title, zoning, and financing evidence."
            ),
            "reversal_conditions": [
                "Arm's-length review removes a material share of transactions.",
                "Property-level NOI or condition evidence reverses segment comparisons.",
                "Alternative financing terms change the required cap-rate threshold.",
                "A planning or community review rejects the screen's geography or regeneration assumptions.",
            ],
        },
    }
