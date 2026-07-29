#!/usr/bin/env python3
"""Build full evidence-matched terminal decision reports for non-ranking cases.

The multi-alternative decision engine remains the right renderer when a case
supports explicit alternatives, criteria, constraints, and uncertainty.
These builders cover equally legitimate terminal decisions that should not be
forced into that schema: do not deploy, require a randomized pilot, prioritize
diligence, and request missing evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from visual_system import (
    BLUE,
    CORAL,
    CORAL_TINT,
    GOLD,
    GOLD_TINT,
    GRID_DARK,
    INK,
    MUTED,
    PAPER,
    QUIET,
    rounded_rect,
    svg_document,
    text,
    theme_for,
    wrapped_text,
)


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECT_ROOT = SKILL_ROOT / "examples" / "real-data-cases" / "projects"
PROJECT_IDS = (
    "census-income-ai",
    "bank-marketing-response",
    "mckesson-financial-quality",
    "cfpb-fintech-complaint-operations",
    "federal-ai-governance",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pct(value: float, digits: int = 1) -> str:
    return f"{100 * value:.{digits}f}%"


def decimal(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def dollars_billions(value: float) -> str:
    return f"${value / 1_000_000_000:.1f}B"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def markdown_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def numbered_list(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, 1))


def summary_svg(spec: dict[str, Any], manifest: dict[str, Any]) -> str:
    accent, accent_dark, accent_tint = theme_for(spec["domain"])
    body: list[str] = []
    body.append(
        rounded_rect(
            42,
            140,
            1116,
            132,
            fill=accent_tint,
            stroke=accent,
            radius=16,
            stroke_width=1.5,
        )
    )
    body.append(text(68, 170, "TERMINAL DECISION", css="eyebrow", fill=accent_dark))
    body.append(
        wrapped_text(
            68,
            205,
            spec["decision"],
            chars=76,
            line_height=24,
            css="section",
            fill=INK,
        )
    )
    body.append(
        text(
            1132,
            169,
            spec["status_label"],
            css="eyebrow",
            anchor="end",
            fill=accent_dark,
        )
    )
    card_width = 352
    for index, metric in enumerate(spec["metrics"]):
        x = 42 + index * 382
        body.append(
            rounded_rect(
                x,
                300,
                card_width,
                118,
                fill=PAPER,
                stroke=GRID_DARK,
                radius=14,
            )
        )
        body.append(text(x + 22, 329, metric["label"].upper(), css="eyebrow"))
        body.append(text(x + 22, 371, metric["value"], css="big", fill=INK))
        body.append(
            wrapped_text(
                x + 22,
                397,
                metric["context"],
                chars=46,
                line_height=15,
                css="small",
                fill=MUTED,
            )
        )
    body.append(
        wrapped_text(
            48,
            458,
            "Claim boundary: " + spec["boundary"],
            chars=132,
            line_height=16,
            css="small",
            fill=QUIET,
        )
    )
    return svg_document(
        "Decision outcome and evidence",
        spec["visual_subtitle"],
        "\n".join(body),
        height=520,
        description=(
            "A decision banner states the evidence-matched terminal decision. "
            "Three metric cards summarize the reviewed evidence and a claim "
            "boundary limits interpretation."
        ),
        accent=accent,
        kicker="EVIDENCE-MATCHED DECISION",
        source=f"Source: {manifest['publisher']}; project outputs/results.json",
        note="Real-data project · terminal decision shown directly",
    )


def gate_svg(spec: dict[str, Any], manifest: dict[str, Any]) -> str:
    accent, accent_dark, accent_tint = theme_for(spec["domain"])
    body: list[str] = []
    y = 140
    status_style = {
        "PASS": (accent_tint, accent_dark),
        "BLOCK": (CORAL_TINT, CORAL),
        "REQUIRED": (GOLD_TINT, GOLD),
        "LIMIT": ("#EEF1F5", MUTED),
    }
    for index, gate in enumerate(spec["gates"], 1):
        fill, foreground = status_style[gate["status"]]
        body.append(
            rounded_rect(
                54,
                y,
                1092,
                78,
                fill=PAPER,
                stroke=GRID_DARK,
                radius=13,
            )
        )
        body.append(text(78, y + 28, f"{index:02d}", css="eyebrow", fill=accent_dark))
        body.append(text(128, y + 28, gate["label"], css="section", fill=INK))
        body.append(
            wrapped_text(
                128,
                y + 53,
                gate["detail"],
                chars=105,
                line_height=15,
                css="small",
                fill=MUTED,
            )
        )
        body.append(
            rounded_rect(
                1010,
                y + 18,
                108,
                30,
                fill=fill,
                stroke=foreground,
                radius=15,
            )
        )
        body.append(
            text(
                1064,
                y + 38,
                gate["status"],
                css="pill",
                anchor="middle",
                fill=foreground,
            )
        )
        if index < len(spec["gates"]):
            body.append(
                f'<line x1="98" y1="{y + 78}" x2="98" y2="{y + 96}" '
                f'stroke="{GRID_DARK}" stroke-width="2"/>'
            )
        y += 96
    height = y + 32
    return svg_document(
        "Decision evidence gates",
        spec["gate_subtitle"],
        "\n".join(body),
        height=height,
        description=(
            "Case-specific evidence gates are arranged in sequence. Each gate "
            "is explicitly labeled pass, limit, block, or required."
        ),
        accent=accent,
        kicker="DECISION PATH",
        source=f"Source: {manifest['publisher']}; project outputs/results.json",
        note="Gate status does not imply operational authorization",
    )


def census_spec(result: dict[str, Any]) -> dict[str, Any]:
    overall = result["overall"]
    naive = result["models"]["naive_bayes_baseline"]
    subgroup = result["subgroup_metrics"]
    return {
        "project_id": "census-income-ai",
        "title": "Consequential-Use Decision: Census-Income Benchmark",
        "domain": "Responsible AI",
        "route": ["descriptive", "predictive", "deployment decision"],
        "status": "not_authorized_for_consequential_use",
        "status_label": "BENCHMARK ONLY",
        "decision": (
            "Do not deploy this model for eligibility, credit, employment, or "
            "another consequential decision; retain it as a historical benchmark."
        ),
        "summary": (
            f"The sparse logistic benchmark separates the historical independent "
            f"test set well (AUC {decimal(overall['auc'])}) and has a Brier score "
            f"of {decimal(overall['brier'])}. Those metrics do not establish "
            "transport, acceptable group error, a valid local target, recourse, "
            "or benefit in a real workflow."
        ),
        "summary_interpretation": (
            "The decision separates model benchmarking from deployment authority. "
            "A strong historical test result is useful evidence about the code path, "
            "not evidence that a contemporary institution should act on the scores."
        ),
        "visual_subtitle": (
            "Adult/Census Income · independent historical test · 16,281 records"
        ),
        "metrics": [
            {
                "label": "Independent-test AUC",
                "value": decimal(overall["auc"]),
                "context": "Sparse logistic model; historical source test.",
            },
            {
                "label": "Brier score",
                "value": decimal(overall["brier"]),
                "context": "Probability error on the same independent test.",
            },
            {
                "label": "Male-group FPR",
                "value": pct(subgroup["sex"]["Male"]["false_positive_rate"]),
                "context": (
                    "Compared with "
                    f"{pct(subgroup['sex']['Female']['false_positive_rate'])} "
                    "for the female group."
                ),
            },
        ],
        "gates": [
            {
                "label": "Independent benchmark evaluation",
                "status": "PASS",
                "detail": "The held-out source test was not used for model selection.",
            },
            {
                "label": "Contemporary target and population match",
                "status": "BLOCK",
                "detail": "The 1994 Census-derived benchmark does not represent a current local decision population.",
            },
            {
                "label": "Acceptable error and subgroup burden",
                "status": "BLOCK",
                "detail": "Observed group error rates differ materially and no decision owner supplied an acceptable-error contract.",
            },
            {
                "label": "Workflow benefit, recourse, and harm controls",
                "status": "REQUIRED",
                "detail": "No prospective workflow evaluation, recourse design, or harm-benefit study is present.",
            },
            {
                "label": "Operational authorization",
                "status": "BLOCK",
                "detail": "No domain owner approved a target, threshold, use case, or deployment boundary.",
            },
        ],
        "gate_subtitle": (
            "Benchmark performance passes; contemporary-use and governance gates do not"
        ),
        "evidence_heading": (
            "The independent benchmark is strong enough for method comparison—not use"
        ),
        "evidence_intro": (
            "The sparse logistic model improves AUC and probability error relative "
            "to the mixed naive-Bayes baseline. The chart is a model-comparison "
            "result on the independent source test; it is not a benefit estimate."
        ),
        "primary_figure": "model-comparison.svg",
        "primary_alt": (
            "Independent-test comparison of majority, naive Bayes, and sparse logistic models"
        ),
        "primary_interpretation": (
            "The comparison supports retaining the model as a reproducible benchmark. "
            "It does not resolve target validity, contemporary transport, intervention "
            "effects, or the cost of errors."
        ),
        "evidence_headers": ["Model or baseline", "Metric", "Independent-test result"],
        "evidence_rows": [
            [
                "Majority baseline",
                "Accuracy",
                decimal(result["models"]["majority_baseline_accuracy"]),
            ],
            ["Mixed naive Bayes", "AUC", decimal(naive["auc"])],
            ["Mixed naive Bayes", "Brier score", decimal(naive["brier"])],
            ["Sparse logistic", "AUC", decimal(overall["auc"])],
            ["Sparse logistic", "Brier score", decimal(overall["brier"])],
        ],
        "secondary_heading": (
            "Calibration and subgroup errors prevent a single aggregate score from carrying the decision"
        ),
        "secondary_intro": (
            "Calibration is broadly informative at the benchmark level, while "
            "subgroup false-positive rates vary sharply. The group comparison is "
            "descriptive because the benchmark does not define a legitimate "
            "institutional action or acceptable-error policy."
        ),
        "secondary_figure": "subgroup-fpr.svg",
        "secondary_alt": "False-positive rates across sex and race groups",
        "secondary_interpretation": (
            "The figure shows why aggregate AUC cannot substitute for an impact "
            "assessment. Small groups also carry wider sampling uncertainty, and "
            "the historical labels embed a social and economic context that may not transport."
        ),
        "case_heading": "A real deployment would require a new validation contract",
        "case_intro": (
            "The next study must begin from a specific decision and population, "
            "not from the availability of this benchmark label."
        ),
        "case_headers": ["Required element", "Current status", "Evidence needed"],
        "case_rows": [
            ["Current local population", "Absent", "Representative, dated local sample"],
            ["Decision-valid target", "Absent", "Owner-approved outcome and exclusion rules"],
            ["Threshold and error costs", "Absent", "Pre-registered utility and harm contract"],
            ["Prospective performance", "Absent", "Locked future-period or external validation"],
            ["Recourse and monitoring", "Absent", "Human review, appeal, drift, and incident plan"],
        ],
        "allowed": [
            "Reproduce the historical benchmark and compare transparent methods.",
            "Study calibration, subgroup errors, drift checks, and abnormal-input behavior.",
            "Use the project as a template for a newly scoped validation study.",
        ],
        "prohibited": [
            "Use scores for eligibility, credit, employment, or resource access.",
            "Treat historical income labels as a causal or normative target.",
            "Represent AUC or accuracy as evidence of institutional benefit or fairness.",
        ],
        "boundary": result["decision_boundary"],
        "reversals": [
            "A newly scoped, contemporary and representative dataset supports the exact decision target.",
            "A locked prospective evaluation meets owner-approved performance and subgroup-error gates.",
            "A reviewed workflow supplies recourse, monitoring, human authority, and incident controls.",
        ],
        "next_steps": [
            "Define the proposed decision, affected population, target, exclusions, and non-model baseline.",
            "Pre-register discrimination, calibration, subgroup-error, and abstention gates before fitting.",
            "Validate on a dated external or prospective cohort and document recourse and monitoring.",
        ],
        "questions": [
            "What real decision—if any—would justify predicting this target?",
            "Which errors create the greatest burden, and who has authority to set the trade-off?",
            "What evidence would demonstrate benefit over a non-model workflow?",
        ],
        "case_specific": {
            "deployment_gates": {
                "benchmark_evaluation": "pass",
                "contemporary_population_match": "block",
                "acceptable_group_error": "block",
                "workflow_and_recourse": "required",
                "operational_authorization": "block",
            },
            "subgroup_false_positive_rates": {
                "Female": subgroup["sex"]["Female"]["false_positive_rate"],
                "Male": subgroup["sex"]["Male"]["false_positive_rate"],
            },
        },
        "methods": [
            "Select model and threshold without using the independent source test.",
            "Compare majority, mixed naive-Bayes, and sparse logistic benchmarks.",
            "Review discrimination, Brier score, calibration, subgroup errors, drift, and abnormal-input behavior separately.",
            "Apply contemporary-use, impact, recourse, and authorization gates after predictive validation.",
        ],
    }


def bank_spec(result: dict[str, Any]) -> dict[str, Any]:
    test = result["test"]
    options = result["capacity_decision"]["options"]
    selected = options["5%"]
    return {
        "project_id": "bank-marketing-response",
        "title": "Prospective-Test Decision: Marketing Capacity",
        "domain": "Business analytics and marketing",
        "route": ["descriptive", "predictive", "prospective-test decision"],
        "status": "randomized_pilot_required",
        "status_label": "PILOT REQUIRED",
        "decision": (
            "Advance the 5% review-capacity rule only to a randomized campaign "
            "pilot; do not treat observational response concentration as causal lift."
        ),
        "summary": (
            f"The untouched source-order test yields AUC {decimal(test['auc'])}. "
            f"The 5% tier captures {pct(selected['positive_capture'])} of observed "
            f"responders and has P(best) {pct(selected['probability_best'])} under "
            "shared block resampling. That comparison is exploratory because "
            "incremental response, cost, burden, profit, and lifetime value are unobserved."
        ),
        "summary_interpretation": (
            "The project supports choosing the next experiment, not choosing an "
            "operational campaign policy. The 5% tier is a resource-bounded pilot "
            "candidate whose ranking can reverse once causal lift and cost are measured."
        ),
        "visual_subtitle": "Bank Marketing · final source-order holdout · 8,238 contacts",
        "metrics": [
            {
                "label": "Untouched-test AUC",
                "value": decimal(test["auc"]),
                "context": "Weak-to-moderate ranking performance.",
            },
            {
                "label": "Top-5% response capture",
                "value": pct(selected["positive_capture"]),
                "context": "Share of observed responders in the selected tier.",
            },
            {
                "label": "Top-5% P(best)",
                "value": pct(selected["probability_best"]),
                "context": "Shared-block uncertainty across capacity options.",
            },
        ],
        "gates": [
            {
                "label": "Pre-contact feature timing",
                "status": "PASS",
                "detail": "Post-contact duration is excluded, preventing the most direct leakage path.",
            },
            {
                "label": "Untouched source-order evaluation",
                "status": "PASS",
                "detail": "Model selection and calibration precede the final 20% evaluation block.",
            },
            {
                "label": "Stable capacity ranking",
                "status": "LIMIT",
                "detail": "The leading 5% option has only 59% probability-best under shared calendar or campaign shocks.",
            },
            {
                "label": "Incremental response lift",
                "status": "BLOCK",
                "detail": "Observed response concentration does not identify a treatment effect.",
            },
            {
                "label": "Profit and customer-burden case",
                "status": "REQUIRED",
                "detail": "Contact cost, margin, lifetime value, opt-out burden, and brand effects are not observed.",
            },
        ],
        "gate_subtitle": (
            "The evidence selects a pilot candidate, not an operational targeting policy"
        ),
        "evidence_heading": (
            "The 5% tier is the leading pilot candidate, but the ranking is not decisive"
        ),
        "evidence_intro": (
            "All three capacity options are evaluated on the same final block and "
            "the same block-resampled replicates. This preserves shared campaign "
            "shocks instead of making the alternatives look artificially independent."
        ),
        "primary_figure": "capacity-capture.svg",
        "primary_alt": "Observed response capture across 5%, 10%, and 20% review capacities",
        "primary_interpretation": (
            "Higher capacity captures more observed responders, but also consumes "
            "more review effort. The exploratory utility ranking favors 5%; its "
            "59% probability-best is too weak for an irreversible operating decision."
        ),
        "evidence_headers": [
            "Review tier",
            "Observed capture",
            "Precision",
            "Lift vs random",
            "P(best)",
        ],
        "evidence_rows": [
            [
                tier,
                pct(option["positive_capture"]),
                pct(option["precision"]),
                decimal(option["lift_vs_random"], 2),
                pct(option["probability_best"]),
            ]
            for tier, option in options.items()
        ],
        "secondary_heading": (
            "Calibration instability reinforces the need for an experiment"
        ),
        "secondary_intro": (
            "The held-out score distribution has repeated score values and uneven "
            "calibration across bins. Capacity capture can still describe ranking, "
            "but the scores should not be read as reliable individual response probabilities."
        ),
        "secondary_figure": "calibration.svg",
        "secondary_alt": "Held-out predicted and observed response rates by score bin",
        "secondary_interpretation": (
            "The chart is a probability-quality diagnostic, not evidence of campaign "
            "impact. A randomized pilot must estimate incremental response and burden directly."
        ),
        "case_heading": "The next decision is an experiment with explicit business guardrails",
        "case_intro": (
            "The pilot design should be set before launch so that weak commercial "
            "outcomes cannot be reinterpreted after the fact."
        ),
        "case_headers": ["Design element", "Required specification", "Decision role"],
        "case_rows": [
            ["Assignment", "Randomized eligible contacts or approved clusters", "Identifies incremental effect"],
            ["Primary outcome", "Incremental term-deposit response", "Tests whether outreach changes behavior"],
            ["Economics", "Contact cost, margin, and capacity use", "Converts lift into net value"],
            ["Guardrails", "Opt-out, complaints, burden, and segment effects", "Constrains harmful scaling"],
            ["Analysis", "Pre-registered estimand, horizon, exclusions, and stop rule", "Prevents post-hoc selection"],
        ],
        "allowed": [
            "Use the 5% tier as the leading candidate in a randomized pilot.",
            "Use observed capture to plan review workload and power scenarios.",
            "Monitor calibration, capacity capture, and segment burden during the pilot.",
        ],
        "prohibited": [
            "Claim incremental lift, profit, or customer value from observational responses.",
            "Roll out the ranking as an operating policy before the randomized result.",
            "Treat P(best) as institutional approval or decision certainty.",
        ],
        "boundary": result["claim_boundary"],
        "reversals": result["capacity_decision"]["reversal_conditions"],
        "next_steps": [
            "Define eligibility, randomization unit, contact treatment, non-contact baseline, and follow-up horizon.",
            "Add cost, margin, opt-out, complaint, and segment-burden outcomes to the data contract.",
            "Pre-register scaling and stopping rules before exposing the first randomized unit.",
        ],
        "questions": [
            "What minimum incremental response would cover contact and review costs?",
            "Which customer-burden metric can veto a positive response result?",
            "Does the capacity ranking persist in a genuinely dated future campaign?",
        ],
        "case_specific": {
            "pilot_candidate": "review top 5%",
            "capacity_options": {
                tier: {
                    key: option[key]
                    for key in (
                        "capacity_share",
                        "selected_count",
                        "positive_capture",
                        "precision",
                        "lift_vs_random",
                        "probability_best",
                        "utility_interval_95",
                    )
                }
                for tier, option in options.items()
            },
            "required_experiment": {
                "estimand": "incremental response under randomized outreach",
                "economics": ["contact cost", "margin", "capacity use"],
                "guardrails": ["opt-out", "complaints", "customer burden", "segment effects"],
            },
        },
        "methods": [
            "Preserve pre-contact feature timing and a 60/20/20 source-order split.",
            "Select and calibrate the model before the untouched final evaluation block.",
            "Compare capacity capture, precision, workload, lift, and probability-best.",
            "Use shared block resampling so every capacity option experiences the same campaign and calendar shocks.",
        ],
    }


def finance_spec(result: dict[str, Any]) -> dict[str, Any]:
    latest = [
        row for row in result["annual_metrics"] if row["fiscal_year"] == 2025
    ]
    margins = [row["operating_margin"] for row in latest]
    cycles = [row["net_working_capital_cycle_days"] for row in latest]
    support = result["decision_support"]
    return {
        "project_id": "mckesson-financial-quality",
        "title": "Diligence Decision: SEC Peer Financial Quality",
        "domain": "Finance and accounting",
        "route": ["descriptive", "diagnostic", "diligence decision"],
        "status": "targeted_diligence_required",
        "status_label": "DILIGENCE NEXT",
        "decision": (
            "Prioritize cash-conversion persistence and working-capital-cycle "
            "reconciliation across filings; do not convert the peer panel into a security ranking."
        ),
        "summary": (
            "The panel covers three SEC SIC 5122 peers over eight fiscal years. "
            f"FY2025 operating margins span {pct(max(margins) - min(margins))} "
            f"and net working-capital cycles span {max(cycles) - min(cycles):.1f} "
            "days. Repeated differences are useful for prioritizing filing work, "
            "but taxonomy, segment mix, acquisitions, and fiscal timing remain unresolved."
        ),
        "summary_interpretation": (
            "The terminal decision is a diligence sequence. It directs attention "
            "to recurring cash-conversion differences while explicitly withholding "
            "valuation, assurance, credit, and investment conclusions."
        ),
        "visual_subtitle": "SEC Companyfacts peer panel · 3 entities × 8 fiscal years",
        "metrics": [
            {
                "label": "Peer panel",
                "value": "3 × 8",
                "context": "Three entities across eight fiscal years.",
            },
            {
                "label": "FY2025 margin range",
                "value": pct(max(margins) - min(margins)),
                "context": "Operating-margin spread across the three peers.",
            },
            {
                "label": "FY2025 cycle range",
                "value": f"{max(cycles) - min(cycles):.1f} days",
                "context": "Net working-capital-cycle spread.",
            },
        ],
        "gates": [
            {
                "label": "Fact-level lineage",
                "status": "PASS",
                "detail": "Company, CIK, XBRL tag, accession, filing date, and fiscal period are retained.",
            },
            {
                "label": "Repeated peer evidence",
                "status": "PASS",
                "detail": "The comparison uses 24 company-years rather than one company or one annual snapshot.",
            },
            {
                "label": "Economic comparability",
                "status": "LIMIT",
                "detail": "Shared SIC and common tags do not resolve segment, acquisition, policy, or calendar differences.",
            },
            {
                "label": "Footnote and filing reconciliation",
                "status": "REQUIRED",
                "detail": "The recurring cash-conversion gap must be traced through filings and footnotes.",
            },
            {
                "label": "Security or credit ranking",
                "status": "BLOCK",
                "detail": "The panel omits valuation, market expectations, covenants, segment detail, and assurance work.",
            },
        ],
        "gate_subtitle": (
            "The peer panel prioritizes filing work; it does not rank securities"
        ),
        "evidence_heading": (
            "Thin margins make recurring operating differences worth reconciling"
        ),
        "evidence_intro": (
            "All three distributors operate at large revenue scale with low "
            "operating margins. The multi-year view reduces reliance on a single "
            "fiscal year, but it cannot by itself explain the accounting or operating cause."
        ),
        "primary_figure": "margin-trends.svg",
        "primary_alt": "Operating-margin trends for three public drug distributors",
        "primary_interpretation": (
            "Small percentage-point differences can be economically material at "
            "this scale. The figure identifies persistence and exceptions for "
            "review; it does not establish superior quality or value."
        ),
        "evidence_headers": [
            "Entity",
            "FY2025 revenue",
            "Operating margin",
            "Operating cash-flow margin",
            "Net working-capital cycle",
        ],
        "evidence_rows": [
            [
                row["entity"],
                dollars_billions(row["revenue_usd"]),
                pct(row["operating_margin"]),
                pct(row["operating_cash_flow_margin"]),
                f"{row['net_working_capital_cycle_days']:.1f} days",
            ]
            for row in latest
        ],
        "secondary_heading": (
            "The working-capital pattern determines the next filing questions"
        ),
        "secondary_intro": (
            "Net working-capital cycles remain a compact diagnostic of inventory, "
            "receivables, and payables, but negative or improving values can arise "
            "from operating structure, timing, acquisitions, or classification choices."
        ),
        "secondary_figure": "working-capital-days.svg",
        "secondary_alt": "Net working-capital-cycle days across peers and fiscal years",
        "secondary_interpretation": (
            "The chart supports tracing persistent gaps into the cash-flow statement, "
            "balance-sheet notes, acquisition disclosures, and supplier-payment terms."
        ),
        "case_heading": "Diligence should proceed from facts to explanations",
        "case_intro": (
            "The sequence below preserves comparability checks before any broader conclusion."
        ),
        "case_headers": ["Priority", "Evidence to reconcile", "Possible reversal"],
        "case_rows": [
            ["1. Cash conversion", "Operating cash flow, working-capital bridge, non-cash items", "Timing explains the apparent gap"],
            ["2. Working-capital cycle", "Inventory, receivables, payables, supplier programs", "Definitions or supplier terms differ"],
            ["3. Segment and acquisitions", "Segment mix, acquired operations, integration effects", "Business mix explains persistence"],
            ["4. Taxonomy and periods", "Tags, accession, restatements, fiscal calendars", "Reclassification removes the difference"],
            ["5. Peer definition", "Broader and narrower peer sets", "Median and rank materially change"],
        ],
        "allowed": [
            "Prioritize specific filings, tags, footnotes, and periods for reconciliation.",
            "Use margin stress to understand why small changes matter in a low-margin industry.",
            "Expand the peer set and repeat the same lineage-preserving diagnostics.",
        ],
        "prohibited": [
            "Rank securities, issuers, or credit quality from the ratio panel.",
            "Treat common XBRL tags as proof of full economic comparability.",
            "Represent the analysis as valuation, assurance, or investment advice.",
        ],
        "boundary": result["claim_boundary"],
        "reversals": support["reversal_conditions"],
        "next_steps": [
            "Reconcile recurring cash-conversion gaps to cash-flow statements and working-capital footnotes.",
            "Document segment mix, material acquisitions, supplier programs, and fiscal-calendar differences.",
            "Repeat the peer medians and persistence checks under at least one broader peer definition.",
        ],
        "questions": [
            "Which recurring gap survives tag, period, and segment reconciliation?",
            "How much of the cash-conversion difference is structural versus timing-related?",
            "Does a broader peer set preserve the same diligence priority?",
        ],
        "case_specific": {
            "diligence_priority": support["recommended_next_diligence"],
            "latest_year_peer_metrics": latest,
            "comparability_boundary": result["comparability_boundary"],
            "fact_lineage": result["fact_reconciliation"],
        },
        "methods": [
            "Reconcile SEC Companyfacts to entity, CIK, tag, accession, filing date, and fiscal period.",
            "Construct a three-entity, eight-year panel with common-size and cash-conversion measures.",
            "Compare within-year peer medians, ranks, dispersion, and persistence.",
            "Use operating-margin stress only to size sensitivity, not to value or rank securities.",
        ],
    }


def cfpb_spec(result: dict[str, Any]) -> dict[str, Any]:
    test = result["test"]
    capacity = result["capacity_validation"]
    gate = result["deployment_gate"]
    auc_interval = result["auc_validation"]["block_bootstrap_95_interval"]
    return {
        "project_id": "cfpb-fintech-complaint-operations",
        "title": "Deployment Decision: Complaint Ranking Model",
        "domain": "Financial technology",
        "route": ["descriptive", "predictive", "deployment decision"],
        "status": "do_not_deploy",
        "status_label": "DO NOT DEPLOY",
        "decision": (
            "Do not deploy the individual complaint-ranking model; retain the "
            "privacy-minimized data contract, aggregate monitoring, and negative-validation evidence."
        ),
        "summary": (
            f"The later-period test AUC is {decimal(test['auc'])} with a block "
            f"interval of {decimal(auc_interval[0])}–{decimal(auc_interval[1])}. "
            f"At 5% review capacity the model captures {pct(capacity['5%']['positive_capture'])} "
            "of positives—effectively the random-review share—and no tested "
            "capacity passes the lift gate with uncertainty."
        ),
        "summary_interpretation": (
            "The negative result is the decision. Privacy minimization and honest "
            "time validation are valuable design properties, but neither can turn "
            "weak operational ranking gain into a deployable model."
        ),
        "visual_subtitle": "CFPB 2022 complaints · later-calendar-period test · 2,396 records",
        "metrics": [
            {
                "label": "Later-period AUC",
                "value": decimal(test["auc"]),
                "context": f"95% block interval {decimal(auc_interval[0])}–{decimal(auc_interval[1])}.",
            },
            {
                "label": "Top-5% lift",
                "value": decimal(capacity["5%"]["lift_vs_random"], 2),
                "context": "No gain over random review at the tested tier.",
            },
            {
                "label": "Outcome prevalence",
                "value": pct(test["prevalence"]),
                "context": "Untimely-response indicator in the later test period.",
            },
        ],
        "gates": [
            {
                "label": "Privacy-minimized public data contract",
                "status": "PASS",
                "detail": "Narratives, company names, ZIP codes, tags, and public-response text are excluded.",
            },
            {
                "label": "Later-calendar-period evaluation",
                "status": "PASS",
                "detail": "The final test period follows the training and validation periods.",
            },
            {
                "label": "AUC deployment threshold",
                "status": "BLOCK",
                "detail": f"Observed AUC {decimal(test['auc'])} is below the predeclared 0.650 gate.",
            },
            {
                "label": "Capacity lift with uncertainty",
                "status": "BLOCK",
                "detail": "No review tier has both required point lift and a block-bootstrap lower bound above random review.",
            },
            {
                "label": "Prospective workflow benefit",
                "status": "REQUIRED",
                "detail": "No prospective study demonstrates benefit, distributional burden, or safe escalation.",
            },
        ],
        "gate_subtitle": "Privacy and validation gates pass; ranking-value gates fail",
        "evidence_heading": "The cumulative-gain curve shows no reliable review advantage",
        "evidence_intro": (
            "At 5%, 10%, and 20% review capacities, observed capture remains close "
            "to random review and uncertainty intervals include no improvement. "
            "This is the operational comparison the deployment decision requires."
        ),
        "primary_figure": "cumulative-gain.svg",
        "primary_alt": "Held-out cumulative gain curve compared with random complaint review",
        "primary_interpretation": (
            "A statistically non-random AUC does not guarantee useful ranking at "
            "the actual operating capacity. Here, capacity performance does not "
            "create a reliable review advantage."
        ),
        "evidence_headers": [
            "Review tier",
            "Positive capture",
            "Lift vs random",
            "95% lift interval",
            "Gate",
        ],
        "evidence_rows": [
            [
                tier,
                pct(option["positive_capture"]),
                decimal(option["lift_vs_random"], 2),
                (
                    f"{decimal(option['lift_block_bootstrap_95_interval'][0], 2)}–"
                    f"{decimal(option['lift_block_bootstrap_95_interval'][1], 2)}"
                ),
                "Fail",
            ]
            for tier, option in capacity.items()
        ],
        "secondary_heading": (
            "The AUC exceeds the permutation center but still misses the deployment gate"
        ),
        "secondary_intro": (
            "The permutation benchmark shows that the model contains some statistical "
            "signal. The deployment question is stricter: whether that signal "
            "produces stable operational gain in the later period."
        ),
        "secondary_figure": "auc-null-benchmark.svg",
        "secondary_alt": "Observed AUC compared with the label-permutation null distribution",
        "secondary_interpretation": (
            "This distinction prevents a low p-value from being mistaken for "
            "decision value. The model fails both the predeclared AUC threshold and "
            "the capacity-lift requirement."
        ),
        "case_heading": "Re-entry requires prospective evidence, not threshold shopping",
        "case_intro": (
            "A future model should return to review only after a pre-registered "
            "later-period evaluation meets all gates."
        ),
        "case_headers": ["Re-entry gate", "Minimum evidence", "Why it matters"],
        "case_rows": [
            ["Discrimination", "Later-period AUC at or above 0.650", "Prevents deployment of weak rankers"],
            ["Capacity value", "Point lift at or above 1.20 and 95% lower bound above 1.00", "Requires gain beyond random review"],
            ["Privacy", "No expansion beyond approved operational fields without review", "Preserves minimization boundary"],
            ["Workflow", "Prospective benefit and burden evaluation", "Tests real operational consequences"],
            ["Monitoring", "Drift, capacity, subgroup, and incident triggers", "Constrains post-launch degradation"],
        ],
        "allowed": [
            "Retain aggregate complaint-volume and timeliness monitoring.",
            "Reuse the privacy-minimized extraction and calendar validation design.",
            "Document the negative result as evidence against deployment.",
        ],
        "prohibited": [
            "Rank individual complaints with the tested model.",
            "Interpret the timely indicator as merit, harm, resolution quality, or compliance.",
            "Use statistical significance to override failed operational gates.",
        ],
        "boundary": result["claim_boundary"],
        "reversals": gate["reversal_conditions"],
        "next_steps": [
            "Define a future-period protocol and freeze AUC, capacity-lift, privacy, and burden gates before fitting.",
            "Evaluate whether newly available operational features add stable signal without expanding sensitive data use.",
            "Run a prospective workflow study before any return to individual ranking.",
        ],
        "questions": [
            "Which operationally available feature could improve ranking without increasing privacy risk?",
            "Would aggregate staffing forecasts provide more value than individual ranking?",
            "Which groups or complaint types could bear disproportionate review delay?",
        ],
        "case_specific": {
            "deployment_gate": gate,
            "capacity_validation": capacity,
            "auc_validation": result["auc_validation"],
        },
        "methods": [
            "Minimize the stored administrative fields before analysis.",
            "Use ordered calendar train, validation, and later-period test windows.",
            "Validate calibration, AUC, cumulative gain, and capacity lift on the held-out period.",
            "Use day-block resampling and a 500-permutation null benchmark before applying deployment gates.",
        ],
    }


def governance_spec(result: dict[str, Any]) -> dict[str, Any]:
    readiness = result["disclosure_readiness"]
    counts = result["field_availability_status_counts"]
    family = result["family_reporting_completeness"]
    support = result["decision_support"]
    return {
        "project_id": "federal-ai-governance",
        "title": "Evidence Decision: Public AI Disclosure",
        "domain": "Technology policy and governance",
        "route": ["descriptive", "measurement-readiness", "evidence decision"],
        "status": "evidence_request_required",
        "status_label": "REQUEST EVIDENCE",
        "decision": (
            "Issue the structured evidence request before evaluating governance "
            "capability; do not score unobserved controls from missing-coded "
            "public-inventory fields."
        ),
        "summary": (
            f"The reviewed inventory contains {result['data']['use_cases']} use "
            f"cases and {result['public_fields_analyzed']} analyzed public fields. "
            f"Mean disclosure readiness is {pct(readiness['mean'])}; {counts['unavailable in snapshot (0%)']} "
            "fields are unavailable in the snapshot. These are observability "
            "findings, not measures of control presence or effectiveness."
        ),
        "summary_interpretation": (
            "The correct terminal decision is to request the missing evidence. "
            "The public inventory can measure disclosure readiness and define the "
            "next information request, but it cannot support a capability score."
        ),
        "visual_subtitle": (
            "Department of Transportation public AI inventory · 70 reported use cases"
        ),
        "metrics": [
            {
                "label": "Public use cases",
                "value": str(result["data"]["use_cases"]),
                "context": "One row per publicly reported AI use case.",
            },
            {
                "label": "Fields analyzed",
                "value": str(result["public_fields_analyzed"]),
                "context": "Complete reviewed public schema, not a selected seven-field subset.",
            },
            {
                "label": "Mean readiness",
                "value": pct(readiness["mean"]),
                "context": "External observability only; not governance maturity.",
            },
        ],
        "gates": [
            {
                "label": "Complete public-schema inventory",
                "status": "PASS",
                "detail": "All 34 public fields are classified and measured across 70 use cases.",
            },
            {
                "label": "Disclosure-readiness measurement",
                "status": "PASS",
                "detail": "Completeness can be reported with an external-observability definition.",
            },
            {
                "label": "Assurance and recourse evidence",
                "status": "BLOCK",
                "detail": "Testing, impact, monitoring, appeal, fallback, and remedy evidence is largely unobservable.",
            },
            {
                "label": "Governance-capability inference",
                "status": "BLOCK",
                "detail": "Blank or missing-coded public fields cannot establish that a control is absent, weak, unsafe, or noncompliant.",
            },
            {
                "label": "Structured evidence request",
                "status": "REQUIRED",
                "detail": "Capability review must begin with owner, lineage, test, monitoring, and recourse evidence.",
            },
        ],
        "gate_subtitle": (
            "Public observability can be measured; actual capability remains unobserved"
        ),
        "evidence_heading": (
            "Disclosure is strongest for identity and weakest for assurance and recourse"
        ),
        "evidence_intro": (
            "The six-family taxonomy uses all reviewed public fields. Identity, "
            "lifecycle, and purpose information are more visible than data, code, "
            "assurance, and recourse evidence."
        ),
        "primary_figure": "governance-reporting.svg",
        "primary_alt": "Public AI inventory reporting completeness by information family",
        "primary_interpretation": (
            "The family comparison locates disclosure gaps. It does not determine "
            "whether an internal control exists or whether that control is effective."
        ),
        "evidence_headers": ["Information family", "Reporting completeness", "Supported interpretation"],
        "evidence_rows": [
            [name.title(), pct(value), "Public observability"]
            for name, value in family.items()
        ],
        "secondary_heading": (
            "Assurance fields define the evidence request rather than a zero score"
        ),
        "secondary_intro": (
            "Public visibility is lowest for predeployment testing, impact assessment, "
            "independent review, monitoring, operator training, fail-safe behavior, "
            "appeal, and feedback. Their absence from the snapshot is a request trigger."
        ),
        "secondary_figure": "assurance-disclosure.svg",
        "secondary_alt": "Disclosure status of assurance and recourse fields",
        "secondary_interpretation": (
            "The chart should be read as an observability map. A capability conclusion "
            "requires reviewed internal artifacts and a separately scoped evaluation."
        ),
        "case_heading": "The evidence request is the decision-ready output",
        "case_intro": (
            "Each request below states why the evidence is needed and whether the "
            "public inventory currently offers partial support."
        ),
        "case_headers": ["Information request", "Why needed", "Inventory support"],
        "case_rows": [
            [
                item["information_request"],
                item["why_needed"],
                item["inventory_support"],
            ]
            for item in result["evidence_request_schema"]
        ],
        "allowed": [
            "Measure field availability and public reporting completeness.",
            "Compare disclosure families and development-stage reporting patterns.",
            "Use the missing-evidence schema to scope the next review.",
        ],
        "prohibited": [
            "Score actual governance capability from public-field completeness.",
            "Treat a blank or missing-coded field as proof that a control is absent or ineffective.",
            "Infer safety, ethics, legality, or compliance from observability alone.",
        ],
        "boundary": result["interpretation_boundary"],
        "reversals": support["reversal_conditions"],
        "next_steps": [
            "Send the structured request for ownership, data lineage, testing, impact, monitoring, and recourse artifacts.",
            "Confirm the publisher's reporting contract and distinguish optional, withheld, and unavailable fields.",
            "Create a separately scoped capability evaluation only after reviewed evidence is available.",
        ],
        "questions": [
            "Which fields are optional, withheld, unpublished, or genuinely not collected?",
            "What evidence demonstrates that stated controls operate in practice?",
            "Which high-impact use cases require a deeper, case-specific review first?",
        ],
        "case_specific": {
            "disclosure_readiness": readiness,
            "field_availability_status_counts": counts,
            "family_reporting_completeness": family,
            "evidence_request": result["evidence_request_schema"],
        },
        "methods": [
            "Classify all 34 reviewed public fields rather than selecting a favorable subset.",
            "Group fields into six information families and measure public reporting completeness.",
            "Separate field availability, reporting completeness, and measurement readiness from governance capability.",
            "Translate unobservable assurance and recourse evidence into a structured information request.",
        ],
    }


SPEC_BUILDERS = {
    "census-income-ai": census_spec,
    "bank-marketing-response": bank_spec,
    "mckesson-financial-quality": finance_spec,
    "cfpb-fintech-complaint-operations": cfpb_spec,
    "federal-ai-governance": governance_spec,
}


def render_report(
    spec: dict[str, Any],
    manifest: dict[str, Any],
    results_hash: str,
) -> str:
    source_link = manifest.get("landing_page") or manifest.get("download_url")
    return f"""# {spec['title']}

## Technical summary

**Decision: {spec['decision']}**

{spec['summary']}

![Decision outcome and evidence](figures/decision-summary.svg)

{spec['summary_interpretation']}

## {spec['evidence_heading']}

{spec['evidence_intro']}

![{spec['primary_alt']}](../../figures/{spec['primary_figure']})

{spec['primary_interpretation']}

{markdown_table(spec['evidence_headers'], spec['evidence_rows'])}

## {spec['secondary_heading']}

{spec['secondary_intro']}

![{spec['secondary_alt']}](../../figures/{spec['secondary_figure']})

{spec['secondary_interpretation']}

## The evidence gates determine the terminal decision

The gate sequence distinguishes useful analytical evidence from the additional
evidence required for the requested decision. A pass on one gate does not
override a block or missing requirement on another.

![Case-specific decision evidence gates](figures/decision-path.svg)

The terminal status is **{spec['status']}**. This status follows from the
case-specific evidence contract; it is not a generic caution added after the
analysis.

## {spec['case_heading']}

{spec['case_intro']}

{markdown_table(spec['case_headers'], spec['case_rows'])}

## What is permitted now—and what is not

### Supported uses

{markdown_list(spec['allowed'])}

### Unsupported uses

{markdown_list(spec['prohibited'])}

## Scope, source, and metric boundary

- **Source:** [{manifest['title']}]({source_link})
- **Publisher:** {manifest['publisher']}
- **Version:** {manifest['version']}
- **Accessed:** {manifest['accessed_at']}
- **Analytical grain:** {manifest['grain']}
- **Prepared rows:** {manifest['expected_rows']:,}
- **Adaptive route:** {' → '.join(spec['route'])}
- **Main analytical report:** [Open report](../../report.md)
- **Machine-readable analytical results:** [Open results](../../results.json)

## Decision method and validation logic

{markdown_list(spec['methods'])}

The terminal decision is produced after the analytical evidence is reviewed
against case-specific gates. A missing capability, treatment effect, approval,
or operating input is recorded as missing evidence rather than assigned a
favorable value.

## Limitations, uncertainty, and reversal conditions

**Claim boundary.** {spec['boundary']}

The decision should be reconsidered only if new evidence changes one of these
conditions:

{markdown_list(spec['reversals'])}

## Recommended next steps

{numbered_list(spec['next_steps'])}

## Further questions

{markdown_list(spec['questions'])}

## Reproducibility

- Decision result: [`decision-results.json`](decision-results.json)
- Decision chart map: [`figures/chart-map.json`](figures/chart-map.json)
- Source manifest: [`../../../source-manifest.json`](../../../source-manifest.json)
- Analytical result SHA-256: `{results_hash}`

The report is generated from the committed analytical result and source
manifest. It does not upgrade the permitted use of the underlying evidence.
"""


def build_project(project_root: Path) -> Path:
    results_path = project_root / "outputs" / "results.json"
    manifest_path = project_root / "source-manifest.json"
    result = load_json(results_path)
    manifest = load_json(manifest_path)
    project_id = result.get("project_id")
    if project_id != manifest.get("project_id") or project_id not in SPEC_BUILDERS:
        raise ValueError(f"Unsupported or mismatched project: {project_root}")
    spec = SPEC_BUILDERS[project_id](result)
    report_root = project_root / "outputs" / "decision" / "report"
    figure_root = report_root / "figures"
    figure_root.mkdir(parents=True, exist_ok=True)
    (figure_root / "decision-summary.svg").write_text(
        summary_svg(spec, manifest),
        encoding="utf-8",
    )
    (figure_root / "decision-path.svg").write_text(
        gate_svg(spec, manifest),
        encoding="utf-8",
    )
    results_hash = sha256(results_path)
    decision_result = {
        "schema_version": "1.0",
        "generated_at": "2026-07-28",
        "project_id": project_id,
        "decision_status": spec["status"],
        "decision": spec["decision"],
        "adaptive_route": spec["route"],
        "evidence_basis": spec["metrics"],
        "evidence_gates": spec["gates"],
        "methods": spec["methods"],
        "supported_uses": spec["allowed"],
        "unsupported_uses": spec["prohibited"],
        "claim_boundary": spec["boundary"],
        "reversal_conditions": spec["reversals"],
        "recommended_next_steps": spec["next_steps"],
        "case_specific": spec["case_specific"],
        "source": {
            "title": manifest["title"],
            "publisher": manifest["publisher"],
            "version": manifest["version"],
            "accessed_at": manifest["accessed_at"],
            "grain": manifest["grain"],
            "expected_rows": manifest["expected_rows"],
            "source_manifest_sha256": sha256(manifest_path),
            "analytical_results_sha256": results_hash,
        },
    }
    write_json(report_root / "decision-results.json", decision_result)
    chart_map = {
        "schema_version": "1.0",
        "project_id": project_id,
        "charts": [
            {
                "file": "decision-summary.svg",
                "report_section": "Technical summary",
                "question": "What is the evidence-matched terminal decision?",
                "family": "Tables & Scorecards",
                "type": "decision scorecard",
                "supported_claim": spec["decision"],
                "source": "outputs/results.json and source-manifest.json",
                "palette_policy": "single-root preferred",
                "accessibility": "Direct metric labels and textual decision outcome",
            },
            {
                "file": "decision-path.svg",
                "report_section": "The evidence gates determine the terminal decision",
                "question": "Which evidence gates pass, block, limit, or remain required?",
                "family": "Decomposition & Progression",
                "type": "labeled gate sequence",
                "supported_claim": f"Terminal status: {spec['status']}",
                "source": "outputs/results.json",
                "palette_policy": "hard two-root cap",
                "accessibility": "Every status is labeled in text and not encoded by color alone",
            },
            {
                "file": f"../../figures/{spec['primary_figure']}",
                "report_section": spec["evidence_heading"],
                "question": "What primary quantitative evidence supports the decision?",
                "family": "Project-native analytical visual",
                "type": "existing reviewed project figure",
                "supported_claim": spec["primary_interpretation"],
                "source": "outputs/results.json",
                "palette_policy": "project visual system",
                "accessibility": spec["primary_alt"],
            },
            {
                "file": f"../../figures/{spec['secondary_figure']}",
                "report_section": spec["secondary_heading"],
                "question": "Which validation or boundary evidence controls interpretation?",
                "family": "Project-native analytical visual",
                "type": "existing reviewed project figure",
                "supported_claim": spec["secondary_interpretation"],
                "source": "outputs/results.json",
                "palette_policy": "project visual system",
                "accessibility": spec["secondary_alt"],
            },
        ],
    }
    write_json(figure_root / "chart-map.json", chart_map)
    (report_root / "decision-report.md").write_text(
        render_report(spec, manifest, results_hash),
        encoding="utf-8",
    )
    return report_root / "decision-report.md"


def build_all(project_root: Path = DEFAULT_PROJECT_ROOT) -> list[Path]:
    reports = []
    for project_id in PROJECT_IDS:
        reports.append(build_project(project_root / project_id))
    return reports


def main() -> int:
    reports = build_all()
    print(f"Built {len(reports)} evidence-matched terminal decision reports.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
