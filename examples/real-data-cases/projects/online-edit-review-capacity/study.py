"""Finite inventory allocation with time-of-day opportunity costs and two oracle bounds."""

from collections import Counter, defaultdict
from datetime import date, timedelta
from math import ceil
from statistics import mean

from applied_metrics import figure, quantile, result


def evaluate(rows, p, seed):
    days = defaultdict(list)

    def feature(r):
        d = int(r["change"])
        return (
            int(r["anonymous"]),
            ("remove" if d < -20 else "insert" if d > 300 else "small"),
            int(r["minor"]),
        )

    for r in rows:
        days[r["ts"][:10]].append(
            (r["ts"][11:], int(r["revision"]), feature(r), int(r["reverted"]))
        )
    for g in days.values():
        g.sort()
    today = date.fromisoformat(p["holdout_start"])
    mature = (today - timedelta(days=7)).isoformat()
    train = {d: g for d, g in days.items() if d < mature}
    test = {d: g for d, g in sorted(days.items()) if d >= today.isoformat()}
    counts = defaultdict(Counter)
    alln = allhits = 0
    for g in train.values():
        for _, __, x, y in g:
            counts[x][y] += 1
            alln += 1
            allhits += y
    overall = allhits / alln

    def risk(x):
        c = counts[x]
        return (c[1] + 30 * overall) / (sum(c.values()) + 30)

    capacity = p["slots_per_day"]
    # Learn an empirical distribution for each hourly arrival count and score.
    # Within an hour use a fixed training-only opportunity schedule with the
    # expected remaining arrivals. During replay no session length is revealed.
    groups = [[] for _ in range(24)]
    for h in range(24):
        groups[h] = [risk(x) for g in train.values() for t, _, x, _ in g if int(t[:2]) == h]
    V = [0.0] * (capacity + 1)
    thresholds = {}
    for h in reversed(range(24)):
        freq = Counter(groups[h])
        total = sum(freq.values())
        m = round(total / len(train))
        times = [V[:]]
        for _ in range(m):
            values = times[-1]
            times.append(
                [0.0]
                + [
                    sum(n * max(values[b], s + values[b - 1]) for s, n in freq.items()) / total
                    for b in range(1, capacity + 1)
                ]
            )
        V = times[-1]
        thresholds[h] = (m, times)
    allscores = [risk(x) for g in train.values() for _, __, x, _ in g]
    threshold = quantile(allscores, max(0, 1 - capacity / (len(allscores) / len(train))))
    totals = defaultdict(Counter)
    daily = []
    for _d, g in sorted(test.items()):
        if not g:
            continue
        edits = [(t, k, risk(x), y) for t, k, x, y in g]
        outcomes = {}
        for rule in [
            "Fixed threshold",
            "Time quota",
            "Inventory value",
            "Future scores",
            "Future outcomes",
        ]:
            if rule.startswith("Future"):
                which = 2 if rule == "Future scores" else 3
                take = sorted(edits, key=lambda r: (-r[which], r[0], r[1]))[:capacity]
            else:
                take = []
                seen = Counter()
                for t, k, sc, truth in edits:
                    h = int(t[:2])
                    rem = capacity - len(take)
                    if rem == 0:
                        break
                    if rule == "Fixed threshold":
                        accept = sc >= threshold
                    elif rule == "Time quota":
                        accept = len(take) < ceil((h + 1) * capacity / 24) and sc >= overall
                    else:
                        m, vs = thresholds[h]
                        r = max(0, m - 1 - seen[h])
                        value = vs[r]
                        accept = sc >= value[rem] - value[rem - 1] - 1e-13
                    seen[h] += 1
                    if accept:
                        take.append((t, k, sc, truth))
            hits = sum(x[3] for x in take)
            totals[rule].update(hits=hits, spent=len(take), score=sum(x[2] for x in take))
            outcomes[rule] = hits
        daily.append((len(edits), outcomes))
    hits = {k: c["hits"] for k, c in totals.items()}
    use = {k: 100 * c["spent"] / (len(test) * capacity) for k, c in totals.items()}
    high = quantile([x[0] for x in daily], 0.9)
    burst = {k: mean(h[k] for n, h in daily if n >= high) for k in totals}
    return result(
        f"Across {len(test)} held-out publication days, the inventory-value policy captured {hits['Inventory value']} seven-day identity reverts, versus {hits['Fixed threshold']} with a fixed threshold and {hits['Future outcomes']} for an outcome-aware upper bound.",
        {
            "Daily slots": capacity,
            "Held-out edits": sum(len(v) for v in test.values()),
            "Training edits": alln,
        },
        [
            figure(
                "Which online policies capture later identity reverts?",
                "Reverted edits selected",
                hits,
                "The two hindsight references see future scores or realized labels and are not deployable.",
            ),
            figure(
                "Use of the daily review inventory",
                "Percent of daily slots",
                use,
                "Unused slots expire at the end of each UTC day.",
            ),
            figure(
                "Highest-volume tenth of held-out days",
                "Mean captured events per day",
                burst,
                "Traffic bursts expose the cost of spending the last slot too early.",
            ),
        ],
        {
            "reservation_price_by_hour_and_slots": {
                h: [round(v[-1][b] - v[-1][b - 1], 6) for b in range(1, capacity + 1)]
                for h, (m, v) in thresholds.items()
            },
            "capacity": capacity,
            "days": len(test),
            "train_end_exclusive": mature,
            "policy_totals": {k: dict(v) for k, v in totals.items()},
            "training_prevalence": overall,
            "fixed_threshold": threshold,
            "bursty_day_size": high,
        },
        "Use logged arrivals to price the next slot. Compare operational rules with both ceilings; knowing the best future scores and knowing the future outcomes are different advantages.",
    )
