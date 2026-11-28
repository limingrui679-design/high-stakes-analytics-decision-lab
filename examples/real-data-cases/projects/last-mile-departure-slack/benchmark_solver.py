"""Build the optional paired wall-budget routing benchmark (OR-Tools 9.15)."""

import argparse
import csv
import gzip
import importlib.metadata
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "_shared"))
from study import latest, repair  # noqa: E402


def standard(initial, matrix, service, low, high, shift, deadline):
    size = len(initial)
    manager = pywrapcp.RoutingIndexManager(size, 1, initial[0])
    routing = pywrapcp.RoutingModel(manager)
    times = [[matrix[i][j] + service[i] for j in range(size)] for i in range(size)]
    transit = routing.RegisterTransitMatrix(times)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)
    routing.AddDimension(transit, shift, shift, False, "time")
    dimension = routing.GetDimensionOrDie("time")
    for i in initial[1:]:
        left = max(0, low[i])
        right = min(shift, high[i])
        if left > right:
            return None
        dimension.CumulVar(manager.NodeToIndex(i)).SetRange(left, right)
    routing.AddVariableMaximizedByFinalizer(dimension.CumulVar(routing.Start(0)))
    dimension.SetSpanCostCoefficientForVehicle(1, 0)
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    )
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.FromMilliseconds(max(1, int((deadline - time.perf_counter()) * 1000)))
    assignment = routing.SolveWithParameters(params)
    if not assignment:
        return None
    path = []
    idx = routing.Start(0)
    while not routing.IsEnd(idx):
        path.append(manager.IndexToNode(idx))
        idx = assignment.Value(routing.NextVar(idx))
    return path


def main(seconds):
    rg = defaultdict(list)
    with gzip.open(ROOT / "data/raw/observations.csv.gz", "rt") as f:
        for r in csv.DictReader(f):
            rg[r["route"]].append(r)
    config = json.loads((ROOT / "config.json").read_text())
    records = {}
    for j, (key, g) in enumerate(sorted(rg.items())):
        g.sort(key=lambda row: row["stop"])
        seq = sorted(range(len(g)), key=lambda i: int(g[i]["sequence"]))
        tt = [list(map(int, r["travel"].split(","))) for r in g]
        svc = [int(r["service"]) for r in g]
        shift = config["parameters"]["shift_hours"] * 3600
        lo = [int(r["open"]) if r["open"] else -(10**6) for r in g]
        hi = [int(r["close"]) if r["close"] else shift for r in g]
        results = {}
        for name in ["OR-Tools VRPTW", "Timed relocation"]:
            begin = time.perf_counter()
            deadline = begin + seconds
            if name == "OR-Tools VRPTW":
                order = standard(seq, tt, svc, lo, hi, shift, deadline)
            else:
                order = seq[:]
                iteration = 0
                while time.perf_counter() < deadline:
                    order = repair(
                        order,
                        tt,
                        svc,
                        lo,
                        hi,
                        shift,
                        12,
                        True,
                        config["analysis_seed"] + j + iteration,
                    )
                    iteration += 1
            elapsed = time.perf_counter() - begin
            value = latest(order, tt, svc, lo, hi, shift) if order else None
            if order and sorted(order) != list(range(len(g))):
                raise ValueError("Incomplete route")
            results[name] = {
                "elapsed_s": round(elapsed, 5),
                "order": [g[i]["stop"] for i in order] if order else None,
                "verified_seconds": value,
            }
        records[key] = results
    output = {
        "ortools_version": importlib.metadata.version("ortools"),
        "wall_budget_seconds_per_route_method": seconds,
        "protocol": "Single vehicle, one thread. OR-Tools minimizes travel and time span then maximizes start for a feasible order. Relocation maximizes certified slack. Wall cutoffs can yield different witnesses on another machine. Baseline and focused search also have a separate deterministic equal-move comparison.",
        "routes": records,
    }
    (ROOT / "solver-witnesses.json").write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=0.5)
    args = parser.parse_args()
    if args.seconds <= 0:
        parser.error("Budget must be positive")
    main(args.seconds)
