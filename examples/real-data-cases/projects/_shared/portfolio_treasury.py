#!/usr/bin/env python3
"""Treasury market-risk analysis module."""

from __future__ import annotations

from portfolio_core import *

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

