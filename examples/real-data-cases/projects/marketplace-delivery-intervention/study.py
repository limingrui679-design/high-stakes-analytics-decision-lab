from collections import Counter, defaultdict
from statistics import mean

from applied_metrics import figure, result


def quarter(month):
    return int(month[:4]) * 4 + (int(month[5:]) - 1) // 3


def evaluate(rows, p, seed):
    obs = [r for r in rows if r["late"] != "" and r["handoff_late"] != ""]
    for r in obs:
        r["q"] = quarter(r["month"])
        r["end"] = int(r["late"])
        r["up"] = int(r["handoff_late"]) * r["end"]
        r["down"] = (1 - int(r["handoff_late"])) * r["end"]
        r["mix"] = (r["category"], r["origin"] == r["destination"], r["destination"])
        r["lane"] = (r["origin"], r["destination"])
    quarters = sorted({r["q"] for r in obs})
    # Exclude partial start/end quarters and avoid using orders whose outcome
    # arrives after the simulated quarter boundary.
    full = [q for q in quarters if q >= 2017 * 4 + 2 and q <= 2018 * 4 + 1]
    totals = defaultdict(Counter)
    audit = []
    for q in full:
        hist = [r for r in obs if q - 4 <= r["q"] < q and quarter(r["known_month"]) < q]
        test = [r for r in obs if r["q"] == q]
        if not hist or not test:
            continue
        by = defaultdict(list)
        mix = defaultdict(list)
        for r in hist:
            by[r["seller"]].append(r)
            mix[r["mix"]].append(r)
        global_rate = mean(r["up"] for r in hist)
        total_rate = mean(r["end"] for r in hist)
        strength = p["prior_orders"]
        rate = {
            k: (sum(r["up"] for r in g) + strength * global_rate) / (len(g) + strength)
            for k, g in mix.items()
        }
        raw = {}
        adj = {}
        carrier = {}
        lanes = defaultdict(list)
        for r in hist:
            lanes[r["lane"]].append(r)
        downstream_mean = mean(r["down"] for r in hist)
        for lane, g in lanes.items():
            carrier[lane] = (sum(r["down"] for r in g) + strength * downstream_mean) / (
                len(g) + strength
            )
        for s, g in by.items():
            raw[s] = (sum(r["end"] for r in g) + strength * total_rate) / (len(g) + strength)
            adj[s] = (sum(r["up"] - rate[r["mix"]] for r in g)) / (len(g) + strength) + global_rate
        b = min(p["quarterly_audit_orders"], len(test))
        first = sorted(test, key=lambda r: r["id"])

        def put(
            name,
            scores,
            key="seller",
            fallback=None,
            candidates=first,
            population_rate=global_rate,
            capacity=b,
        ):
            # Precommit seller priority before observing outcomes. Within sellers
            # the public order-ID tie-break is fixed without reading outcomes.
            ranked = sorted(
                candidates,
                key=lambda r: (
                    -scores.get(r[key], population_rate if fallback is None else fallback)
                ),
            )
            chosen = ranked[:capacity]
            stats = totals[name]
            for k in ("up", "down", "end"):
                stats[k] += sum(r[k] for r in chosen)
            stats["count"] += capacity

        put("Order volume", {s: len(g) for s, g in by.items()}, fallback=0)
        put("Overall lateness", raw)
        put("Case-adjusted handoff", adj)
        put("Post-handoff delay", carrier, "lane", downstream_mean)
        audit.append(
            {
                "quarter": f"{q // 4}Q{q % 4 + 1}",
                "priority_sellers": sorted(adj, key=adj.get, reverse=True)[:5],
                "priority_lanes": [
                    list(x) for x in sorted(carrier, key=carrier.get, reverse=True)[:5]
                ],
                "mature_training_orders": len(hist),
                "held_out_orders": len(test),
                "slots": b,
            }
        )
    up = {k: 100 * g["up"] / g["count"] for k, g in totals.items()}
    down = {k: 100 * g["down"] / g["count"] for k, g in totals.items()}
    a = totals["Case-adjusted handoff"]
    c = totals["Post-handoff delay"]
    boundary = a["up"] / c["down"] if c["down"] else None
    return result(
        f"Across {len(audit)} future quarters and {a['count']:,} equal review slots per policy, adjusted seller targeting found {a['up']} late deliveries following a missed handoff deadline. Carrier-focused targeting found {c['down']} late deliveries after on-time handoff.",
        {
            "Single-item orders": len(rows),
            "Complete handoff and delivery": len(obs),
            "Policy slots": a["count"],
        },
        [
            figure(
                "Late deliveries with late handoff",
                "Per 100 review slots",
                up,
                "Groups are prioritized using only matured prior-quarter outcomes.",
            ),
            figure(
                "Late deliveries after on-time handoff",
                "Per 100 review slots",
                down,
                "This decomposition identifies the timing of a delay, not the responsible party.",
            ),
            figure(
                "Equal-effectiveness scenario at different carrier costs",
                "Modeled relative benefit per unit cost",
                {str(x) + "× carrier cost": (c["down"] / x) / max(1, a["up"]) for x in (0.5, 1, 2)},
                "Compare against 1.0. Relative intervention effectiveness and unit cost are assumptions.",
            ),
        ],
        {
            "quadrants": {
                f"handoff {h}, delivery {late}": sum(
                    r["handoff_late"] == str(h) and r["late"] == str(late) for r in rows
                )
                for h in (0, 1)
                for late in (0, 1)
            },
            "unknown_hand_or_delivery": len(rows) - len(obs),
            "quarter_splits": audit,
            "policies": {k: dict(v) for k, v in totals.items()},
            "carrier_to_seller_effectiveness_break_even_at_equal_cost": boundary,
        },
        "Match proposed seller coaching or carrier service review to the observed stage. With equal per-order costs, choose carrier review only above the reported relative-effectiveness crossover; estimate effects prospectively.",
    )
