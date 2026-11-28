import math
from collections import Counter, defaultdict
from datetime import date
from statistics import mean, median

from applied_metrics import figure, result


def evaluate(rows, p, seed):
    vintages = defaultdict(dict)
    for r in rows:
        t = date.fromisoformat(r["week"]).toordinal()
        vintages[t][r["state"]] = (
            math.log1p(int(r["advance"])),
            math.log1p(int(r["residence"])),
            date.fromisoformat(r["released"]).toordinal(),
            date.fromisoformat(r["next_release"]).toordinal(),
        )
    methods = ["Seasonal prior", "First release", "Shrunk revisions", "Revision probability"]
    ks = p["top_k"]
    acc = {k: {m: [] for m in methods} for k in ks}
    jurisdictions = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    reversals = defaultdict(int)
    flips = defaultdict(int)
    calibration = []
    observed = 0
    weeks = []
    for t, week in sorted(vintages.items()):
        if t < date.fromisoformat(p["holdout_start"]).toordinal():
            continue
        release, later = next(iter(week.values()))[2:]
        before = sorted(
            v for v in vintages if v < t and next(iter(vintages[v].values()))[3] <= release
        )
        if len(before) < 53:
            continue
        prior = before[-52:]
        pooled = median(b - a for v in prior for a, b, _, __ in vintages[v].values())
        scores = {m: {} for m in methods}
        target = {}
        historical_shocks = {v: {} for v in prior}
        for s, (a, b, _, _) in week.items():
            h = [vintages[v][s] for v in prior if s in vintages[v]]
            last = [rec[1] for rec in h[-8:]]
            seasonal = vintages.get(t - 364, {}).get(s)
            typical = 0.65 * median(last) + 0.35 * (seasonal[1] if seasonal else median(last))
            centre = median(x[1] for x in h)
            spread = max(0.12, 1.4826 * median(abs(x[1] - centre) for x in h))
            revisions = [x[1] - x[0] for x in h[-13:]]
            weight = len(revisions) / (len(revisions) + p["shrink_weeks"])
            adj = weight * mean(revisions) + (1 - weight) * pooled
            scores["Seasonal prior"][s] = (
                (seasonal[1] if seasonal else median(last)) - typical
            ) / spread
            scores["First release"][s] = (a - typical) / spread
            scores["Shrunk revisions"][s] = (a + adj - typical) / spread
            target[s] = (b - typical) / spread
            centre_revision = mean(vintages[v][s][1] - vintages[v][s][0] for v in prior)
            for v in prior:
                advance, residence, _, _ = vintages[v][s]
                historical_shocks[v][s] = (
                    scores["Shrunk revisions"][s] + (residence - advance - centre_revision) / spread
                )
        # Replay entire historical weeks to retain cross-jurisdiction dependence.
        scenarios = [
            sorted(shock, key=lambda s, shock=shock: (-shock[s], s))
            for shock in historical_shocks.values()
        ]
        for k in ks:
            winners = set(sorted(target, key=lambda s: (-target[s], s))[:k])
            counts = Counter(s for ranking in scenarios for s in ranking[:k])
            scores["Revision probability"] = {s: counts[s] / len(scenarios) for s in target}
            if k == p["review_slots"]:
                calibration.extend(
                    (prob - float(s in winners)) ** 2
                    for s, prob in scores["Revision probability"].items()
                )
            for m in methods:
                chosen = set(sorted(scores[m], key=lambda s: (-scores[m][s], s))[:k])
                acc[k][m].append(len(chosen & winners) / k)
                if k == p["review_slots"]:
                    for state in sorted(target):
                        cell = jurisdictions[state][m]
                        cell["raised"] += state in chosen
                        cell["confirmed"] += state in chosen and state in winners
                        cell["displaced"] += state in chosen and state not in winners
                        cell["missed"] += state not in chosen and state in winners
                        cell["days_until_publication_for_missed"] += (later - release) * int(
                            state not in chosen and state in winners
                        )
                    flips[m] += len(chosen - winners)
                    reversals[m] += len(winners - chosen) * (later - release)
        observed += len(week)
        weeks.append(t)
    k = p["review_slots"]
    hit = {m: 100 * mean(v) for m, v in acc[k].items()}
    return result(
        f"Across {len(weeks)} held-out weekly releases at {k} review slots, {hit['First release']:.1f}% of first-release alerts and {hit['Shrunk revisions']:.1f}% of revision-adjusted alerts appeared in the next release's residence-based list.",
        {"Holdout weeks": len(weeks), "State-weeks evaluated": observed, "Weekly slots": k},
        [
            figure(
                "First-release triage against the next publication",
                "Top-list precision (%)",
                hit,
                "All methods spend the same number of weekly review slots.",
            ),
            figure(
                "First-release alerts displaced in the next vintage",
                "Count of state-week alerts",
                flips,
                "An alert is displaced if its state falls outside the later top list.",
            ),
            figure(
                "Review capacity sensitivity",
                "Revision-adjusted top-list precision (%)",
                {f"{k} slots": 100 * mean(v["Shrunk revisions"]) for k, v in acc.items()},
                "Target ranking and capacity are recalculated at every budget.",
            ),
        ],
        {
            "state_membership_brier": mean(calibration),
            "jurisdiction_review": dict(jurisdictions),
            "hit_rate": hit,
            "flips": dict(flips),
            "missed_state_days_until_next_release": dict(reversals),
            "holdout_weeks": len(weeks),
            "state_weeks": observed,
            "pdf_pairs": len(vintages),
            "maturity_rule": "Only residence observations available by this release enter past history.",
        },
        "Keep first-publication alerts provisional. Actual review budgets and the observed cost of a one-release delay determine whether an adjusted list is useful.",
    )
