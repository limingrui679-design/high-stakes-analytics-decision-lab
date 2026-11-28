from collections import defaultdict
from statistics import mean

from applied_metrics import figure, quantile, result


def evaluate(rows, p, seed):
    for r in rows:
        r["m"] = float(r["motion"])
        r["q"] = float(r["peak_share"])
        r["err"] = abs(float(r["wrist_bpm"]) - float(r["ecg_bpm"])) if r["ecg_bpm"] else None

    def split(r):
        return (
            "External WESAD"
            if r["cohort"] == "WESAD"
            else ("Development" if int(r["person"][1:]) % 3 != 0 else "Held-out DaLiA")
        )

    tr = [r for r in rows if split(r) == "Development"]
    parts = {k: [r for r in rows if split(r) == k] for k in ["Held-out DaLiA", "External WESAD"]}

    def scores(r, weight):
        return r["q"] - weight * r["m"]

    def subject_mae(accepted):
        g = defaultdict(list)
        for r in accepted:
            if r["err"] is not None:
                g[r["person"]].append(r["err"])
        return mean(mean(x) for x in g.values())

    def keep(data, fn, k):
        return sorted(data, key=lambda r: (-fn(r), r["key"]))[: round(k * len(data))]

    frac = p["report_fraction"]
    weight = min(
        [0, 0.125, 0.25, 0.5, 1], key=lambda w: subject_mae(keep(tr, lambda r: scores(r, w), frac))
    )

    def continuous(r):
        return scores(r, weight)

    edges = [quantile([continuous(r) for r in tr], q / 8) for q in range(1, 8)]

    def band(r):
        return sum(continuous(r) > cutpoint for cutpoint in edges)

    observed = [r for r in tr if r["err"] is not None]
    prior = mean(r["err"] > 10 for r in observed)
    calibration = {}
    for k in range(8):
        buck = [r for r in observed if band(r) == k]
        calibration[k] = (sum(r["err"] > 10 for r in buck) + 20 * prior) / (len(buck) + 20)

    # Empirical Bayes probabilities identify risk; the continuous score only breaks ties.
    def fn(r):
        return 1 - calibration[band(r)] + 1e-8 * max(-1, min(1, continuous(r)))

    cut = quantile([fn(r) for r in tr], 1 - frac)
    gate = {}
    for k, rs in parts.items():
        matched = keep(rs, fn, frac)
        motion = keep(rs, lambda r: -r["m"], frac)
        frozen = [r for r in rs if fn(r) >= cut]

        def by_activity(all_rows, retained):
            details = {}
            keys = {x["key"] for x in retained}
            for act in sorted({r["activity"] for r in all_rows}):
                all_act = [r for r in all_rows if r["activity"] == act]
                kept = [r for r in all_act if r["key"] in keys]
                readable = [r for r in kept if r["err"] is not None]
                details[act] = {
                    "eligible": len(all_act),
                    "reported": len(kept),
                    "reference_readable": len(readable),
                    "coverage_pct": 100 * len(kept) / len(all_act),
                    "mae": subject_mae(readable) if readable else None,
                    "error_over_10bpm_pct": 100 * mean(r["err"] > 10 for r in readable)
                    if readable
                    else None,
                }
            return details

        maximum = 0
        for subj in {r["person"] for r in rs}:
            current = 0
            prev = -1000
            for r in sorted((r for r in rs if r["person"] == subj), key=lambda r: int(r["sec"])):
                t = int(r["sec"])
                current = (current if t == prev + 8 else 0) + 8 if fn(r) < cut else 0
                maximum = max(maximum, current)
                prev = t
        gate[k] = {
            "windows": len(rs),
            "usable_ecg": sum(r["err"] is not None for r in rs),
            "all_mae": subject_mae(rs),
            "motion_mae": subject_mae(motion),
            "matched_quality_mae": subject_mae(matched),
            "frozen_mae": subject_mae(frozen),
            "frozen_coverage": len(frozen) / len(rs),
            "longest_gap_s": maximum,
            "coverage_and_error_by_activity": by_activity(rs, frozen),
            "matched_quality_by_activity": by_activity(rs, matched),
            "matched_motion_by_activity": by_activity(rs, motion),
            "subjects": {
                s: subject_mae([r for r in frozen if r["person"] == s])
                for s in sorted({r["person"] for r in frozen if r["err"] is not None})
            },
            "activities": {
                s: {"n": len(g), "mae": subject_mae(g)}
                for s in sorted({r["activity"] for r in frozen})
                if (g := [r for r in frozen if r["activity"] == s and r["err"] is not None])
            },
            "matched_coverage_curve": {
                str(c): subject_mae(keep(rs, fn, c)) for c in [0.5, 0.7, 0.9]
            },
        }
    ext = gate["External WESAD"]
    return result(
        f"With the DaLiA threshold frozen, WESAD retained {100 * ext['frozen_coverage']:.1f}% of {ext['windows']:,} eligible windows. Subject-averaged absolute error among reported ECG-readable windows was {ext['frozen_mae']:.2f} bpm.",
        {
            "Development participants": len({r["person"] for r in tr}),
            "External participants": len({r["person"] for r in parts["External WESAD"]}),
            "Longest external silence": f"{ext['longest_gap_s']} s",
        },
        [
            figure(
                "Error at matched reporting coverage",
                "Subject-averaged MAE (bpm)",
                {
                    f"{k.split()[1]} {method}": v[key]
                    for k, v in gate.items()
                    for method, key in [
                        ("motion", "motion_mae"),
                        ("quality", "matched_quality_mae"),
                    ]
                },
                "At matched coverage, quality and motion policies report the same number of windows in each cohort.",
            ),
            figure(
                "Which external activities retain a reading?",
                "Reported percent",
                {k: v["coverage_pct"] for k, v in ext["coverage_and_error_by_activity"].items()},
                "Frozen development threshold. The audit gives paired per-activity error, reference availability and large-error frequency.",
            ),
            figure(
                "Longest uninterrupted no-readout run",
                "Seconds",
                {k: v["longest_gap_s"] for k, v in gate.items()},
                "Clock gaps and changes in study activity eligibility break no-readout runs.",
            ),
        ],
        {
            "development_error_over_10bpm_probability_by_bin": calibration,
            "development_score_cutpoints": edges,
            "development_motion_weight": weight,
            "fixed_cutoff": cut,
            "groups": gate,
            "reference": "Same chest-ECG energy-envelope algorithm and quality gate in each cohort",
        },
        "Choose the reporting threshold using both per-person error and maximum no-readout time. Verify the policy in intended activities and hardware before relying on a new deployment.",
    )
