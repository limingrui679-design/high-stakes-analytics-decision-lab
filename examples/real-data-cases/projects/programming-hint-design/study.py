import math
from collections import Counter, defaultdict
from statistics import NormalDist, mean

from applied_metrics import figure, result


def logistic(samples):
    coef = [0.0] * 4
    for _ in range(130):
        g = [0.0] * 4
        for x, y in samples:
            p = 1 / (
                1 + math.exp(-max(-35, min(35, sum(a * b for a, b in zip(x, coef, strict=False)))))
            )
            for i, val in enumerate(x):
                g[i] += (p - y) * val
        for i in range(4):
            coef[i] -= 0.45 * (g[i] / len(samples) + (0.025 * coef[i] if i else 0))
    return coef


def metrics(pred):
    tp = sum(bool(p and y) for p, y in pred)
    fp = sum(bool(p and not y) for p, y in pred)
    fn = sum(bool(y and not p) for p, y in pred)
    return 2 * tp / max(1, 2 * tp + fp + fn)


def evaluate(rows, p, seed):
    challenge = sorted((r for r in rows if r["source"] == "CSEDM"), key=lambda r: int(r["order"]))
    ref = [r for r in rows if r["source"] == "Refactory"]
    students = {r["student"] for r in challenge}
    official = []
    new = []
    naive = []
    allp = []
    probs = []
    # At each time block, fit on other learners whose attempt and all their
    # released evaluation rows precede the block. No target learner enters fit.
    boundaries = [
        int(challenge[min(len(challenge) - 1, len(challenge) * i // 5)]["order"])
        for i in range(1, 5)
    ] + [10**12]
    latest = {s: max(int(r["order"]) for r in challenge if r["student"] == s) for s in students}
    for start, stop in zip(boundaries, boundaries[1:], strict=False):
        for fold in sorted({r["fold"] for r in challenge}):
            hist = [r for r in challenge if r["fold"] != fold and latest[r["student"]] < start]
            target = [r for r in challenge if r["fold"] == fold and start <= int(r["order"]) < stop]
            if len(hist) < 25 or not target:
                continue
            totals = defaultdict(Counter)
            for r in hist:
                totals[r["problem"]][int(r["first"])] += 1

            def vector(r, fit=False, totals=totals):
                c = totals[r["problem"]]
                y = int(r["first"])
                rate = (c[1] - (y if fit else 0) + 2) / (sum(c.values()) - int(fit) + 4)
                return [
                    1.0,
                    rate,
                    float(r["prior_rate"]),
                    math.log1p(float(r["prior_attempts"])) / 3,
                ]

            b = logistic([(vector(r, True), int(r["first"])) for r in hist])
            for r in target:
                x = vector(r)
                pr = 1 / (1 + math.exp(-sum(a * c for a, c in zip(x, b, strict=False))))
                y = int(r["first"])
                probs.append((pr, y))
                new.append((pr >= 0.5, y))
                naive.append((x[1] >= 0.5, y))
                official.append((int(r["official"]), y))
                allp.append(r)
    proxy = [
        (pred, int(r["first"]) == 1 and int(r["hint"]) == 0)
        for (pred, _), r in zip(new, allp, strict=False)
    ]
    scores = {
        "Problem prior": metrics(naive),
        "Author fold output": metrics(official),
        "Past-only logistic": metrics(new),
    }
    pattern = {
        k: sum(r["mutates"] == "1" and r["correct"] == v for r in ref)
        for k, v in [("Incorrect archive", "0"), ("Correct archive", "1")]
    }
    # Independent hand-trace of the inspected wrong_3_053.py mutation pattern.
    example = next(r for r in ref if r["file"] == "wrong_3_053.py")
    if (example["correct"], example["mutates"]) != ("0", "1"):
        raise ValueError("Diagnostic anchor changed")
    scenario = p["planned_effect"]
    a, b = 0.5, 0.5 + scenario
    z = NormalDist().inv_cdf(0.975)
    power = NormalDist().inv_cdf(0.8)
    avg = (a + b) / 2
    n = math.ceil(
        (
            (z * math.sqrt(2 * avg * (1 - avg)) + power * math.sqrt(a * (1 - a) + b * (1 - b)))
            / scenario
        )
        ** 2
    )
    help_groups = {
        k: 100 * mean(int(r["hint"]) for r in challenge if r["first"] == v)
        for k, v in [("Incorrect first", "0"), ("Correct first", "1")]
    }
    return result(
        f"The authors' public file contained {len(challenge)} learner–problem records. On {len(new)} matched out-of-time learner-held-out observations, first-correct F1 was {scores['Past-only logistic']:.3f} for the past-only model. In the independent code archive, {pattern['Incorrect archive']} incorrect programs removed from the list being traversed.",
        {
            "Observed learner–problem records": len(challenge),
            "Observed students": len(students),
            "Prospective learners per arm": n,
        },
        [
            figure(
                "Anticipating first-attempt correctness",
                "F1 score",
                scores,
                "Author predictions come from the published learner-fold analysis; the new fit imposes an additional historical cutoff.",
            ),
            figure(
                "Which observed attempts included any hint?",
                "Any-hint percent",
                help_groups,
                "The released aggregate gives a binary hint indicator, not hint timestamps or treatment assignment.",
            ),
            figure(
                "A real diagnostic pattern in a second corpus",
                "Programs containing the AST pattern",
                pattern,
                "Correct programs can share the pattern, so inspect a concrete trace before selecting feedback.",
            ),
        ],
        {
            "public_evaluation_rows": len(challenge),
            "learners": len(students),
            "public_evaluation_problems": len({r["problem"] for r in challenge}),
            "indicator_no_hint_and_first_correct_f1": metrics(proxy),
            "indicator_definition": "First correct and no hint recorded anywhere in this problem summary. Hint timing within the problem is unavailable.",
            "matched_count": len(new),
            "matched_students": len({r["student"] for r in allp}),
            "brier": mean((v - y) ** 2 for v, y in probs),
            "outcomes": scores,
            "code_archive_size": len(ref),
            "unparseable": sum(r["mutates"] == "" for r in ref),
            "teaching_example": "Refactory question 3, wrong_3_053.py: for [2,1,2], removing the first 2 leaves [1,2]; the intended order is [2,1].",
            "planned_experiment": {
                "arms": [
                    "Predict the counterexample then trace the deletion",
                    "View the corrected accumulation rule then trace identical input",
                ],
                "unit": "learner; equal practice time and same independent unseen transfer item; randomize within baseline-skill stratum",
                "primary": "Unaided first response on unseen order-preserving transfer task",
                "secondary": "Explanation score and delayed transfer; conceal scoring condition",
                "baseline_assumption": a,
                "absolute_effect_assumption": scenario,
                "alpha": 0.05,
                "power": 0.8,
                "independent_learners_per_arm": n,
                "missing_outcomes": "Intention-to-treat denominators, differential attrition and worst/best bounds",
                "status": "Prospective design; no participant trial",
            },
        },
        "Use the two interactive feedback variants for a future learner-randomized study. Historical hint use is observational and cannot measure which prototype improves independent transfer.",
    )
