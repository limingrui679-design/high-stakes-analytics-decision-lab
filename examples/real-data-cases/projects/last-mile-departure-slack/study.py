import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from applied_metrics import figure, result


def latest(tour, travel, service, left, right, shift):
    """Latest permissible depot departure for this exact tour, or None if infeasible."""
    depot = tour[0]
    nxt = depot
    time = shift
    for i in reversed(tour[1:]):
        time = min(right[i], time - travel[i][nxt] - service[i])
        if time < left[i]:
            return None
        nxt = i
    return time - travel[depot][nxt]


def bound(depot, tt, svc, hi, end):
    n = len(tt)
    travel_min = sum(min(tt[i][j] for i in range(n) if i != j) for j in range(n))
    # Each feasible Hamiltonian tour uses one incoming arc per stop, including depot.
    upper = end - sum(svc) - travel_min
    dist = [math.inf] * n
    dist[depot] = 0
    done = set()
    for _ in range(n):
        i = min((k for k in range(n) if k not in done), key=lambda k: dist[k])
        done.add(i)
        for j in range(n):
            dist[j] = min(dist[j], dist[i] + tt[i][j])
    return min(upper, min(hi[i] - dist[i] for i in range(n) if i != depot))


def repair(initial, tt, sv, lo, hi, shift, cap, focused, seed):
    rng = random.Random(seed)
    tour = initial[:]
    n = len(tour)

    def quality(r):
        v = latest(r, tt, sv, lo, hi, shift)
        if v is not None:
            return (1, v)
        time = late = 0
        for i, j in zip(r, r[1:], strict=False):
            time = max(lo[j], time + sv[i] + tt[i][j])
            late += max(0, time - hi[j])
        late += max(0, time + sv[r[-1]] + tt[r[-1]][r[0]] - shift)
        return (0, -late)

    best = quality(tour)
    tighter = sorted(tour[1:], key=lambda k: hi[k])[: min(12, n - 1)]
    for i in range(cap):
        candidate = tour[:]
        if focused:
            j = candidate.index(rng.choice(tighter)) if i % 3 else rng.randrange(1, n)
            target = rng.randrange(max(1, j - 17), min(n, j + 18))
            candidate.insert(target, candidate.pop(j))
        else:
            j, k = sorted(rng.sample(range(1, n), 2))
            candidate[j : k + 1] = reversed(candidate[j : k + 1])
        actual = quality(candidate)
        if actual > best:
            tour, best = candidate, actual
    return tour


def evaluate(rows, p, seed):
    solt = json.loads(Path(__file__).with_name("solver-witnesses.json").read_text())
    rs = defaultdict(list)
    for r in rows:
        rs[r["route"]].append(r)
    audits = {}
    modes = ["Driver sequence", "Standard 2-opt", "Window relocation"]
    witness = Counter()
    stress_count = Counter()
    for i, (k, g) in enumerate(sorted(rs.items())):
        g.sort(key=lambda r: r["stop"])
        n = len(g)
        actual = sorted(range(n), key=lambda i: int(g[i]["sequence"]))
        depot = actual[0]
        if g[depot]["depot"] != "1" or any(len(r["travel"].split(",")) != n for r in g):
            raise ValueError("Incomplete route matrix or invalid observed sequence")
        shift = p["shift_hours"] * 3600
        tt = [list(map(int, r["travel"].split(","))) for r in g]
        svc = [int(r["service"]) for r in g]
        low = [int(r["open"]) if r["open"] else -(10**6) for r in g]
        high = [int(r["close"]) if r["close"] else shift for r in g]
        tours = [actual] + [
            repair(actual, tt, svc, low, high, shift, p["move_budget"], b, seed + i)
            for b in [False, True]
        ]
        vals = [latest(t, tt, svc, low, high, shift) for t in tours]
        upper = bound(depot, tt, svc, high, shift)
        for v in vals:
            if v is not None and v > upper:
                raise ValueError("Feasible witness exceeds certified upper bound")
        zone = next((r["zone"] for r in g if r["zone"]), "")
        stressed = [
            [math.ceil(t * 1.25) if g[j]["zone"] == zone else t for j, t in enumerate(line)]
            for line in tt
        ]
        stress = [latest(t, stressed, svc, low, high, shift) for t in tours]
        for m, v, w in zip(modes, vals, stress, strict=False):
            witness[m] += v is not None and v >= 0
            stress_count[m] += w is not None and w >= 0
        ids = {r["stop"]: i for i, r in enumerate(g)}
        timed = {}
        for name, candidate in solt["routes"][k].items():
            path = candidate["order"]
            witness_seconds = None
            if path:
                if len(path) != n or set(path) != set(ids) or ids[path[0]] != depot:
                    raise ValueError("Incomplete solver witness")
                route = [ids[stop] for stop in path]
                witness_seconds = latest(route, tt, svc, low, high, shift)
                if witness_seconds is not None and witness_seconds > upper:
                    raise ValueError("Solver exceeded time bound")
            if witness_seconds != candidate["verified_seconds"]:
                raise ValueError("Solver witness failed replay")
            timed[name] = witness_seconds
        demonstrated = [v for v in [*vals, *timed.values()] if v is not None and v >= 0]
        witnesses = {}
        for name, order, v in zip(modes, tours, vals, strict=False):
            if v is None:
                continue
            clock = v
            slacks = []
            for a, b in zip(order, order[1:], strict=False):
                clock = max(low[b], clock + svc[a] + tt[a][b])
                if g[b]["close"]:
                    slacks.append((high[b] - clock, g[b]["stop"]))
            slacks.append((shift - (clock + svc[order[-1]] + tt[order[-1]][depot]), "depot return"))
            witnesses[name] = {
                "order": [g[j]["stop"] for j in order],
                "binding_stop_or_return": min(slacks)[1],
                "minimum_margin_seconds": min(slacks)[0],
            }
        audits[k] = {
            "timed_slack_seconds": timed,
            "verified_interval_seconds": [max(demonstrated) if demonstrated else None, upper],
            "witnesses": witnesses,
            "station": g[0]["station"],
            "stops": n,
            "windows": sum(int(r["window_packages"]) for r in g),
            "packages": sum(int(r["packages"]) for r in g),
            "slack_seconds": dict(zip(modes, vals, strict=False)),
            "upper_seconds": upper,
            "stress_slack_seconds": dict(zip(modes, stress, strict=False)),
            "status": "feasible witness"
            if demonstrated
            else ("certified infeasible" if upper < 0 else "search inconclusive"),
        }
    paired = [
        v
        for v in audits.values()
        if all(x is not None and x >= 0 for x in v["slack_seconds"].values())
    ]
    held = [v for v in audits.values() if v["station"] == p["holdout_station"]]
    unresolved = sum(v["status"] == "search inconclusive" for v in audits.values())
    timed_counts = {
        m: sum(
            v["timed_slack_seconds"][m] is not None and v["timed_slack_seconds"][m] >= 0
            for v in audits.values()
        )
        for m in ("OR-Tools VRPTW", "Timed relocation")
    }
    return result(
        f"On {len(audits)} complete published routes, window-focused relocation produced {witness['Window relocation']} nonnegative departure-delay witnesses; the recorded sequences produced {witness['Driver sequence']}. {unresolved} routes remained inconclusive under the search budget.",
        {
            "Complete routes": len(audits),
            "Held-out depot routes": len(held),
            "Evaluated moves per optimized tour": p["move_budget"],
        },
        [
            figure(
                "Routes with a feasible delay witness",
                "Routes",
                witness,
                "Every reported delay supports a verified order and a return within the stated shift.",
            ),
            figure(
                "Minutes of delay on jointly feasible routes",
                "Median feasible minutes",
                {
                    m: median(v["slack_seconds"][m] / 60 for v in paired) if paired else 0
                    for m in modes
                },
                "The paired denominator is recorded separately to expose feasibility selection.",
            ),
            figure(
                "One common zone travel-time disruption",
                "Routes still feasible",
                stress_count,
                "Each evaluated order sees the same 25% travel-time increase into one zone.",
            ),
        ],
        {
            "equal_wall_budget_counts": timed_counts,
            "seconds_per_method_route": solt["wall_budget_seconds_per_route_method"],
            "solver_version": solt["ortools_version"],
            "routes": audits,
            "jointly_feasible": len(paired),
            "independent_station": p["holdout_station"],
            "station_witness_counts": {
                m: sum(
                    v["slack_seconds"][m] is not None and v["slack_seconds"][m] >= 0 for v in held
                )
                for m in modes
            },
            "inconclusive": unresolved,
            "upper_bound": "Maximize departure time subject to a one-incoming-arc travel lower bound and shortest depot-to-deadline constraints",
        },
        "Offer delay only up to a recomputed feasible route witness. If the search and upper bounds disagree, retain the interval and use more solver time before making a dispatch promise.",
    )
