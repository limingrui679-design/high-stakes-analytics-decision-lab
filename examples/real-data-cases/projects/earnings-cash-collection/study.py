from collections import defaultdict
from datetime import date
from statistics import mean

from applied_metrics import figure, result


def fit(xy):
    size = len(xy[0][0])
    a = [
        [sum(x[i] * x[j] for x, y in xy) + (0.05 if i == j and i else 0) for j in range(size)]
        + [sum(x[i] * y for x, y in xy)]
        for i in range(size)
    ]
    for i in range(size):
        pivot = max(range(i, size), key=lambda j: abs(a[j][i]))
        a[i], a[pivot] = a[pivot], a[i]
        scale = a[i][i]
        if abs(scale) < 1e-10:
            return [mean(y for x, y in xy)] + [0.0] * (size - 1)
        a[i] = [v / scale for v in a[i]]
        for j in range(size):
            if j != i:
                factor = a[j][i]
                a[j] = [b - factor * c for b, c in zip(a[j], a[i], strict=False)]
    return [r[-1] for r in a]


def evaluate(rows, p, seed):
    v = defaultdict(list)
    for r in rows:
        v[r["cik"], r["end"]].append(r)
    originals = defaultdict(list)
    changes = 0
    for (issuer, end), rs in sorted(v.items()):
        os = sorted(
            [
                r
                for r in rs
                if r["form"] == "10-K"
                and (date.fromisoformat(r["filed"]) - date.fromisoformat(end)).days <= 180
            ],
            key=lambda r: (r["filed"], r["accession"]),
        )
        if not os:
            continue
        first = os[0]
        if any(
            r["income"] and first["income"] and float(r["income"]) != float(first["income"])
            for r in rs
            if r["filed"] > first["filed"]
        ):
            changes += 1
        originals[issuer].append(first)
    dataset = []
    for issuer, fs in originals.items():
        fs.sort(key=lambda r: r["end"])
        for x, y, z in zip(fs, fs[1:], fs[2:], strict=False):
            if not all(
                320
                <= (date.fromisoformat(r["end"]) - date.fromisoformat(earlier["end"])).days
                <= 390
                for earlier, r in [(x, y), (y, z)]
            ):
                continue
            if not all(
                r[k] != ""
                for r, keys in [
                    (x, ("assets", "receivables", "inventory")),
                    (y, ("assets", "receivables", "inventory", "income", "cfo")),
                    (z, ("cfo", "income")),
                ]
                for k in keys
            ):
                continue
            opening = float(x["assets"])
            closing = float(y["assets"])
            if min(opening, closing) <= 0:
                continue
            ni = float(y["income"]) / opening
            cash = float(y["cfo"]) / opening
            feat = [
                1.0,
                ni,
                cash,
                (float(y["receivables"]) - float(x["receivables"])) / opening,
                (float(y["inventory"]) - float(x["inventory"])) / opening,
            ]
            dataset.append(
                (
                    y["filed"],
                    z["filed"],
                    issuer,
                    feat,
                    float(z["cfo"]) / closing,
                    y["accession"],
                    float(z["income"]) / closing,
                )
            )
    trials = []
    earnings = []
    for filed, _out, issuer, x, label, _ac, next_income in sorted(dataset):
        hist = [(r[3], r[4]) for r in dataset if r[1] < filed]
        peer = [(r[3], r[4]) for r in dataset if r[1] < filed and r[2] != issuer]
        if len(hist) < p["min_matured"] or len(peer) < p["min_matured"]:
            continue
        full = fit(hist)
        wo = fit(peer)

        def predicted(b, x=x):
            return sum(s * t for s, t in zip(b, x, strict=False))

        accrual_income = fit([(r[3], r[6]) for r in dataset if r[1] < filed])
        earnings.append(
            (
                next_income,
                {
                    "CFO persistence": x[2],
                    "Earnings persistence": x[1],
                    "Accrual components": predicted(accrual_income),
                },
            )
        )
        trials.append(
            (
                issuer,
                filed,
                label,
                {
                    "CFO persistence": x[2],
                    "Earnings persistence": x[1],
                    "Accrual components": predicted(full),
                    "Other-firm fit": predicted(wo),
                },
                x[1] - x[2],
            )
        )
    names = list(trials[0][3])
    mae = {m: 100 * mean(abs(y - q[m]) for _, __, y, q, g in trials) for m in names}
    by_year = {
        k: 100
        * mean(
            abs(v[2] - v[3]["CFO persistence"]) - abs(v[2] - v[3]["Accrual components"])
            for v in trials
            if v[1][:4] == k
        )
        for k in sorted({r[1][:4] for r in trials})
    }
    apple = [r for r in originals["CIK0000320193"] if r["equity"] and r["income"]]
    apple.sort(key=lambda r: r["end"])
    latest = apple[-1]
    previous = apple[-2]
    book = float(latest["equity"])
    roe = float(latest["income"]) / float(previous["equity"])
    # Fully distributed earnings; constant opening book. Explicit discounted
    # residual-income stream with persistence omega and no terminal premium.
    sensitivity = {
        f"{r:.0%} cost / {w:.1f} decay": 1 + (roe - r) / (1 + r - w)
        for r in [0.08, 0.10, 0.12]
        for w in [0.3, 0.6, 0.8]
    }
    # Explicit one-year credit-loss shock: a stated fraction of reported trade receivables
    # is uncollectible and expensed once at year 1, with no tax shield or later recovery.
    trade_receivables = float(latest["receivables"])
    collection_sensitivity = {
        str(haircut): book * sensitivity["10% cost / 0.6 decay"]
        - haircut * trade_receivables / 1.10
        for haircut in (0, 0.05, 0.10, 0.20)
    }
    earnings_mae = {
        key: 100 * mean(abs(y - pred[key]) for y, pred in earnings) for key in earnings[0][1]
    }
    return result(
        f"Across {len(trials)} out-of-time company-year forecasts, next-year operating-cash-flow MAE was {mae['CFO persistence']:.2f}% of opening assets for cash persistence and {mae['Accrual components']:.2f}% for the accrual model.",
        {
            "Issuers with evaluated forecasts": len({v[0] for v in trials}),
            "Forecasts": len(trials),
            "Later comparative earnings changes": changes,
        },
        [
            figure(
                "One-year-ahead cash-flow forecasts",
                "Mean absolute error (% of target year's opening assets)",
                mae,
                "Each fitted model sees only labels publicly filed before the forecast.",
            ),
            figure(
                "Does the cash advantage persist by year?",
                "MAE improvement over cash persistence (pp)",
                dict(list(by_year.items())[-8:]),
                "Negative values mean the accrual model lost to cash persistence.",
            ),
            figure(
                "Apple residual-income sensitivity",
                "Modeled price / opening book",
                sensitivity,
                "Scenario valuation holds book fixed under full payout. The cost of equity and persistence are assumptions.",
            ),
        ],
        {
            "observed_vintages": len(rows),
            "first_report_issuers": len(originals),
            "forecast_count": len(trials),
            "mae_pct": mae,
            "earnings_target_mae_pct": earnings_mae,
            "yearly_improvement_pp": by_year,
            "loss_by_cash_gap": {
                "positive": sum(t[4] > 0 for t in trials),
                "nonpositive": sum(t[4] <= 0 for t in trials),
            },
            "valuation": {
                "issuer": "Apple",
                "accession": latest["accession"],
                "trade_receivables_usd_m": trade_receivables,
                "collection_sensitivity_usd_m": collection_sensitivity,
                "collection_assumptions": "One-time year-one loss as a fraction of trade receivables with other cash flows and full-payout baseline held fixed; no tax shield.",
                "opening_book_for_projection_usd_m": book,
                "observed_roe": roe,
                "price_to_book_scenarios": sensitivity,
                "valuation_usd_m": {k: book * vv for k, vv in sensitivity.items()},
            },
            "audited_note": "Apple FY2023 Form 10-K, printed page 38: vendor non-trade receivables arise from components supplied to manufacturing vendors. The two largest counterparties accounted for 48% and 23%. Audit trade and vendor receivables separately before interpreting collections.",
            "chronology": "New annual originals only for forecast features. Later amended or repeated comparative values are retained separately for auditing.",
        },
        "Investigate persistent cash-collection gaps alongside the audited note, industry and fiscal period. Use issuer-specific balance-sheet classifications before applying a valuation haircut.",
    )
