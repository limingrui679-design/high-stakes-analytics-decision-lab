"""Measure optional host-specific latency and storage using the verified case workloads."""

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

PROJECTS = Path(__file__).resolve().parents[1] / "projects"
sys.path.insert(0, str(PROJECTS / "_shared"))
OPTIONS = ["transit-timetable-repair", "versioned-road-geometry"]


def benchmark(slug, repeats):
    here = PROJECTS / slug
    spec = importlib.util.spec_from_file_location(slug, here / "study.py")
    study = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(study)
    file = here / "data/processed/analysis.csv"
    config = json.loads((here / "config.json").read_text())
    with file.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    pooled = defaultdict(list)
    for iteration in range(repeats + 1):
        observations = defaultdict(list)
        study.evaluate(rows, config["parameters"], config["analysis_seed"], observations)
        if iteration:
            for field, values in observations.items():
                pooled[field].extend(values)
    stats = {}
    for k, v in pooled.items():
        ranked = sorted(v)
        stats[k] = {
            "samples": len(v),
            "median": round(median(v), 5),
            "p95": round(ranked[math.ceil(0.95 * len(v)) - 1], 5),
            "maximum": round(ranked[-1], 5),
        }
    info = {
        "environment": {
            "system": platform.system(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
        },
        "input_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
        "unmeasured_warmups": 1,
        "measured_full_replays": repeats,
        "protocol": "Single process, perf_counter_ns, warm filesystem, no network. p95 is the empirical nearest-rank statistic. Timetable cache sizes use protocol-5 serialized bytes. Full road storage retains only the current snapshot, while incremental storage also retains history and reverse dependencies. Durations vary by host.",
        "measurements": stats,
    }
    path = here / "outputs/benchmark-host.json"
    path.write_text(json.dumps(info, indent=2) + "\n")
    print(slug, len(stats), "measurements", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=OPTIONS, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    a = parser.parse_args()
    if a.repeats < 1:
        parser.error("A benchmark needs at least one measured repeat")
    benchmark(a.case, a.repeats)
