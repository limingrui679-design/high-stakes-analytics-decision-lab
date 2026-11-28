"""A common-random-numbers, nonpreemptive discrete-event queue replay."""

import bisect
import heapq
import math
import random
from collections import Counter, defaultdict
from datetime import date
from statistics import mean, median

from applied_metrics import figure, quantile, result

STEP = 1800
OPEN = 8 * 3600


def survival(calls):
    counts = Counter(c[2] for c in calls)
    events = Counter(c[2] for c in calls if not c[3])
    n = len(calls)
    s = 1.0
    ends = []
    cumulative = []
    for t in sorted(counts):
        s *= 1 - events[t] / n
        if events[t]:
            ends.append(t)
            cumulative.append(1 - s)
        n -= counts[t]
    return ends, cumulative


def complete(day, curves, services, seed, tail):
    """Observed abandonments fix patience. A service start right-censors patience."""
    rng = random.Random(seed)
    records = []
    for at, kind, wait, served, duration in sorted(day):
        ts, cs = curves[kind]
        if served:
            i = bisect.bisect_right(ts, wait)
            cdf = cs[i - 1] if i else 0.0
            u = cdf + (1 - cdf) * rng.random()
            j = bisect.bisect_left(cs, u)
            patience = ts[j] if j < len(ts) else max(wait + 1, ts[-1] + tail)
        else:
            patience = wait
            duration = rng.choice(services[kind])
        records.append((at, duration, patience))
    return records


def simulate(calls, base, forecast, flex, policy):
    """Flex is purchased in half-hours. Busy agents finish service after a boundary."""
    by_slot = [[] for _ in range(10)]
    for idx, (a, s, p) in enumerate(calls):
        by_slot[(a - OPEN) // STEP].append((a, idx, s, p))
    reserve = flex
    queue = []
    busy = []
    waits = []
    abandoned = 0
    changes = 0
    prev = False
    static = set(sorted(range(10), key=lambda i: (-forecast[i], i))[:flex])
    arrivals_so_far = 0
    backlogs = []
    for slot in range(10):
        left = OPEN + slot * STEP
        while busy and busy[0] <= left:
            heapq.heappop(busy)
        remaining = 10 - slot
        observed = arrivals_so_far / max(1, sum(forecast[:slot])) if slot else 1
        updated = [max(0.3, min(3, observed)) * v for v in forecast[slot:]]
        pending = sum(item[0] + item[3] >= left for item in queue)
        if policy == "fixed":
            take = slot in static
        elif policy == "queue":
            take = reserve and (pending >= 2 or remaining == reserve)
        else:
            pressure = [max(0, v - base[i + slot] * STEP / 165) for i, v in enumerate(updated)]
            pressure[0] += pending
            cutoff = sorted(pressure, reverse=True)[reserve - 1] if reserve else math.inf
            take = reserve and (pressure[0] >= cutoff or remaining == reserve)
        take = bool(take)
        reserve -= int(take)
        changes += int(prev != take)
        prev = take
        cap = base[slot] + int(take)
        incoming = by_slot[slot]
        ai = 0
        time = left
        while time < left + STEP:
            while busy and busy[0] <= time:
                heapq.heappop(busy)
            while ai < len(incoming) and incoming[ai][0] <= time:
                heapq.heappush(queue, incoming[ai])
                ai += 1
            while len(busy) < cap and queue:
                a, idx, d, p = heapq.heappop(queue)
                if time - a > p:
                    abandoned += 1
                    continue
                waits.append(time - a)
                heapq.heappush(busy, time + d)
            arrival = incoming[ai][0] if ai < len(incoming) else math.inf
            firstfree = busy[0] if busy else math.inf
            time = min(arrival, firstfree, left + STEP)
        backlogs.append(sum(a + pat >= left + STEP for a, _, _, pat in queue))
        arrivals_so_far += len(incoming)
    # Keep serving the evaluated arrival cohort with the last base capacity.
    time = OPEN + 10 * STEP
    while queue:
        while busy and busy[0] <= time:
            heapq.heappop(busy)
        while queue and len(busy) < base[-1]:
            a, idx, d, p = heapq.heappop(queue)
            if time - a > p:
                abandoned += 1
            else:
                waits.append(time - a)
                heapq.heappush(busy, time + d)
        if busy:
            time = busy[0]
    worst = max(backlogs)
    peak = backlogs.index(worst)
    recovery = next((j - peak for j in range(peak, len(backlogs)) if backlogs[j] == 0), None)
    return dict(
        long_wait=sum(w >= 120 for w in waits) / max(1, len(waits)),
        recovery_minutes=30 * recovery if recovery is not None else None,
        peak_backlog=worst,
        abandon=abandoned / len(calls),
        wait=mean(waits) if waits else 0,
        changes=changes,
        flex_used=flex - reserve,
    )


def evaluate(rows, par, seed):
    days = defaultdict(list)
    for r in rows:
        days[r["date"]].append(
            (int(r["arrival"]), r["kind"], int(r["wait"]), int(r["served"]), int(r["service"] or 0))
        )
    keys = sorted(days)
    train = [k for k in keys if k < "1999-08-01"]
    validation = [k for k in keys if "1999-08-01" <= k < "1999-10-01"]
    test = [k for k in keys if k >= "1999-10-01"]
    history = [r for k in train for r in days[k]]
    groups = defaultdict(list)
    for r in history:
        groups[r[1]].append(r)
    # Small or novel service types borrow the pooled training distribution.
    pools = {k: (g if sum(not x[3] for x in g) >= 10 else history) for k, g in groups.items()}
    pools["__other__"] = history
    curves = {k: survival(v) for k, v in pools.items()}
    services = {k: [x[4] for x in v if x[3]] for k, v in pools.items()}

    def materialize(k, tail=900):
        calls = [
            (a, kind if kind in pools else "__other__", w, s, h) for a, kind, w, s, h in days[k]
        ]
        return complete(calls, curves, services, seed + date.fromisoformat(k).toordinal(), tail)

    forecast = [sum((r[0] - OPEN) // STEP == i for r in history) / len(train) for i in range(10)]
    load = [
        sum(x[4] for x in history if (x[0] - OPEN) // STEP == i) / (len(train) * STEP)
        for i in range(10)
    ]

    def base(mult):
        return [max(1, round(x * mult)) for x in load]

    banks = {k: materialize(k) for k in validation + test}

    def empirical(k):
        g = days[k]
        return (mean(1 - x[3] for x in g), mean(x[2] for x in g if x[3]))

    def score(mult):
        vals = []
        for k in validation:
            sim = simulate(banks[k], base(mult), forecast, par["flex_slots"], "fixed")
            e, w = empirical(k)
            vals.append(abs(sim["abandon"] - e) + abs(sim["wait"] - w) / 300)
        return mean(vals)

    selected = min([0.85, 1.0, 1.15, 1.3, 1.5], key=score)
    policies = ["fixed", "queue", "horizon"]
    out = {
        p: {k: simulate(banks[k], base(selected), forecast, par["flex_slots"], p) for k in test}
        for p in policies
    }
    rates = {p: 100 * mean(v["abandon"] for v in d.values()) for p, d in out.items()}
    waits = {p: mean(v["wait"] for v in d.values()) for p, d in out.items()}
    observed = 100 * mean(empirical(k)[0] for k in test)
    peak = quantile([len(banks[k]) for k in test], 0.75)
    peaks = {
        p: 100 * mean(v["abandon"] for k, v in d.items() if len(banks[k]) >= peak)
        for p, d in out.items()
    }
    tails = {
        str(t): 100
        * mean(
            simulate(materialize(k, t), base(selected), forecast, par["flex_slots"], "horizon")[
                "abandon"
            ]
            for k in test
        )
        for t in [300, 1800]
    }
    stress = {}
    for factor in (1.0, 1.15, 1.30):
        samples = defaultdict(list)
        for k in test:
            stream = list(banks[k])
            peak_slot = max(
                range(10), key=lambda j: sum((a - OPEN) // STEP == j for a, _, _ in stream)
            )
            burst = [r for r in stream if (r[0] - OPEN) // STEP == peak_slot]
            rng = random.Random(seed + date.fromisoformat(k).toordinal())
            stream = sorted(stream + rng.choices(burst, k=round((factor - 1) * len(burst))))
            for pol in policies:
                samples[pol].append(
                    simulate(stream, base(selected), forecast, par["flex_slots"], pol)
                )
        stress[str(factor)] = {
            pol: {
                str(cost): mean(x["abandon"] * 100 + cost * x["changes"] for x in arr)
                for cost in (0, 0.25, 1)
            }
            for pol, arr in samples.items()
        }
    recovery = {
        pol: [vv["recovery_minutes"] for vv in obs.values() if vv["recovery_minutes"] is not None]
        for pol, obs in out.items()
    }
    return result(
        f"Across {len(test)} held-out mornings, mean simulated abandonment was {rates['fixed']:.2f}% with a fixed reserve and {rates['horizon']:.2f}% under receding-horizon dispatch. Observed abandonment averaged {observed:.2f}%.",
        {
            "Calls": len(rows),
            "Test days": len(test),
            "Flex hours per morning": par["flex_slots"] / 2,
        },
        [
            figure(
                "Abandonment at identical purchased staffing hours",
                "Percent",
                rates,
                "The three policies receive the same two-hour flexible reserve.",
            ),
            figure(
                "Waiting among answered calls",
                "Mean seconds over held-out days",
                waits,
                "The simulation runs common arrivals, latent patience draws and service durations.",
            ),
            figure(
                "High-arrival mornings",
                "Mean abandonment (%)",
                peaks,
                "Days above the holdout 75th percentile expose the cost of spending the reserve early.",
            ),
        ],
        {
            "stress_loss_abandonment_pp_plus_cost_per_switch": stress,
            "answered_wait_at_least_120s_pct": {
                m: 100 * mean(v["long_wait"] for v in ds.values()) for m, ds in out.items()
            },
            "peak_to_empty_minutes": {
                m: {"observable_days": len(v), "median_minutes": median(v) if v else None}
                for m, v in recovery.items()
            },
            "validation_days": len(validation),
            "training_days": len(train),
            "holdout_days": len(test),
            "calibrated_multiplier": selected,
            "observed_abandonment_pct": observed,
            "observed_mean_wait_s": mean(empirical(k)[1] for k in test),
            "tail_sensitivity": tails,
            "staff_by_half_hour": base(selected),
            "reserve_slots": par["flex_slots"],
            "switches": {p: mean(v["changes"] for v in d.values()) for p, d in out.items()},
            "flex_usage_range": {
                p: [
                    min(v["flex_used"] for v in d.values()),
                    max(v["flex_used"] for v in d.values()),
                ]
                for p, d in out.items()
            },
        },
        "Review out-of-time discrepancies in waiting and abandonment before staffing a live shift. The forecast and flexibility costs can be varied independently.",
    )
