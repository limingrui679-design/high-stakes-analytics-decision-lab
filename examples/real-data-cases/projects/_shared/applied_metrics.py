"""Small, auditable estimators shared by applied studies. Standard library only."""

import math
import random
from statistics import mean


def quantile(values, q):
    """Empirical inverse CDF: the smallest observed x with F(x) >= q."""
    v = sorted(values)
    return v[max(0, math.ceil(q * len(v)) - 1)]


def cluster_interval(differences, draws, seed):
    """Percentile CI for equally weighted independent unit means."""
    rng = random.Random(seed)
    sims = [mean(rng.choices(differences, k=len(differences))) for _ in range(draws)]
    return [quantile(sims, 0.025), quantile(sims, 0.975)]


def figure(title, unit, values, note):
    return dict(title=title, unit=unit, values=dict(values), note=note)


def result(conclusion, metrics, charts, audit, action):
    if len(charts) != 3:
        raise ValueError("Supply a comparison, slice and sensitivity or validation chart")
    return dict(
        conclusion=conclusion,
        headline_metrics=[f"{k}: {v}" for k, v in metrics.items()],
        figures=dict(zip(("comparison", "slice", "sensitivity"), charts, strict=True)),
        audit=audit,
        next_decision=action,
    )


def rank_groups(scores):
    """Midranks for tied scores; increasing score represents higher priority."""
    ordered = sorted(scores, key=scores.get)
    ranks = {}
    i = 0
    while i < len(ordered):
        end = i + 1
        while end < len(ordered) and scores[ordered[end]] == scores[ordered[i]]:
            end += 1
        ranks.update(dict.fromkeys(ordered[i:end], (i + end - 1) / 2))
        i = end
    return ranks


def inclusion(scores, capacity):
    """Expected inclusion under a uniform draw among ties at the capacity cutoff."""
    if not 0 < capacity <= len(scores):
        raise ValueError("Capacity must be positive and feasible")
    cut = sorted(scores.values(), reverse=True)[capacity - 1]
    above = sum(x > cut for x in scores.values())
    equal = sum(x == cut for x in scores.values())
    return {
        k: 1 if v > cut else ((capacity - above) / equal if v == cut else 0)
        for k, v in scores.items()
    }
