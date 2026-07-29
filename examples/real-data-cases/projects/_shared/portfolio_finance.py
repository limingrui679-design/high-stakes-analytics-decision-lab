#!/usr/bin/env python3
"""Financial statement and market-risk analysis modules."""

from __future__ import annotations

from portfolio_core import *

def _growth_rate(first: float, last: float, periods: int) -> float | None:
    if first <= 0 or last <= 0 or periods <= 0:
        return None
    return (last / first) ** (1 / periods) - 1


def analyze_mckesson(project_root: Path) -> dict[str, Any]:
    source_rows = read_csv(project_root / "data/processed/analysis.csv")
    rows: list[dict[str, Any]] = []
    for source_row in source_rows:
        row: dict[str, Any] = {
            "entity": source_row["entity"],
            "cik": source_row["cik"],
            "fiscal_year": int(source_row["fiscal_year"]),
            "period_end": source_row["period_end"],
        }
        for field in SEC_FACT_TAGS:
            row[field] = _safe_number(source_row.get(field))
        required = (
            "revenue",
            "gross_profit",
            "operating_income",
            "net_income",
            "operating_cash_flow",
            "capital_expenditure",
            "inventory",
            "receivables",
            "accounts_payable",
            "assets",
            "equity",
        )
        if any(row[field] is None for field in required):
            missing = [field for field in required if row[field] is None]
            raise ValueError(
                "SEC annual fact reconciliation is incomplete for "
                f"{row['entity']} FY{row['fiscal_year']}: {missing}"
            )
        rows.append(row)

    rows.sort(key=lambda item: (item["entity"], item["fiscal_year"]))
    by_entity_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_entity_rows[row["entity"]].append(row)

    annual_metrics: list[dict[str, Any]] = []
    for entity, entity_rows in sorted(by_entity_rows.items()):
        for index, row in enumerate(entity_rows):
            revenue = row["revenue"]
            gross_profit = row["gross_profit"]
            cogs = revenue - gross_profit
            if cogs <= 0:
                raise ValueError(
                    f"Non-positive cost of goods sold for {entity} "
                    f"FY{row['fiscal_year']}."
                )
            previous = entity_rows[index - 1] if index else None
            average_inventory = (
                (previous["inventory"] + row["inventory"]) / 2
                if previous
                else row["inventory"]
            )
            average_receivables = (
                (previous["receivables"] + row["receivables"]) / 2
                if previous
                else row["receivables"]
            )
            average_payables = (
                (previous["accounts_payable"] + row["accounts_payable"]) / 2
                if previous
                else row["accounts_payable"]
            )
            net_income = row["net_income"]
            annual_metrics.append(
                {
                    "entity": entity,
                    "cik": row["cik"],
                    "fiscal_year": row["fiscal_year"],
                    "period_end": row["period_end"],
                    "revenue_usd": revenue,
                    "revenue_growth": (
                        None
                        if previous is None
                        else revenue / previous["revenue"] - 1
                    ),
                    "gross_margin": gross_profit / revenue,
                    "operating_margin": row["operating_income"] / revenue,
                    "net_margin": net_income / revenue,
                    "operating_cash_flow_margin": (
                        row["operating_cash_flow"] / revenue
                    ),
                    "cash_earnings_ratio": (
                        None
                        if math.isclose(net_income, 0)
                        else row["operating_cash_flow"] / net_income
                    ),
                    "free_cash_flow_proxy_usd": (
                        row["operating_cash_flow"] - row["capital_expenditure"]
                    ),
                    "inventory_days": average_inventory / cogs * 365,
                    "receivable_days": average_receivables / revenue * 365,
                    "payable_days": average_payables / cogs * 365,
                    "net_working_capital_cycle_days": (
                        average_inventory / cogs * 365
                        + average_receivables / revenue * 365
                        - average_payables / cogs * 365
                    ),
                    "equity_to_assets": row["equity"] / row["assets"],
                    "long_term_debt_to_assets": (
                        None
                        if row["long_term_debt"] is None
                        else row["long_term_debt"] / row["assets"]
                    ),
                    "cash_usd": row["cash"],
                }
            )

    by_year_metrics: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in annual_metrics:
        by_year_metrics[item["fiscal_year"]].append(item)
    peer_dispersion = {}
    for fiscal_year, items in sorted(by_year_metrics.items()):
        if len(items) != len(by_entity_rows):
            raise ValueError(f"Peer panel is incomplete for FY{fiscal_year}.")
        for field in (
            "gross_margin",
            "operating_margin",
            "net_margin",
            "operating_cash_flow_margin",
            "net_working_capital_cycle_days",
        ):
            field_values = [float(item[field]) for item in items]
            field_median = statistics.median(field_values)
            reverse = field != "net_working_capital_cycle_days"
            ordered = sorted(items, key=lambda item: item[field], reverse=reverse)
            for rank, item in enumerate(ordered, start=1):
                item[f"peer_median_{field}"] = field_median
                item[f"peer_gap_{field}"] = item[field] - field_median
                item[f"peer_rank_{field}"] = rank
        margins = [item["operating_margin"] for item in items]
        cycles = [item["net_working_capital_cycle_days"] for item in items]
        peer_dispersion[str(fiscal_year)] = {
            "operating_margin_range": max(margins) - min(margins),
            "working_capital_cycle_range_days": max(cycles) - min(cycles),
        }

    config = load_json(project_root / "config.json")
    alert_ratio = config["parameters"]["cash_conversion_alert_ratio"]
    entity_summaries: dict[str, dict[str, Any]] = {}
    stress: list[dict[str, Any]] = []
    for entity in sorted(by_entity_rows):
        metrics = [
            item for item in annual_metrics if item["entity"] == entity
        ]
        latest = metrics[-1]
        ratios = [
            item["cash_earnings_ratio"]
            for item in metrics
            if item["cash_earnings_ratio"] is not None
        ]
        entity_summaries[entity] = {
            "observations": len(metrics),
            "revenue_cagr": _growth_rate(
                metrics[0]["revenue_usd"],
                metrics[-1]["revenue_usd"],
                len(metrics) - 1,
            ),
            "latest_revenue_usd": latest["revenue_usd"],
            "mean_operating_margin": mean(
                item["operating_margin"] for item in metrics
            ),
            "operating_margin_volatility": sd(
                item["operating_margin"] for item in metrics
            ),
            "latest_operating_margin": latest["operating_margin"],
            "latest_operating_margin_peer_gap": (
                latest["peer_gap_operating_margin"]
            ),
            "latest_cash_earnings_ratio": latest["cash_earnings_ratio"],
            "cash_conversion_alert_years": sum(
                ratio < alert_ratio for ratio in ratios
            ),
            "latest_working_capital_cycle_days": (
                latest["net_working_capital_cycle_days"]
            ),
            "latest_working_capital_cycle_peer_gap_days": (
                latest["peer_gap_net_working_capital_cycle_days"]
            ),
            "latest_free_cash_flow_proxy_usd": (
                latest["free_cash_flow_proxy_usd"]
            ),
            "latest_equity_to_assets": latest["equity_to_assets"],
            "latest_long_term_debt_to_assets": (
                latest["long_term_debt_to_assets"]
            ),
        }
        for basis_points in config["parameters"]["margin_stress_basis_points"]:
            stressed_margin = latest["operating_margin"] + basis_points / 10_000
            stress.append(
                {
                    "entity": entity,
                    "fiscal_year": latest["fiscal_year"],
                    "operating_margin_change_basis_points": basis_points,
                    "stressed_operating_margin": stressed_margin,
                    "stressed_operating_income_usd": (
                        stressed_margin * latest["revenue_usd"]
                    ),
                }
            )

    common_years = sorted(by_year_metrics)
    evidence_table = {
        "panel": {
            "entities": len(by_entity_rows),
            "company_years": len(annual_metrics),
            "common_fiscal_years": common_years,
        },
        "entity_summaries": entity_summaries,
        "peer_dispersion": peer_dispersion,
        "comparison_design": (
            "Within-year peer medians and ranks use three SEC SIC 5122 firms. "
            "Ranks are descriptive and never treated as security rankings."
        ),
    }
    decision_support = {
        "question": (
            "Which recurring peer difference should receive the next layer of "
            "filing and footnote reconciliation?"
        ),
        "recommended_next_diligence": (
            "cash-conversion persistence and working-capital-cycle reconciliation"
        ),
        "why": [
            (
                "The three firms share a low-margin distribution setting, so "
                "small margin gaps are economically material even when scale differs."
            ),
            (
                "Repeated company-year cash conversion and working-capital gaps "
                "are more decision-relevant than a single latest-year ratio."
            ),
        ],
        "not_a_decision": (
            "This prioritizes analytical follow-up; it is not an investment, "
            "credit, assurance, or treasury recommendation."
        ),
        "reversal_conditions": [
            "Footnotes or taxonomy changes explain an apparent peer gap.",
            "Segment mix, acquisitions, or fiscal timing make a ratio non-comparable.",
            "A broader peer definition materially changes the cross-sectional median.",
        ],
    }
    write_json(
        project_root / "outputs/decision-support.json",
        decision_support,
    )
    result = {
        "project_id": "mckesson-financial-quality",
        "data": {
            "entities": len(by_entity_rows),
            "company_years": len(rows),
            "fiscal_years_per_entity": len(common_years),
            "period": [common_years[0], common_years[-1]],
            "entity_names": sorted(by_entity_rows),
        },
        "annual_metrics": annual_metrics,
        "evidence_table": evidence_table,
        "operating_margin_stress": stress,
        "decision_support": decision_support,
        "fact_reconciliation": (
            "Each company-year value retains entity, CIK, tag, accession, filing "
            "date, and fiscal period in outputs/fact-lineage.csv."
        ),
        "comparability_boundary": (
            "A shared SIC and common XBRL tags do not eliminate differences in "
            "business mix, accounting policy, fiscal calendars, acquisitions, "
            "or later reclassifications."
        ),
        "claim_boundary": (
            "Peer ratio analysis of SEC facts is not valuation, assurance, a "
            "credit conclusion, or an investment recommendation; full filings "
            "and footnotes remain necessary."
        ),
    }
    source = (
        "SEC XBRL Companyfacts for McKesson, Cardinal Health, and Cencora; "
        "snapshots reviewed 2026-07-27 to 2026-07-28"
    )
    figures = project_root / "outputs/figures"
    svg_line(
        figures / "revenue-scale.svg",
        "Reported annual revenue by peer",
        "Entity fiscal years 2018–2025; USD billions",
        [
            (
                entity,
                [
                    (item["fiscal_year"], item["revenue_usd"] / 1_000_000_000)
                    for item in annual_metrics
                    if item["entity"] == entity
                ],
            )
            for entity in sorted(by_entity_rows)
        ],
        source,
    )
    svg_line(
        figures / "margin-trends.svg",
        "Reported operating margin by peer",
        "Common-size ratios from reconciled annual 10-K facts",
        [
            (
                entity,
                [
                    (item["fiscal_year"], item["operating_margin"])
                    for item in annual_metrics
                    if item["entity"] == entity
                ],
            )
            for entity in sorted(by_entity_rows)
        ],
        source,
        y_percent=True,
    )
    svg_line(
        figures / "working-capital-days.svg",
        "Net working-capital cycle by peer",
        "Approximate days using entity-specific average annual balances",
        [
            (
                entity,
                [
                    (
                        item["fiscal_year"],
                        item["net_working_capital_cycle_days"],
                    )
                    for item in annual_metrics
                    if item["entity"] == entity
                ],
            )
            for entity in sorted(by_entity_rows)
        ],
        source,
    )
    svg_bar(
        figures / "cash-earnings.svg",
        "Latest fiscal-year cash-earnings ratio",
        "Operating cash flow divided by net income; FY2025",
        [
            (
                entity,
                entity_summaries[entity]["latest_cash_earnings_ratio"],
            )
            for entity in sorted(by_entity_rows)
        ],
        source,
    )
    svg_bar(
        figures / "peer-margin-gap.svg",
        "Latest operating margin by peer",
        "FY2025; dashed line marks the three-company median",
        [
            (
                entity,
                entity_summaries[entity]["latest_operating_margin"],
            )
            for entity in sorted(by_entity_rows)
        ],
        source,
        percent=True,
        benchmark=statistics.median(
            entity_summaries[entity]["latest_operating_margin"]
            for entity in by_entity_rows
        ),
    )
    return result

PORTFOLIOS = {
    "short-baseline": {"2 Yr": 0.60, "5 Yr": 0.30, "10 Yr": 0.10},
    "intermediate": {"2 Yr": 0.20, "5 Yr": 0.60, "10 Yr": 0.20},
    "barbell": {"2 Yr": 0.45, "5 Yr": 0.10, "10 Yr": 0.45},
    "long-duration": {"2 Yr": 0.10, "5 Yr": 0.20, "10 Yr": 0.70},
}
DURATIONS = {"2 Yr": 1.9, "5 Yr": 4.5, "10 Yr": 8.0}


def _portfolio_returns(rows: list[dict[str, str]], weights: dict[str, float]) -> list[tuple[str, float]]:
    values = []
    for previous, current in zip(rows, rows[1:]):
        if any(
            _safe_number(previous.get(maturity)) is None
            or _safe_number(current.get(maturity)) is None
            for maturity in weights
        ):
            continue
        daily = 0.0
        for maturity, weight in weights.items():
            yield_previous = float(previous[maturity]) / 100
            change = (float(current[maturity]) - float(previous[maturity])) / 100
            daily += weight * (yield_previous / 252 - DURATIONS[maturity] * change)
        values.append((current["date"], daily))
    return values


def _risk_metrics(returns: list[float]) -> dict[str, float]:
    q05 = quantile(returns, 0.05)
    tail = [value for value in returns if value <= q05]
    cumulative = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in returns:
        cumulative *= 1 + value
        peak = max(peak, cumulative)
        max_drawdown = max(max_drawdown, 1 - cumulative / peak)
    return {
        "annualized_mean_return": mean(returns) * 252,
        "annualized_volatility": sd(returns) * math.sqrt(252),
        "var95_loss": -q05,
        "expected_shortfall95_loss": -mean(tail),
        "worst_day_loss": -min(returns),
        "maximum_drawdown": max_drawdown,
    }


def _safe_log_probability(successes: int, total: int, probability: float) -> float:
    if total == 0:
        return 0.0
    probability = min(1 - 1e-12, max(1e-12, probability))
    return successes * math.log(probability) + (total - successes) * math.log(
        1 - probability
    )


def _rolling_var_backtest(
    returns: list[float],
    *,
    window: int = 250,
    alpha: float = 0.05,
) -> dict[str, Any]:
    if len(returns) <= window:
        raise ValueError("Rolling VaR backtest requires more rows than the window.")
    forecasts = []
    breaches = []
    for index in range(window, len(returns)):
        var_threshold = quantile(returns[index - window : index], alpha)
        forecasts.append(var_threshold)
        breaches.append(int(returns[index] < var_threshold))
    observations = len(breaches)
    exceedances = sum(breaches)
    observed_rate = exceedances / observations
    null_log = _safe_log_probability(exceedances, observations, alpha)
    fitted_log = _safe_log_probability(
        exceedances,
        observations,
        observed_rate,
    )
    kupiec_lr = max(0.0, -2 * (null_log - fitted_log))
    transitions = Counter(zip(breaches[:-1], breaches[1:]))
    n00 = transitions[(0, 0)]
    n01 = transitions[(0, 1)]
    n10 = transitions[(1, 0)]
    n11 = transitions[(1, 1)]
    p01 = n01 / (n00 + n01) if n00 + n01 else 0.0
    p11 = n11 / (n10 + n11) if n10 + n11 else 0.0
    unconditional = (n01 + n11) / max(1, n00 + n01 + n10 + n11)
    independent_log = (
        _safe_log_probability(n01, n00 + n01, unconditional)
        + _safe_log_probability(n11, n10 + n11, unconditional)
    )
    markov_log = (
        _safe_log_probability(n01, n00 + n01, p01)
        + _safe_log_probability(n11, n10 + n11, p11)
    )
    independence_lr = max(0.0, -2 * (independent_log - markov_log))
    return {
        "method": "rolling historical 5% VaR",
        "window_days": window,
        "observations": observations,
        "exceedances": exceedances,
        "observed_exceedance_rate": observed_rate,
        "expected_exceedance_rate": alpha,
        "kupiec_unconditional_coverage": {
            "lr_statistic": kupiec_lr,
            "chi_square_1df_p_approx": math.erfc(math.sqrt(kupiec_lr / 2)),
        },
        "christoffersen_independence": {
            "transition_counts": {
                "00": n00,
                "01": n01,
                "10": n10,
                "11": n11,
            },
            "lr_statistic": independence_lr,
            "chi_square_1df_p_approx": math.erfc(
                math.sqrt(independence_lr / 2)
            ),
        },
        "forecast_thresholds": forecasts,
        "breaches": breaches,
    }


def analyze_treasury(project_root: Path) -> dict[str, Any]:
    rows = read_csv(project_root / "data/processed/analysis.csv")
    portfolios = {}
    rng = random.Random(51)
    for name, weights in PORTFOLIOS.items():
        dated = _portfolio_returns(rows, weights)
        returns = [value for _, value in dated]
        metrics = _risk_metrics(returns)
        bootstrap = {key: [] for key in ("annualized_mean_return", "expected_shortfall95_loss", "worst_day_loss")}
        block = 20
        for _ in range(400):
            sample: list[float] = []
            while len(sample) < len(returns):
                start = rng.randrange(max(1, len(returns) - block))
                sample.extend(returns[start : start + block])
            sampled_metrics = _risk_metrics(sample[: len(returns)])
            for key in bootstrap:
                bootstrap[key].append(round(sampled_metrics[key], 8))
        metrics["weights"] = weights
        metrics["bootstrap"] = bootstrap
        metrics["var_exceedances"] = sum(
            value < -metrics["var95_loss"] for value in returns
        )
        metrics["observations"] = len(returns)
        backtesting = _rolling_var_backtest(returns)
        metrics["backtesting"] = {
            key: value
            for key, value in backtesting.items()
            if key not in {"forecast_thresholds", "breaches"}
        }
        regimes = {
            "covid-liquidity-shock-2020": ("2020-02-20", "2020-04-30"),
            "rapid-tightening-2022": ("2022-01-03", "2022-12-30"),
            "post-tightening-2023-2025": ("2023-01-03", "2025-12-31"),
        }
        metrics["historical_regimes"] = {}
        for regime, (start, end) in regimes.items():
            period_returns = [
                value for date, value in dated if start <= date <= end
            ]
            metrics["historical_regimes"][regime] = {
                **_risk_metrics(period_returns),
                "observations": len(period_returns),
                "source": "historical observed Treasury yield changes",
            }
        block_sensitivity = {}
        for block_size in (5, 20, 60):
            sensitivity_rng = random.Random(5100 + block_size)
            es_values = []
            for _ in range(200):
                sample: list[float] = []
                while len(sample) < len(returns):
                    start = sensitivity_rng.randrange(len(returns))
                    sample.extend(
                        returns[(start + offset) % len(returns)]
                        for offset in range(block_size)
                    )
                es_values.append(
                    _risk_metrics(sample[: len(returns)])[
                        "expected_shortfall95_loss"
                    ]
                )
            block_sensitivity[str(block_size)] = {
                "expected_shortfall95_interval": [
                    quantile(es_values, 0.025),
                    quantile(es_values, 0.975),
                ]
            }
        metrics["block_length_sensitivity"] = block_sensitivity
        portfolios[name] = metrics
    curves = {}
    for target in ("2020-12-31", "2022-12-30", "2025-12-31"):
        match = next((row for row in rows if row["date"] == target), None)
        if match:
            curves[target] = {
                maturity: float(match[maturity])
                for maturity in ("2 Yr", "5 Yr", "10 Yr", "30 Yr")
                if _safe_number(match.get(maturity)) is not None
            }
    result = {
        "project_id": "treasury-risk-engineering",
        "data": {"yield_curves": len(rows), "period": [rows[0]["date"], rows[-1]["date"]]},
        "return_model": (
            "Daily carry plus first-order duration response to official par-yield changes; "
            "no convexity, transaction cost, or tradable-index replication."
        ),
        "portfolios": portfolios,
        "yield_curve_snapshots": curves,
        "risk_boundary": "Historical simulation is not a forecast or investment recommendation.",
        "uncertainty_and_model_risk": {
            "shared_market_shocks": (
                "Every portfolio is evaluated on the same dated yield-curve changes; "
                "cross-portfolio losses are therefore correlated by construction."
            ),
            "fat_tails": "Historical VaR and ES retain the empirical return tail.",
            "parameter_instability": (
                "Rolling coverage tests and 5/20/60-day block sensitivities expose "
                "window and dependence assumptions."
            ),
            "liquidity_and_costs": (
                "No security-level bid-ask spread, financing cost, rebalancing cost, "
                "or market-depth model is available; results are pre-cost."
            ),
            "regime_change": (
                "COVID-liquidity, 2022 tightening, and post-tightening periods are "
                "reported separately rather than pooled without comment."
            ),
        },
        "implementation": {
            "use": "historical risk review only",
            "monitor": [
                "rolling VaR breach rate",
                "breach clustering",
                "duration approximation error",
                "liquidity and transaction cost",
            ],
            "reversal_conditions": [
                "Coverage or independence tests reject the historical model.",
                "Portfolio instruments have material convexity or basis risk.",
                "Trading costs or liquidity erase the apparent carry advantage.",
            ],
        },
    }
    source = "U.S. Treasury Daily Par Yield Curve Rates, 2020–2025"
    figures = project_root / "outputs/figures"
    maturities = {"2 Yr": 2.0, "5 Yr": 5.0, "10 Yr": 10.0, "30 Yr": 30.0}
    svg_line(
        figures / "yield-curves.svg",
        "Selected Treasury par yield curves",
        "Official annualized yields at four maturities",
        [
            (
                date,
                [(maturities[maturity], value) for maturity, value in curve.items()],
            )
            for date, curve in curves.items()
        ],
        source,
    )
    svg_bar(
        figures / "expected-shortfall.svg",
        "Historical 95% expected shortfall by portfolio",
        "Daily loss fraction under the duration approximation, 2020–2025",
        [
            (name.replace("-", " ").title(), value["expected_shortfall95_loss"])
            for name, value in portfolios.items()
        ],
        source,
        percent=True,
    )
    svg_bar(
        figures / "var-backtest.svg",
        "Rolling historical VaR exceedance rate",
        "250-day window; benchmark is 5% under correct unconditional coverage",
        [
            (
                name.replace("-", " ").title(),
                value["backtesting"]["observed_exceedance_rate"],
            )
            for name, value in portfolios.items()
        ],
        source,
        percent=True,
        benchmark=0.05,
    )
    return result

__all__ = [name for name in globals() if not name.startswith("__")]
