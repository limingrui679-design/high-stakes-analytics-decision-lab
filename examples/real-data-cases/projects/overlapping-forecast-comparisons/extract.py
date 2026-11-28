"""Align hourly load by UTC before computing lag-seven-days forecast errors."""

import csv
from collections import defaultdict
from datetime import datetime, timedelta


def rows(src):
    regions = ["CISO", "ERCO", "ISNE", "MISO", "NYIS", "PJM"]
    values = {a: {} for a in regions}
    for path in src.names("EIA930_BALANCE_*.csv"):
        with src.get(path).open(encoding="utf-8-sig", newline="") as stream:
            for r in csv.DictReader(stream):
                a = r["Balancing Authority"]
                if a not in values:
                    continue

                def number(k, r=r):
                    try:
                        return float(r[k].replace(",", ""))
                    except (ValueError, AttributeError):
                        return None

                obs = number("Demand (MW)")
                f = number("Demand Forecast (MW)")
                t = datetime.strptime(
                    r["UTC Time at End of Hour"], "%m/%d/%Y %I:%M:%S %p"
                ) - timedelta(hours=1)
                if obs and obs > 0:
                    item = (obs, f if f and f > 0 else None)
                    if t in values[a] and item != values[a][t]:
                        raise ValueError("Conflicting duplicate UTC hour")
                    values[a][t] = item
    for a, series in values.items():
        days = defaultdict(list)
        for t, (obs, f) in sorted(series.items()):
            past = series.get(t - timedelta(days=7))
            if f is not None and past is not None:
                days[t.date()].append((abs(f - obs), abs(past[0] - obs), obs, max(obs, f, past[0])))
        for day, triples in sorted(days.items()):
            if len(triples) == 24:
                x, y, z = (sum(part) for part in list(zip(*triples, strict=False))[:3])
                yield (
                    f"{a}/{day}",
                    a,
                    day,
                    round(x, 3),
                    round(y, 3),
                    round(z, 3),
                    24,
                    max(part[3] for part in triples),
                )
