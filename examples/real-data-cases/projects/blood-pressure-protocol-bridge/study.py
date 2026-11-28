"""Leave-one-PSU-out protocol bridge with a stratified survey linearization."""

import math
from collections import defaultdict

from applied_metrics import figure, result


def estimate(rows, value):
    return sum(r[3] * value(r) for r in rows) / sum(r[3] for r in rows)


def survey_summary(rows, value, domain=lambda row: True):
    """Ratio linearization, with within-stratum variance of PSU-level residual totals."""
    domain_rows = [r for r in rows if domain(r)]
    total = sum(r[3] for r in domain_rows)
    mu = estimate(domain_rows, value)
    psu = defaultdict(lambda: defaultdict(float))
    for r in rows:
        psu[r[1]][r[2]] += r[3] * (value(r) - mu) / total if domain(r) else 0
    variance = 0
    for clusters in psu.values():
        m = len(clusters)
        if m < 2:
            raise ValueError("Design-based interval needs two observed PSUs per stratum")
        centre = sum(clusters.values()) / m
        variance += m / (m - 1) * sum((x - centre) ** 2 for x in clusters.values())
    return {
        "estimate": mu,
        "se": math.sqrt(variance),
        "normal_95": [mu - 1.96 * math.sqrt(variance), mu + 1.96 * math.sqrt(variance)],
    }


def group(r):
    return "18–39" if r[0] < 40 else "40–59" if r[0] < 60 else "60+"


def evaluate(records, par, seed):
    rows = [
        (
            int(a["age"]),
            int(a["stratum"]),
            int(a["psu"]),
            float(a["weight"]),
            int(a["minutes"]),
            float(a["manual"]),
            float(a["automatic"]),
        )
        for a in records
    ]

    def diff(r):
        return r[5] - r[6]

    clusters = sorted({(r[1], r[2]) for r in rows})
    predictions = []
    for block in clusters:
        train = [r for r in rows if (r[1], r[2]) != block]
        offsets = {"pooled": estimate(train, diff)}
        for k in ("18–39", "40–59", "60+"):
            g = [r for r in train if group(r) == k]
            # Kish effective size prevents unequal weights from dominating the prior.
            eff = sum(r[3] for r in g) ** 2 / sum(r[3] ** 2 for r in g)
            offsets[k] = (eff * estimate(g, diff) + par["prior_people"] * offsets["pooled"]) / (
                eff + par["prior_people"]
            )
        for r in rows:
            if (r[1], r[2]) == block:
                predictions.append((*r, r[6] + offsets["pooled"], r[6] + offsets[group(r)]))
    error = {
        k: estimate(predictions, lambda r, i=i: abs(r[i] - r[5]))
        for k, i in [("Unadjusted", 6), ("Pooled offset", 7), ("Age shrinkage", 8)]
    }
    rates = {}
    for t in par["thresholds_mmHg"]:
        rates[t] = {
            k: 100 * estimate(rows, func)
            for k, func in [
                ("up", lambda r, t=t: r[5] < t <= r[6]),
                ("down", lambda r, t=t: r[6] < t <= r[5]),
                ("manual", lambda r, t=t: r[5] >= t),
                ("automatic", lambda r, t=t: r[6] >= t),
            ]
        }
        rates[t]["net_pp"] = survey_summary(
            rows, lambda r, t=t: 100 * (int(r[6] >= t) - int(r[5] >= t))
        )
    order = {
        k: estimate([r for r in rows if cond(r)], lambda r: -diff(r))
        for k, cond in [
            ("Manual first", lambda r: r[4] > 0),
            ("Automatic first", lambda r: r[4] < 0),
            ("Within 2 hours", lambda r: abs(r[4]) <= 120),
        ]
    }
    by_age = {}
    for band in ("18–39", "40–59", "60+"):
        switches = {}
        for direction, indicator in (
            ("up", lambda r: r[5] < 130 <= r[6]),
            ("down", lambda r: r[6] < 130 <= r[5]),
        ):
            switches[direction] = survey_summary(
                rows, lambda r, fn=indicator: 100 * fn(r), lambda r, b=band: group(r) == b
            )
        by_age[band] = switches
    bias = survey_summary(rows, lambda r: -diff(r))
    main = rates[130]
    return result(
        f"Across {len(rows):,} paired adults, the survey-weighted automatic-minus-manual mean was {bias['estimate']:.2f} mmHg. At 130 mmHg, {main['up']:.2f}% moved above and {main['down']:.2f}% moved below the cutoff.",
        {
            "Paired adults": len(rows),
            "Held-out PSUs": len(clusters),
            "Weighted paired difference": f"{bias['estimate']:.2f} mmHg",
        },
        [
            figure(
                "Prediction of the manual protocol in held-out PSUs",
                "Weighted mean absolute error (mmHg)",
                error,
                "Every calibration excludes the complete test sampling unit.",
            ),
            figure(
                "Which participants cross the analysis threshold?",
                "Weighted percent of paired adults",
                {f"{t} {k}": v[k] for t, v in rates.items() for k in ("up", "down")},
                "Movement up and down can cancel in a prevalence difference.",
            ),
            figure(
                "Protocol difference by measurement sequence",
                "Automatic minus manual (mmHg)",
                order,
                "Signed elapsed time orders examinations. The within-two-hour subset tests time separation.",
            ),
        ],
        {
            "age_group_crossings_at_130_pct": by_age,
            "bias": bias,
            "thresholds": rates,
            "calibration": error,
            "order": order,
            "n": len(rows),
            "strata": len({r[1] for r in rows}),
            "psus": len(clusters),
            "at_least_two": True,
        },
        "For a surveillance trend crossing the protocol change, publish weighted directional switches and uncertainty alongside the series; use held-out error to choose any bridge.",
    )
