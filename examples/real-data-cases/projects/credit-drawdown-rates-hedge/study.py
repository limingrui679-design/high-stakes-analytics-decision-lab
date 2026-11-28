import math
from statistics import mean

from applied_metrics import figure, result


def beta(values, factor):
    centre = mean(factor)
    asset_mean = mean(values)
    ss = sum((f - centre) ** 2 for f in factor)
    return (
        sum((x - asset_mean) * (f - centre) for x, f in zip(values, factor, strict=False)) / ss
        if ss
        else 0
    )


def drawdown(values):
    x = peak = 1
    worst = 0
    for r in values:
        x *= 1 + r
        peak = max(peak, x)
        worst = min(worst, x / peak - 1)
    return worst


def evaluate(rows, p, seed):
    records = [(r["week"], *[float(r[k]) for k in ("LQD", "IEF", "SHY", "TLT")]) for r in rows]
    width = p["lookback_weeks"]
    cost = p["one_way_cost_bps"] / 10000
    names = ["Hold credit", "Cut credit", "Hedge rates"]
    history = {n: [] for n in names}
    last = {n: (1, 0, 0, 0) for n in names}
    mismatches = []
    active = 0
    for i in range(width, len(records)):
        t, *current = records[i]
        past = records[i - width : i]
        factor = [r[2] - r[3] for r in past]
        b = [beta([r[j] - r[3] for r in past], factor) for j in range(1, 5)]
        stressed = math.prod(1 + x[1] for x in past[-8:]) - 1 < -p["trailing_loss_trigger"]
        alpha = p["credit_cut"] if stressed else 0
        # A Treasury/short-bill overlay is self-financing. Beta is estimated
        # for excess returns. Target the rate exposure of the cut-credit option.
        hedge = alpha * b[0] / b[3] if abs(b[3]) > 0.15 else 0
        hedge = max(-1, min(1, hedge))
        ws = [(1, 0, 0, 0), (1 - alpha, 0, alpha, 0), (1, 0, hedge, -hedge)]
        if stressed:
            active += 1
            mismatches.append(
                abs(sum((x - y) * z for x, y, z in zip(ws[1], ws[2], b, strict=False)))
            )
        for n, w in zip(names, ws, strict=False):
            tr = sum(abs(x - y) for x, y in zip(w, last[n], strict=False))
            gross = sum(x * r for x, r in zip(w, current, strict=False))
            history[n].append((t, gross, tr, gross - cost * tr, stressed))
            # Rebalance to target after weights drift with realized weekly returns.
            last[n] = tuple(
                weight * (1 + rr) / (1 + gross) for weight, rr in zip(w, current, strict=False)
            )
    ret = {
        n: 100 * (math.prod(1 + x[3] for x in g) ** (52 / len(g)) - 1) for n, g in history.items()
    }
    dd = {n: 100 * drawdown([x[3] for x in g]) for n, g in history.items()}
    turnover = {n: 52 * mean(x[2] for x in g) for n, g in history.items()}
    regimes = {}
    for name, start, end in [
        ("Credit crisis", "2008-01", "2009-07"),
        ("COVID shock", "2020-02", "2020-05"),
        ("Rate repricing", "2022-01", "2023-01"),
    ]:
        regimes[name] = {
            n: 100 * (math.prod(1 + x[3] for x in g if start <= x[0] < end) - 1)
            for n, g in history.items()
        }
    # These revised monthly regimes are descriptive labels and never enter the trading rule.
    retrospective = {
        r["week"]: (float(r["spread_change_bp"]), float(r["rate_change_bp"]))
        for r in rows
        if r["spread_change_bp"] and r["rate_change_bp"]
    }
    regimes_by_change = {}
    for title, predicate in [
        ("Spread widens at least 25 bp", lambda s, y: s >= 25),
        ("Treasury rises at least 25 bp", lambda s, y: y >= 25),
        ("Both widen/rise by 25 bp", lambda s, y: s >= 25 and y >= 25),
    ]:
        performance = {}
        for n, g in history.items():
            selected = [
                x[3] for x in g if x[0] in retrospective and predicate(*retrospective[x[0]])
            ]
            performance[n] = {
                "weeks": len(selected),
                "mean_net_weekly_bps": 10000 * mean(selected) if selected else None,
            }
        regimes_by_change[title] = performance
    diff = sum(
        x[1] - y[1] for x, y in zip(history["Hedge rates"], history["Cut credit"], strict=False)
    )
    trade = sum(
        x[2] - y[2] for x, y in zip(history["Hedge rates"], history["Cut credit"], strict=False)
    )
    return result(
        f"Over {len(history[names[0]])} held-out weeks, the rule triggered {active} times. The modeled net maximum drawdown was {dd['Cut credit']:.2f}% after cutting credit and {dd['Hedge rates']:.2f}% under the matched-rate hedge.",
        {
            "Backtest weeks": len(history[names[0]]),
            "Triggered weeks": active,
            "One-way costs": f"{p['one_way_cost_bps']} bp",
        },
        [
            figure(
                "Compounded total return after trading costs",
                "Annualized percent",
                ret,
                "Fund inputs are weekly NAV total returns with ex-date distributions reinvested.",
            ),
            figure(
                "Peak-to-trough drawdown",
                "Percent",
                dd,
                "The same lagged signal and transaction cost convention apply to every strategy.",
            ),
            figure(
                "Crisis-window portfolio returns",
                "Net percent in the 2022 rate repricing",
                regimes["Rate repricing"],
                "Named historical windows are descriptive stress checks.",
            ),
        ],
        {
            "monthly_regime_returns": regimes_by_change,
            "annualized_return_pct": ret,
            "drawdown_pct": dd,
            "annualized_one_way_turnover": turnover,
            "regimes": regimes,
            "mean_abs_ex_ante_beta_mismatch": mean(mismatches),
            "gross_linear_pnl_break_even_bps": 10000 * diff / trade if trade else None,
            "assumed_cost_bps": p["one_way_cost_bps"],
            "duration_proxy": "52-week Treasury factor sensitivity",
        },
        "Use the matched-rate comparison and stress-period outcomes to distinguish spread/liquidity exposure from rate sensitivity. The turnover threshold identifies when modeled trading costs reverse the gross comparison.",
    )
