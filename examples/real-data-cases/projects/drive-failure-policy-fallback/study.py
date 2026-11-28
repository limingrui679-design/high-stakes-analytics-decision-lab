"""Prospective alert allocation with censoring, alert episodes and mature monitoring labels."""

from collections import Counter, defaultdict
from datetime import date
from heapq import nsmallest
from statistics import median

from applied_metrics import figure, result


def features(values):
    return (
        min(sum(x > 0 for x in values), 2),
        max(values),
        min(2, sum(x < 0 for x in values)),
        values[2] > 0,
    )


def intervals(rows):
    """Attach the next actual failure or end of observation across contiguous SMART spells."""
    drives = defaultdict(list)
    for r in rows:
        a, b = (date.fromisoformat(r[k]).toordinal() for k in ("from", "until"))
        vals = tuple(int(r[k]) for k in ("reallocated", "uncorrectable", "pending", "offline"))
        drives[r["drive"]].append((a, b, r["model"], features(vals), int(r["failure"])))
    for serial, spans in sorted(drives.items()):
        next_start = None
        for a, b, model, f, failed in sorted(spans, reverse=True):
            if b + 1 != next_start or failed:
                end = b
                failure = b if failed else 0
            # A drive already known to have failed at close is ineligible that evening.
            if a <= b - failed:
                yield serial, model, f, a, b - failed, end, failure
            next_start = a


def evaluate(rows, p, seed):
    split = date(2016, 8, 1).toordinal()
    horizon = p["horizon_days"]
    final = date(2016, 12, 31).toordinal() - horizon
    horizon_model = p["held_model"]
    training = defaultdict(Counter)
    starts = defaultdict(list)
    ends = defaultdict(list)
    serials = set()
    models = {}
    days = Counter()
    events = defaultdict(set)
    for serial, model, f, a, b, end, failure in intervals(rows):
        serials.add(serial)
        if model != horizon_model and int(serial, 16) % 10 < 7:
            stop = min(b, split - 1 - horizon)
            positive = (
                max(0, min(stop, failure - 1) - max(a, failure - horizon) + 1) if failure else 0
            )
            known_end = min(stop, end - horizon)
            # Positive windows ending early at a failure also have observable outcomes.
            known_positive = (
                max(0, min(known_end, failure - 1) - max(a, failure - horizon) + 1)
                if failure
                else 0
            )
            training[f][0] += max(0, known_end - a + 1) - known_positive
            training[f][1] += positive
            continue
        a, b = max(a, split), min(b, final)
        if a > b:
            continue
        models[serial] = model
        starts[a].append((serial, f, end, failure))
        ends[b + 1].append(serial)
        days[model] += b - a + 1
        if failure and max(a, failure - horizon) <= min(b, failure - 1):
            events[model].add((serial, failure))
    positive = sum(v[1] for v in training.values())
    prior = positive / sum(sum(v.values()) for v in training.values())
    prior_strength = 100

    def score(f):
        counts = training[f]
        return (counts[1] + prior_strength * prior) / (sum(counts.values()) + prior_strength)

    names = ["Pending-sector rule", "Frozen score", "Monitored fallback"]
    scores = {f: score(f) for changes in starts.values() for _, f, _, _ in changes}
    active = {}
    monitor = {}
    gates = []
    episodes = defaultdict(dict)
    current = defaultdict(dict)
    detected = defaultdict(dict)
    selected = defaultdict(Counter)
    missing = 0
    unknown_selected = Counter()
    n = p["daily_slots"]
    for t in range(split, final + 1):
        for serial in ends[t]:
            active.pop(serial)
        for serial, f, end, failure in starts[t]:
            active[serial] = (f, end, failure)
        matured = [
            hit
            for u in range(t - horizon - 7, t - horizon)
            for hit in monitor.get(u, [])
            if hit is not None
        ]
        unreliable = len(matured) >= 2 * n and sum(matured) / len(matured) < prior
        if unreliable:
            gates.append(date.fromordinal(t).isoformat())
        # Identical, deterministic tie order is independent of any outcome or follow-up.
        ranked = [
            (serial, f, ((int(serial, 16) * 11400714819323198485) ^ (t * 2654435761)) % 4294967291)
            for serial, (f, _, _) in active.items()
        ]
        for method in names:

            def priority(row, method=method, unreliable=unreliable):
                serial, f, tie = row
                simple = method == names[0] or (method == names[2] and (unreliable or f[2] >= 2))
                return (-(float(f[3]) if simple else scores[f]), tie, serial)

            choices = nsmallest(n, ranked, key=priority)
            for serial, f, _ in choices:
                _, end, failure = active[serial]
                model = models[serial]
                yes = bool(failure and t < failure <= t + horizon)
                label = 1 if yes else (0 if t + horizon <= end else None)
                if method == names[1]:
                    monitor.setdefault(t, []).append(label)
                if method == names[2] and f[2] >= 2:
                    missing += 1
                if label is None:
                    unknown_selected[method] += 1
                selected[method][model] += 1
                prev, start = current[method].get(serial, (-2, 0))
                if t - prev != 1:
                    start = t
                current[method][serial] = (t, start)
                evidence = episodes[method].setdefault((serial, start), [False, False])
                evidence[0] |= yes
                evidence[1] |= label is None
                if yes:
                    key = (serial, failure)
                    detected[method][key] = max(detected[method].get(key, 0), failure - t)

    def summarize(method, model=None):
        pool = events[model] if model is not None else set().union(*events.values())
        lead = [dt for event, dt in detected[method].items() if event in pool]
        ep = [v for (s, _), v in episodes[method].items() if model is None or models[s] == model]
        denom = days[model] if model is not None else sum(days.values())
        false = sum(not hit and not cens for hit, cens in ep)
        return {
            "observable_failures": len(pool),
            "alert_slots": selected[method][model]
            if model is not None
            else sum(selected[method].values()),
            "at_risk_device_days": denom,
            "episodes": len(ep),
            "confirmed_false_episodes": false,
            "unresolved_episodes": sum(not h and c for h, c in ep),
            "recall_pct": 100 * len(lead) / len(pool) if pool else None,
            "median_lead_days": median(lead) if lead else None,
            "false_per_1000_device_days": 1000 * false / denom,
        }

    totals = {m: summarize(m) for m in names}
    bymodel = {k: {m: summarize(m, k) for m in names} for k in sorted(days)}

    def metric(key):
        return {m: v[key] for m, v in totals.items()}

    rec = metric("recall_pct")
    return result(
        f"With {n} daily review slots across {final - split + 1} held-out dates, event recall was {rec[names[0]]:.1f}% for the pending-sector rule and {rec[names[2]]:.1f}% for monitored fallback across {totals[names[0]]['observable_failures']} observable failures.",
        {
            "Distinct drives": len(serials),
            "Held-out at-risk device-days": sum(days.values()),
            "Review slots per day": n,
        },
        [
            figure(
                "Failures warned before the event",
                "Percent of eligible failures",
                rec,
                "Each drive and failure date counts once even with repeat warnings.",
            ),
            figure(
                "Confirmed false alert episodes",
                "Per 1,000 held-out device-days",
                metric("false_per_1000_device_days"),
                "A consecutive episode with incomplete follow-up is reported as unresolved unless a failure is observed.",
            ),
            figure(
                "Lead time on detected failures",
                "Median days",
                metric("median_lead_days"),
                "Lead time uses the earliest eligible warning in the fourteen-day horizon.",
            ),
        ],
        {
            "totals": totals,
            "by_hardware_model": bymodel,
            "held_out_model": horizon_model,
            "matured_training_share": prior,
            "missing_feature_fallback_selections": missing,
            "gated_dates": gates,
            "unobservable_selected_windows": dict(unknown_selected),
            "monitor_window": "Seven days of frozen-model alerts whose entire fourteen-day outcome window expired before today.",
        },
        "Use the per-model alert counts, false investigations and warning time to set a review budget. Record whether missing measurements or delayed precision caused each fallback.",
    )
