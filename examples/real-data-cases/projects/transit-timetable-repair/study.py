"""Prefix checkpoints for exact connection-scan repair after timetable edits."""

import bisect
import heapq
import pickle
import time
from collections import Counter, defaultdict

from applied_metrics import figure, result


def scan(edges, origin, start, buffer, step, old=None, change=None):
    states = {}
    reach = {origin: start - buffer}
    on = set()
    lo = (start // step) * step
    work = 0
    if old is not None:
        if change is None:
            return old, 0
        pivot = max(lo, change // step * step)
        if pivot in old[0]:
            reach, on = old[0][pivot]
            reach = reach.copy()
            on = on.copy()
            states = {k: v for k, v in old[0].items() if k < pivot}
            lo = pivot
    for bucket in range(lo, edges["end"] + step, step):
        states[bucket] = (reach.copy(), on.copy())
        for depart, trip, _seq, a, b, arrive, board, alight in edges.get(bucket, ()):
            if depart < start:
                continue
            work += 1
            if trip in on or (board and reach.get(a, 10**10) + buffer <= depart):
                on.add(trip)
                if alight and arrive < reach.get(b, 10**10):
                    reach[b] = arrive
    return (states, reach), work


def network_index(edges):
    by_stop = defaultdict(list)
    by_trip = defaultdict(list)
    for e in edges:
        by_stop[e[3]].append(e)
        by_trip[e[1]].append(e)
    for v in by_stop.values():
        v.sort()
    for v in by_trip.values():
        v.sort(key=lambda e: e[2])
    return (
        by_stop,
        by_trip,
        {a: [e[0] for e in v] for a, v in by_stop.items()},
        {(trip, e[2]): j for trip, g in by_trip.items() for j, e in enumerate(g)},
    )


def label_setting(index, origin, start, buffer):
    """Time-dependent shortest paths with one transfer buffer per boarding."""
    dep, trips, times, offset = index
    heap = [(start - buffer, origin)]
    labels = {origin: start - buffer}
    first = {}
    visits = 0
    while heap:
        t, a = heapq.heappop(heap)
        if labels[a] != t:
            continue
        if a not in dep:
            continue
        j = bisect.bisect_left(times[a], t + buffer)
        for e in dep[a][j:]:
            visits += 1
            if not e[6]:
                continue
            trip = e[1]
            idx = offset[trip, e[2]]
            cut = first.get(trip, len(trips[trip]))
            if idx >= cut:
                continue
            first[trip] = idx
            for edge in trips[trip][idx:cut]:
                visits += 1
                if edge[7] and edge[5] < labels.get(edge[4], 10**10):
                    labels[edge[4]] = edge[5]
                    heapq.heappush(heap, (edge[5], edge[4]))
    return labels, visits, first


def affected(previous, edits, start, buffer):
    labels, boarded = previous
    for edge in edits:
        departure, trip, _, a, _, _, boarding, _ = edge
        if departure >= start and (
            trip in boarded or (boarding and labels.get(a, 10**10) + buffer <= departure)
        ):
            return True
    return False


def evaluate(rows, p, seed, telemetry=None):
    versions = defaultdict(list)
    for r in rows:
        versions[r["feed"]].append(r)
    net = {}
    cache = {}
    baseline_cache = {}
    counts = Counter()
    summary = {}
    nquery = 0
    origins = [
        "place-pktrm",
        "place-dwnxg",
        "place-harsq",
        "place-north",
        "place-kencl",
        "place-welln",
    ]
    queries = [(o, s) for o in origins for s in p["departure_hours"]]
    step = p["checkpoint_minutes"] * 60
    for _number, (feed, changes) in enumerate(sorted(versions.items())):
        earliest = None
        diff = Counter()
        edited = []
        for r in changes:
            if r["op"] == "header":
                continue
            trip = r["trip"]
            seq = int(r["seq"])
            key = (trip, seq)
            e = (
                int(r["depart"]),
                trip,
                seq,
                r["a"],
                r["b"],
                int(r["arrive"]),
                int(r["board"]),
                int(r["alight"]),
            )
            old = net.get(key)
            if r["op"] == "drop":
                del net[key]
                diff["Removed"] += 1
            else:
                net[key] = e
                if old is None:
                    diff["Added"] += 1
                elif e[0] < old[0]:
                    diff["Earlier"] += 1
                elif e[0] > old[0]:
                    diff["Later"] += 1
                else:
                    diff["Changed stop or arrival"] += 1
            if old:
                edited.append(old)
            if r["op"] != "drop":
                edited.append(e)
            tt = min([x[0] for x in (old, e) if x])
            earliest = tt if earliest is None else min(earliest, tt)
        by = defaultdict(list)
        for edge in sorted(net.values()):
            by[edge[0] // step * step].append(edge)
        by["end"] = max(k for k in by)
        per = Counter()
        changed_arrivals = 0
        index = network_index(net.values())
        for origin, h in queries:
            if not any(origin in e[3:5] for e in net.values()):
                raise ValueError("Query station absent: " + origin)
            start = int(h * 3600)
            prior = cache.get((origin, h))
            stamp = time.perf_counter_ns() if telemetry is not None else 0
            fresh, cost = scan(by, origin, start, p["transfer_seconds"], step)
            if telemetry is not None:
                telemetry["full_query_ms"].append((time.perf_counter_ns() - stamp) / 1e6)
                stamp = time.perf_counter_ns()
            repair, visited = scan(by, origin, start, p["transfer_seconds"], step, prior, earliest)
            if telemetry is not None:
                telemetry["repair_query_ms"].append((time.perf_counter_ns() - stamp) / 1e6)
            old_base = baseline_cache.get((origin, h))
            if old_base is None or affected(old_base, edited, start, p["transfer_seconds"]):
                dist, relaxed, boarded = label_setting(index, origin, start, p["transfer_seconds"])
                baseline_cache[origin, h] = (dist, boarded)
            else:
                dist, relaxed = old_base[0], 0
            if dist != fresh[1]:
                raise ValueError(f"Independent label-setting mismatch {feed}/{origin}/{h}")
            if repair[1] != fresh[1]:
                raise ValueError(f"Routing mismatch {feed}/{origin}/{h}")
            if prior:
                changed_arrivals += sum(
                    prior[1].get(k) != fresh[1].get(k) for k in prior[1].keys() | fresh[1].keys()
                )
                per["Touched-trip shortest path"] += relaxed
                per["Full scan"] += cost
                per["Invalidate and scan"] += cost if earliest is not None else 0
                per["Prefix repair"] += visited
            cache[origin, h] = repair
            nquery += 1
        if telemetry is not None:
            telemetry["serialized_checkpoints_MiB"].append(
                len(pickle.dumps(cache, protocol=5)) / (1024**2)
            )
            telemetry["serialized_labels_MiB"].append(
                len(pickle.dumps(baseline_cache, protocol=5)) / (1024**2)
            )
        counts.update(diff)
        summary[feed] = dict(
            edges=len(net),
            work=dict(per),
            earliest_affected_second=earliest,
            changed_arrival_times=changed_arrivals,
            edits=dict(diff),
            after_midnight=sum(e[0] >= 86400 for e in net.values()),
        )
    totals = {
        m: sum(v["work"].get(m, 0) for v in summary.values())
        for m in ["Full scan", "Invalidate and scan", "Prefix repair", "Touched-trip shortest path"]
    }
    changes = sum(v["changed_arrival_times"] for v in summary.values())
    return result(
        f"Across {len(versions)} timetable versions, all {nquery} route-query results matched a full scan. Revisions changed {changes:,} destination arrival labels; checkpoint repair visited {totals['Prefix repair']:,} connections versus {totals['Full scan']:,} for full recomputation.",
        {
            "Version-query checks": nquery,
            "Mismatched queries": 0,
            "Held service date": "2024-11-22",
        },
        [
            figure(
                "Post-initialization work",
                "Scheduled connections visited",
                totals,
                "All algorithms answer the same station/time queries to every reachable destination.",
            ),
            figure(
                "Publisher timetable changes",
                "Connection operations",
                dict(counts),
                "A changed departure time is compared within the same published trip and stop sequence.",
            ),
            figure(
                "After-midnight scheduled connections",
                "Connections in selected timetable snapshots",
                {k: v["after_midnight"] for k, v in list(summary.items())[::2]},
                "GTFS times beyond 24:00 stay attached to the preceding service date.",
            ),
        ],
        {
            "versions": summary,
            "queries": queries,
            "verified_full_oracle": nquery,
            "work": totals,
            "airport_or_walking_edges": "No invented footpaths. Platforms are canonicalized to parent station.",
        },
        "Retain prefix checkpoints only while their input prefix is unchanged. Early-in-day edits can erase the savings; invariance against full routing remains the release criterion.",
    )
