"""Interval uncertainty after publishing a new overlapping score each day."""

import math
import random
from collections import defaultdict
from datetime import date
from statistics import mean

from applied_metrics import figure, quantile, result


def window(series, width):
    return {
        t: sum(series[t - j] for j in range(width)) / width
        for t in sorted(series)
        if all(t - j in series for j in range(width))
    }


def intervals(series, lag, block, draws, rng):
    dates = sorted(series)
    n = len(dates)
    centre = mean(series.values())
    std = sum((v - centre) ** 2 for v in series.values()) / (n - 1)
    naive = 1.96 * math.sqrt(std / n)
    nonoverlap = [series[t] for t in dates if (t - dates[0]) % 7 == 0]
    step_mu = mean(nonoverlap)
    step_se = math.sqrt(
        sum((x - step_mu) ** 2 for x in nonoverlap) / (len(nonoverlap) - 1) / len(nonoverlap)
    )
    gamma0 = sum((v - centre) ** 2 for v in series.values()) / n
    var = gamma0 + 2 * sum(
        (1 - k / (lag + 1))
        * sum((series[t] - centre) * (series[t - k] - centre) for t in dates if t - k in series)
        / n
        for k in range(1, lag + 1)
    )
    hac = 1.96 * math.sqrt(max(0, var) / n)
    blocks = [
        sum(series[t + i] for i in range(block))
        for t in dates
        if all(t + i in series for i in range(block))
    ]
    # Random contiguous date blocks. Use block sums and truncate to an integer
    # number of blocks; Gaussian limit methods use every available date.
    b = max(1, round(n / block))
    diffs = sorted(sum(rng.choices(blocks, k=b)) / (b * block) for _ in range(draws))
    # Centre at the bootstrap expectation to remove endpoint weighting bias.
    expected = mean(blocks) / block
    return dict(
        IID=[centre - naive, centre + naive],
        Nonoverlap=[step_mu - 1.96 * step_se, step_mu + 1.96 * step_se],
        HAC=[centre - hac, centre + hac],
        Block=[
            centre - (quantile(diffs, 0.975) - expected),
            centre - (quantile(diffs, 0.025) - expected),
        ],
    )


def evaluate(rows, p, seed):
    by = defaultdict(dict)
    raw = defaultdict(dict)
    flagged = []
    for r in rows:
        t = date.fromisoformat(r["day"]).toordinal()
        score = 100 * (float(r["forecast_error"]) - float(r["lag_error"])) / float(r["load"])
        raw[r["area"]][t] = score
        if float(r["max_hour_MW"]) > p["gross_error_screen_mw"]:
            flagged.append(
                {
                    "authority": r["area"],
                    "day": r["day"],
                    "max_input_MW": float(r["max_hour_MW"]),
                    "unfiltered_difference_pp": score,
                }
            )
        else:
            by[r["area"]][t] = score
    raw_week = [window(v, 7) for v in raw.values()]
    raw_common = set.intersection(*(set(v) for v in raw_week))
    unfiltered = mean(mean(v[t] for v in raw_week) for t in sorted(raw_common))
    regions = {k: window(v, 7) for k, v in sorted(by.items())}
    common = sorted(set.intersection(*(set(x) for x in regions.values())))
    paired = {t: mean(s[t] for s in regions.values()) for t in common}
    rng = random.Random(seed)
    ci = intervals(paired, p["hac_lag"], p["block_days"], p["bootstrap_draws"], rng)
    # Known mean zero under AR(1) innovations. Apply exactly the same 7-day
    # overlap and interval algorithms as the real study, with burn-in.
    sims = {}
    for rho in [0, 0.55]:
        hits = defaultdict(int)
        for _rep in range(p["simulation_reps"]):
            daily = {}
            x = 0
            for t in range(-60, 185):
                x = rho * x + rng.gauss(0, math.sqrt(1 - rho * rho))
                if t >= 0:
                    daily[t] = x
            for name, (lo, hi) in intervals(
                window(daily, 7), p["hac_lag"], p["block_days"], 169, rng
            ).items():
                hits[name] += lo <= 0 <= hi
        sims[str(rho)] = {name: 100 * h / p["simulation_reps"] for name, h in hits.items()}
    delta = mean(paired.values())
    means = {k: mean(v.values()) for k, v in regions.items()}
    width = {k: v[1] - v[0] for k, v in ci.items()}
    return result(
        f"Across {len(common):,} shared dates after the source-quality screen and {len(by)} balancing authorities, the day-ahead minus seasonal-naive score averaged {delta:.2f} percentage points. The 95% HAC interval spanned {width['HAC']:.3f} points versus {width['IID']:.3f} under independence.",
        {
            "Shared dates": len(common),
            "Actual BA-days": len(rows),
            "Width ratio": f"{width['HAC'] / width['IID']:.2f}×",
        },
        [
            figure(
                "Forecast advantage by balancing authority",
                "Difference in load-normalized absolute loss (pp)",
                means,
                "Negative values favor EIA's posted day-ahead forecasts over seven-day persistence.",
            ),
            figure(
                "Uncertainty in the shared-date average",
                "95% interval width (pp)",
                width,
                "Blocking the cross-area mean resamples entire dates jointly across areas.",
            ),
            figure(
                "Known-truth coverage after seven-day overlap",
                "Coverage (%) in AR(1) simulation",
                sims["0.55"],
                "Seeded experiments use a zero population mean; simulation coverage and historical intervals answer different questions.",
            ),
        ],
        {
            "raw_unscreened_pp": unfiltered,
            "raw_common_windows": len(raw_common),
            "excluded_source_days": flagged,
            "gross_error_screen_mw": p["gross_error_screen_mw"],
            "intervals": ci,
            "region_days": {k: len(v) for k, v in regions.items()},
            "weeks_share_days": 6,
            "coverage_pct": sims,
            "mc_standard_error_at_95_pct": 100 * math.sqrt(0.95 * 0.05 / p["simulation_reps"]),
            "block_sensitivity": {
                str(b): intervals(paired, p["hac_lag"], b, 349, rng)["Block"] for b in (7, 14, 28)
            },
        },
        "Publish uncertainty for paired calendar dates and sensitivity to block length. Treat published historical forecast errors as observations and the simulation as a coverage experiment.",
    )
