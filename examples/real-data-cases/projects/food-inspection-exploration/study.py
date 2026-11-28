import random
from collections import Counter, defaultdict
from statistics import mean

from applied_metrics import figure, result


def offer(g, scores, budget, fraction, rng):
    ordered = sorted(g, key=lambda r: (-scores[r["license"]], r["license"]))
    m = round(budget * fraction)
    targeted = ordered[: budget - m]
    others = ordered[budget - m :]
    strata = defaultdict(list)
    for r in others:
        strata[r["area"]].append(r)
    quotas = Counter()
    for _ in range(m):
        # Allocate one slot to the geographically least-covered remaining stratum.
        k = min(
            (s for s in strata if quotas[s] < len(strata[s])),
            key=lambda s: (quotas[s] / len(strata[s]), s),
        )
        quotas[k] += 1
    selected = targeted[:]
    for k, gk in sorted(strata.items()):
        selected += rng.sample(gk, quotas[k])
    return selected, {
        k: {
            "eligible_after_exploitation": len(v),
            "random_draws": quotas[k],
            "pi": quotas[k] / len(v),
        }
        for k, v in strata.items()
    }


def evaluate(rows, p, seed):
    quarters = defaultdict(list)
    for r in rows:
        quarters[r["quarter"]].append(r)
    rng = random.Random(seed)
    totals = defaultdict(Counter)
    group = defaultdict(Counter)
    design = {}
    logged = defaultdict(list)
    timing = defaultdict(list)
    log_example = []
    for date, g in sorted(quarters.items()):
        if date < "2013-01-01":
            continue
        hist = [r for t, h in quarters.items() if t < date for r in h if r["outcome"] != ""]
        levels = defaultdict(list)
        for r in hist:
            levels[r["risk"], r["last_critical"]].append(int(r["outcome"]))
        rate = mean(int(r["outcome"]) for r in hist)
        score = {}
        for r in g:
            a = levels[r["risk"], r["last_critical"]]
            score[r["license"]] = (sum(a) + 20 * rate) / (len(a) + 20) + 0.08 * (
                int(r["critical_history"]) + rate * 3
            ) / (int(r["prior_visits"]) + 3)
        methods = {
            "Calendar": sorted(g, key=lambda r: (-int(r["days_since"]), r["license"]))[: p["slots"]]
        }
        for f in [0, 0.10, 0.25, 0.5]:
            chosen, details = offer(g, score, p["slots"], f, rng)
            name = f"Risk + {f:.0%} audit"
            methods[name] = chosen
            if f == 0.25:
                design[date] = details
                if not log_example:
                    targeted = {
                        r["license"]
                        for r in sorted(g, key=lambda r: (-score[r["license"]], r["license"]))[
                            : p["slots"] - round(0.25 * p["slots"])
                        ]
                    }
                    log_example = [
                        {
                            "quarter": date,
                            "license": r["license"],
                            "area": r["area"],
                            "policy": "targeted" if r["license"] in targeted else "stratified draw",
                            "inclusion_probability": 1
                            if r["license"] in targeted
                            else details[r["area"]]["pi"],
                        }
                        for r in chosen
                    ]
        seen = {r["license"] for r in g if r["outcome"] != ""}
        for name, chosen in methods.items():
            c = totals[name]
            c["selected"] += len(chosen)
            c["known"] += sum(r["outcome"] != "" for r in chosen)
            c["critical"] += sum(r["outcome"] == "1" for r in chosen)
            c["unknown"] += sum(r["outcome"] == "" for r in chosen)
            for r in chosen:
                group[name][r["area"]] += 1
            eligible = [r for r in g if r["license"] in seen]
            cal = sorted(eligible, key=lambda r: (-int(r["days_since"]), r["license"]))
            if name == "Calendar":
                historical = cal[: p["slots"]]
            else:
                historical, _ = offer(
                    eligible, score, p["slots"], int(name.split()[2][:-1]) / 100, rng
                )
            logged[name].append(sum(r["outcome"] == "1" for r in historical))
            # Assign shortlisted visits to the quarter's earliest actual slots; other inspected
            # restaurants retain their original relative order. Outcomes are held fixed.
            chosen_ids = {r["license"] for r in historical}
            ordered = historical + sorted(
                (r for r in eligible if r["license"] not in chosen_ids),
                key=lambda r: (int(r["inspection_day"]), r["license"]),
            )
            slots = sorted(int(r["inspection_day"]) for r in eligible)
            timing[name].extend(
                int(r["inspection_day"]) - assigned
                for r, assigned in zip(ordered, slots, strict=False)
                if r["outcome"] == "1"
            )
    lo = {k: 100 * c["critical"] / c["selected"] for k, c in totals.items()}
    hi = {k: 100 * (c["critical"] + c["unknown"]) / c["selected"] for k, c in totals.items()}
    k = "Risk + 25% audit"
    c = totals[k]
    return result(
        f"The 25% exploration policy allocated {c['selected']:,} slots over {len(design)} quarters. Historical results were observable for {c['known']} selections, giving full-roster critical-finding bounds of {lo[k]:.1f}% to {hi[k]:.1f}%.",
        {
            "Eligible restaurant-quarters": len(rows),
            "Exploration-policy reviews": c["selected"],
            "Unobserved selected outcomes": c["unknown"],
        },
        [
            figure(
                "Retrospective ranking where an outcome is observed",
                "Mean critical inspections per quarter",
                {m: mean(v) for m, v in logged.items()},
                "Only the historically inspected subset enters this conditional replay.",
            ),
            figure(
                "Unknown outcomes at fixed inspection capacity",
                "Percent of selections",
                {m: 100 * v["unknown"] / v["selected"] for m, v in totals.items()},
                "Wider bounds identify the cost of selective outcome observation.",
            ),
            figure(
                "Where mixed-policy inspection slots went",
                "Selected restaurant-quarters",
                group[k],
                "The audit sample has known selection probabilities within each fixed geographic band.",
            ),
        ],
        {
            "mean_days_earlier_logged_critical": {k: mean(v) for k, v in timing.items()},
            "randomization_ledger_first_quarter": log_example,
            "all_roster_lower_pct": lo,
            "all_roster_upper_pct": hi,
            "policy_counts": {k: dict(v) for k, v in totals.items()},
            "geo_selections": {k: dict(v) for k, v in group.items()},
            "prospective_randomization": design,
            "conditional_replay_counts": dict(logged),
        },
        "Implement exploration as a recorded randomized sample of the non-targeted eligible roster, retaining each stratum's probability. Evaluate future yield with design weights and geographic coverage.",
    )
