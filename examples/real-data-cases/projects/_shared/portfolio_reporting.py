#!/usr/bin/env python3
"""Project registry and reporting for High-Stakes Analytics & Decision Lab."""

from __future__ import annotations

from portfolio_core import *
from portfolio_clinical import *
from portfolio_modeling import *
from portfolio_treasury import *
from portfolio_spatial import *
from portfolio_asset_realestate import *

ANALYZERS: dict[str, Callable[[Path], dict[str, Any]]] = {
    "population-health-survival": analyze_population,
    "behavioral-reading-experiment": analyze_behavioral,
    "census-income-ai": analyze_adult,
    "bike-demand-operations": analyze_bike,
    "treasury-risk-engineering": analyze_treasury,
    "commercial-real-estate-risk": analyze_real_estate,
    "spatial-equity-planning": analyze_spatial,
    "bank-marketing-response": analyze_bank_marketing,
    "sec-nport-filing-review": analyze_multi_asset,
    "cfpb-fintech-complaint-operations": analyze_cfpb,
}

PREPARERS["sec-nport-filing-review"] = prepare_multi_asset
PREPARERS["commercial-real-estate-risk"] = prepare_real_estate


REPORT_COPY = {
    "population-health-survival": {
        "answer": "Low ejection fraction is associated with a higher observed death-event rate, but the dataset supports triage-rule validation—not a treatment recommendation.",
        "findings": [
            "The Kaplan–Meier view retains censoring and the changing risk set rather than treating all follow-up windows as complete.",
            "The adjusted Cox model reports associational hazard ratios, apparent discrimination, and 180-day calibration without upgrading prediction to causality.",
            "The absolute event-rate contrast is paired with a patient-bootstrap interval rather than a p-value alone.",
            "Patient bootstrap intervals show how much the candidate triage comparison moves under resampling.",
        ],
        "methods": "Kaplan–Meier survival estimation, multivariable Breslow-tie Cox regression, Schoenfeld-time diagnostics, apparent 180-day calibration, subgroup risk differences, patient bootstrap, and protocol capture/workload analysis.",
        "limits": "Small observational cohort; selection and treatment information are incomplete; thresholds were not prospectively registered.",
    },
    "behavioral-reading-experiment": {
        "answer": "Pseudoword passages increase fixation-duration burden, and the paired effect differs by reader group; a combined protocol gains contrast at the cost of time.",
        "findings": [
            "The primary contrast is within participant, preserving the repeated-measures design.",
            "Primary and secondary paired outcomes use sign-flip inference with Holm adjustment rather than uncorrected multiple testing.",
            "A randomization-style permutation test evaluates the between-group difference without relying on a normal approximation.",
        ],
        "methods": "Paired differences, participant bootstrap intervals, sign-flip inference, Holm multiplicity control, order sensitivity, MDE design sensitivity, standardized group separation, and label permutation.",
        "limits": "The public file contains 57 participants and does not establish downstream educational or policy outcomes.",
    },
    "census-income-ai": {
        "answer": "The benchmark classifier improves on the majority baseline, but subgroup error rates and imperfect calibration make consequential reuse indefensible.",
        "findings": [
            "A majority rule and mixed naive Bayes baseline are compared with a sparse logistic model selected inside the training file.",
            "Sex- and race-stratified diagnostics expose performance heterogeneity instead of reporting only aggregate accuracy.",
            "The independent source test, calibration, drift checks, and abnormal-input challenge remain separate from hyperparameter selection.",
        ],
        "methods": "Majority and mixed-naive-Bayes baselines, sparse one-hot logistic regression, internal hyperparameter selection, independent source test, validation-only cost threshold, calibration, drift, subgroup, and abnormal-input diagnostics.",
        "limits": "1994 Census-derived data, missing categories, historical social structure, and no validation for any real eligibility decision.",
    },
    "bike-demand-operations": {
        "answer": "A robust time-block allocation reduces modeled unmet demand out of time, while the forecast benchmark quantifies how much predictable structure exists.",
        "findings": [
            "The forecast trains on 2011 and evaluates on 2012, avoiding a random time leak.",
            "The optimizer respects a fixed resource total and minimum coverage in every six-hour block.",
            "Exhaustive feasibility, Pareto, resource shadow-value, and perfect-information upper-bound analyses expose when the preferred allocation could reverse.",
        ],
        "methods": "Segmented demand benchmark, out-of-time MAE, exhaustive integer allocation, binding-constraint checks, Pareto frontier, resource shadow values, perfect-information upper bound, weather stress, and shared day bootstrap.",
        "limits": "System totals do not include station imbalances, travel times, labor rules, or causal service effects.",
    },
    "bank-marketing-response": {
        "answer": "Pre-contact features concentrate observed term-deposit responses on the untouched final split, but only a randomized campaign can establish incremental lift or ROI.",
        "findings": [
            "Model selection uses the middle source-order split, while the final 20% remains untouched until evaluation.",
            "Capacity options share every adjacent-row block-bootstrap replicate, so common campaign shocks flow through probability-best rather than being sampled independently.",
            "Call duration is excluded because it is unavailable before the contact decision.",
        ],
        "methods": "Source-order train/validation/test design, leakage-controlled mixed naive Bayes, AUC/Brier/calibration, capacity lift, subgroup checks, shared block bootstrap, and decision sensitivity.",
        "limits": "The source supplies order but not full dates, comes from one bank and campaign system, and is observational; response is not causal lift, value, or profit.",
    },
    "sec-nport-filing-review": {
        "answer": "The walk-forward allocation is evaluated against equal-weight and 60/40 benchmarks under shared market histories, costs, drawdowns, and correlated stress; it is research evidence, not an investment mandate.",
        "findings": [
            "Every strategy is evaluated on the same post-lookback trading days and the adaptive allocation uses only trailing information at each monthly rebalance.",
            "Shared month-block resampling keeps common market shocks aligned when estimating probability-best.",
            "Historical pandemic and 2022 rate-regime performance are reported separately from full-period averages.",
            "Transaction-cost, turnover, drawdown, and tail-loss evidence prevent a return-only ranking.",
        ],
        "methods": "Adjusted-price alignment, daily returns, monthly walk-forward inverse-volatility allocation, bounded weights, declared turnover cost, equal-weight and 60/40 benchmarks, drawdown, historical VaR/ES, regime stress, and shared moving-block bootstrap.",
        "limits": "The provider snapshot and ETF proxies omit taxes, bid–ask spreads, market impact, tracking error, investor liabilities, capacity, and future regimes. Historical adjusted prices do not establish future performance or suitability.",
    },
    "cfpb-fintech-complaint-operations": {
        "answer": "The later-period ranking model fails the deployment gate: AUC is weak and top-capacity lift is not reliably above random review. The defensible contribution is the privacy-preserving data contract, calendar validation, and explicit negative result.",
        "findings": [
            "The observed AUC is compared with both a day-block bootstrap interval and a 500-permutation null distribution.",
            "Calibration is evaluated on November–December only, after model and calibrator selection.",
            "Every tested capacity is benchmarked against random review; no artificial utility score is used to force a preferred capacity.",
            "The cumulative-gain curve makes the operational failure visible: useful ranking should separate clearly from the random diagonal.",
        ],
        "methods": "Privacy-minimized administrative data, calendar train/validation/test split, rare-outcome AUC/Brier/calibration, cumulative gain, capacity lift versus random review, day-block bootstrap, label-permutation null benchmark, subgroup diagnostics, and explicit non-deployment gates.",
        "limits": "Published complaints are selective; the timely flag does not measure complaint merit, harm, resolution quality, company quality, or compliance. The 2022 model is weak and may not transport.",
    },
    "treasury-risk-engineering": {
        "answer": "Longer-duration allocations offer different carry/risk trade-offs and materially larger historical tail losses; the short portfolio remains the risk reference.",
        "findings": [
            "VaR and expected shortfall are calculated from daily historical returns and accompanied by exceedance counts.",
            "Block bootstrap samples preserve short-run dependence better than independent daily resampling.",
            "Rolling VaR coverage and breach-independence tests are reported separately across common historical regimes.",
        ],
        "methods": "Yield-curve changes, first-order duration returns, empirical VaR/ES, drawdown, rolling Kupiec coverage, Christoffersen independence, regime stress, and block-length sensitivity.",
        "limits": "Approximate hypothetical portfolios omit convexity, security selection, bid–ask costs, taxes, financing, and investability.",
    },
    "commercial-real-estate-risk": {
        "answer": "Public sales records support a transaction-liquidity and price screen; financing scenarios can identify evidence needs, but property-level income, condition, leases, title, and loan terms are required before valuation or investment.",
        "findings": [
            "Borough medians are paired with transaction counts, dispersion, and bootstrap uncertainty rather than treated as appraisal values.",
            "Annual transaction activity shows how observed liquidity changes across the post-2020 rate regime.",
            "The financing layer reports break-even cap-rate requirements under declared LTV, amortization, rate, and DSCR assumptions.",
            "Segments pass only a public-data sufficiency gate and advance to property-level diligence, never directly to acquisition.",
        ],
        "methods": "Administrative transaction filtering, privacy minimization, robust price-per-square-foot summaries, median bootstrap intervals, borough/property-type segment depth, annual liquidity trends, and amortizing-debt break-even cap-rate scenarios.",
        "limits": "The source does not establish arm's-length status, lease income, operating expenses, occupancy, property condition, appraisal value, zoning feasibility, financing availability, or causal regeneration effects.",
    },
    "spatial-equity-planning": {
        "answer": "Need is spatially clustered, but the poverty-priority rule currently outperforms the composite rule on all three reported screening metrics; the composite result is retained as a transparent trade-off scenario, not labeled the winner.",
        "findings": [
            "Moran’s I quantifies local clustering rather than relying on the map alone.",
            "The location-allocation comparison uses a fixed hub count and radius across all strategies.",
            "Radius, need-weight, and coarse-grid sensitivity show how planning priorities depend on service assumptions and spatial scale.",
        ],
        "methods": "ACS rate construction, z-score composite, five-nearest-neighbor Moran’s I, greedy maximum coverage, and tract bootstrap.",
        "limits": "Straight-line distance and tract centroids are planning-screen approximations; ACS margins of error and service capacity require local review.",
    },
}


VISUAL_COPY: dict[str, list[dict[str, str]]] = {
    "population-health-survival": [
        {
            "file": "kaplan-meier.svg",
            "title": "Survival estimates retain censoring and the changing risk set",
            "finding": "The Kaplan–Meier view shows the observed follow-up experience without treating every patient window as complete.",
            "boundary": "Descriptive survival contrast; it does not identify a treatment effect.",
        },
        {
            "file": "cox-hazard-ratios.svg",
            "title": "Adjusted associations remain estimates, not intervention effects",
            "finding": "The multivariable Cox model reports hazard-ratio direction and interval width alongside apparent discrimination.",
            "boundary": "Observed associations remain vulnerable to omitted variables, treatment selection, and cohort transport.",
        },
        {
            "file": "ejection-risk.svg",
            "title": "The absolute risk contrast is paired with resampling uncertainty",
            "finding": "Low ejection fraction is associated with a higher observed event rate, and the patient bootstrap shows how much that contrast moves.",
            "boundary": "The threshold was not prospectively registered and must not be interpreted as a treatment rule.",
        },
        {
            "file": "protocol-comparison.svg",
            "title": "Candidate follow-up protocols expose capture–workload trade-offs",
            "finding": "Protocol comparisons make the operational trade-off visible instead of presenting risk separation as a complete decision.",
            "boundary": "Prospective validation and clinical ownership are required before any protocol use.",
        },
    ],
    "behavioral-reading-experiment": [
        {
            "file": "paired-effect.svg",
            "title": "The primary effect is estimated within participant",
            "finding": "Paired fixation-duration differences preserve the repeated-measures design and display participant-bootstrap uncertainty.",
            "boundary": "The contrast is specific to this sample, task, and measurement protocol.",
        },
        {
            "file": "paired-outcomes.svg",
            "title": "Multiplicity changes how the outcome family is read",
            "finding": "Primary and secondary outcomes are shown together after sign-flip inference and Holm adjustment.",
            "boundary": "Statistical separation does not establish a downstream educational or policy benefit.",
        },
        {
            "file": "protocol-burden.svg",
            "title": "Additional contrast carries an assessment-time cost",
            "finding": "The protocol comparison places group separation beside measurement burden so neither outcome is optimized in isolation.",
            "boundary": "The value placed on burden versus separation is a stakeholder judgment, not a property of the dataset.",
        },
    ],
    "census-income-ai": [
        {
            "file": "model-comparison.svg",
            "title": "The independent test supports benchmarking, not deployment",
            "finding": "Sparse logistic performance is compared with majority and mixed-naive-Bayes baselines on the untouched source test.",
            "boundary": "Historical test performance does not establish contemporary validity or institutional benefit.",
        },
        {
            "file": "subgroup-fpr.svg",
            "title": "Aggregate discrimination does not describe subgroup error",
            "finding": "Sex- and race-stratified false-positive rates expose heterogeneity hidden by a single AUC.",
            "boundary": "These are descriptive error diagnostics; they are not a complete fairness or impact assessment.",
        },
        {
            "file": "calibration.svg",
            "title": "Probability quality is evaluated separately from ranking",
            "finding": "Calibration shows whether predicted probabilities align with observed frequencies across the historical test sample.",
            "boundary": "Calibration in this archive cannot validate a future population, target, threshold, or workflow.",
        },
    ],
    "bike-demand-operations": [
        {
            "file": "hourly-demand.svg",
            "title": "Demand structure is evaluated out of time",
            "finding": "The forecast learns from 2011 and is evaluated on 2012, preserving the direction of operational time.",
            "boundary": "System totals omit station imbalance, travel time, labor rules, and causal service response.",
        },
        {
            "file": "allocation-unmet.svg",
            "title": "Feasible allocations reveal an explicit service trade-off",
            "finding": "Every candidate respects the same resource total and minimum block coverage before unmet demand is compared.",
            "boundary": "Modeled unmet demand is a planning quantity, not a measured service outcome under rollout.",
        },
        {
            "file": "resource-shadow-value.svg",
            "title": "The value of additional capacity is not constant",
            "finding": "Resource shadow values and the perfect-information upper bound show where learning or added capacity could matter.",
            "boundary": "The curve is conditional on the simplified demand and allocation model.",
        },
    ],
    "bank-marketing-response": [
        {
            "file": "monthly-response.svg",
            "title": "Observed response varies across the campaign sequence",
            "finding": "The descriptive view preserves source order and reveals why random row splitting would overstate independence.",
            "boundary": "Monthly response is observational and may reflect targeting, seasonality, or campaign composition.",
        },
        {
            "file": "calibration.svg",
            "title": "Untouched-test probabilities are checked, not assumed",
            "finding": "Model and calibration choices are fixed before the final source-order split is evaluated.",
            "boundary": "Predicting response is not the same as estimating incremental lift, customer value, or profit.",
        },
        {
            "file": "capacity-capture.svg",
            "title": "Capacity planning preserves common campaign shocks",
            "finding": "Every capacity option shares adjacent-row block-bootstrap replicates, so probability-best reflects the same campaign perturbations.",
            "boundary": "Only a randomized campaign can establish incremental effect and ROI.",
        },
    ],
    "sec-nport-filing-review": [
        {
            "file": "portfolio-growth.svg",
            "title": "Walk-forward growth remains benchmarked through time",
            "finding": "The adaptive allocation uses only trailing information and remains beside equal-weight and 60/40 references.",
            "boundary": "Historical adjusted-price performance does not establish future returns, suitability, or executable prices.",
        },
        {
            "file": "risk-adjusted-performance.svg",
            "title": "Risk-adjusted performance is one comparison, not a mandate",
            "finding": "Annualized return is read beside volatility, turnover, drawdown, and explicit benchmarks.",
            "boundary": "The ratio omits investor liabilities, taxes, capacity, and preference-specific utility.",
        },
        {
            "file": "tail-loss.svg",
            "title": "Tail loss remains visible across every strategy",
            "finding": "Expected shortfall reports the severity beyond the historical 95% loss quantile.",
            "boundary": "Historical tails are incomplete stress evidence and can understate an unobserved regime.",
        },
        {
            "file": "probability-best.svg",
            "title": "Probability-best preserves correlated market shocks",
            "finding": "All strategies receive the same sampled month blocks rather than independent perturbations.",
            "boundary": "Bootstrap frequency is conditional on this history, block length, strategy set, and estimation design.",
        },
    ],
    "cfpb-fintech-complaint-operations": [
        {
            "file": "monthly-volume.svg",
            "title": "Calendar structure defines the validation contract",
            "finding": "Complaint volume is shown over time because later-period validation—not a random split—matches the monitoring question.",
            "boundary": "Published complaints are selective and do not measure the underlying incidence of consumer harm.",
        },
        {
            "file": "auc-null-benchmark.svg",
            "title": "The observed AUC is weak against a label-permutation null",
            "finding": "A day-block interval and 500-permutation benchmark make the limited discrimination explicit.",
            "boundary": "A weak ranking result should terminate deployment rather than be rescued by narrative.",
        },
        {
            "file": "calibration.svg",
            "title": "Calibration is tested only after model selection",
            "finding": "The November–December period remains separate from model and calibrator choice.",
            "boundary": "Probability calibration cannot compensate for weak ranking or an outcome with limited decision meaning.",
        },
        {
            "file": "cumulative-gain.svg",
            "title": "The gain curve stays close to random review",
            "finding": "Useful operational ranking should visibly separate from the diagonal; this model does not.",
            "boundary": "The chart supports a negative validation result, not a claim that all future models will fail.",
        },
        {
            "file": "capacity-capture.svg",
            "title": "No tested review capacity delivers reliable lift",
            "finding": "Every capacity is compared with random review and paired with day-block uncertainty.",
            "boundary": "No artificial utility score is introduced to force a preferred operating point.",
        },
        {
            "file": "subproduct-late-rate.svg",
            "title": "Subproduct differences remain descriptive context",
            "finding": "Observed late-response rates identify where definitions and process review may be most useful.",
            "boundary": "The timely-response flag does not establish complaint merit, resolution quality, compliance, or company quality.",
        },
    ],
    "treasury-risk-engineering": [
        {
            "file": "yield-curves.svg",
            "title": "Common market regimes anchor the portfolio comparison",
            "finding": "Observed Treasury curves provide the shared daily shocks used by every hypothetical duration allocation.",
            "boundary": "The portfolios are approximations and omit convexity, security selection, costs, taxes, and financing.",
        },
        {
            "file": "expected-shortfall.svg",
            "title": "Longer duration increases historical tail loss",
            "finding": "Empirical VaR and expected shortfall are reported together so the severity beyond the quantile remains visible.",
            "boundary": "Historical tail loss is scenario evidence, not a guarantee about a future regime.",
        },
        {
            "file": "var-backtest.svg",
            "title": "Coverage and breach dependence are separate diagnostics",
            "finding": "Rolling exceedances, Kupiec coverage, and Christoffersen independence test different failure modes.",
            "boundary": "Passing one backtest does not validate the full return model or authorize investment use.",
        },
    ],
    "commercial-real-estate-risk": [
        {
            "file": "borough-price-per-sqft.svg",
            "title": "Transaction pricing differs across boroughs",
            "finding": "Median nominal price per reported gross square foot is paired with count, dispersion, and bootstrap uncertainty.",
            "boundary": "Administrative sale price is not appraisal value and the source does not establish arm's-length status or condition.",
        },
        {
            "file": "transaction-activity.svg",
            "title": "Observed liquidity changes across calendar years",
            "finding": "Filtered transaction counts show the market activity available to the public-data screen.",
            "boundary": "Recorded sales do not measure unsold inventory, financing availability, demand, or causal rate effects.",
        },
        {
            "file": "financing-stress.svg",
            "title": "Debt cost changes the income hurdle",
            "finding": "Break-even cap rates expose the NOI required by declared LTV, rate, amortization, and DSCR assumptions.",
            "boundary": "The source contains no lease-level NOI, expenses, occupancy, or property-specific loan terms.",
        },
        {
            "file": "segment-observation.svg",
            "title": "Public-data depth gates the next diligence step",
            "finding": "Only sufficiently observed borough/property-type segments advance to property-level evidence collection.",
            "boundary": "Passing the observation gate is not a valuation, planning approval, financing decision, or acquisition recommendation.",
        },
    ],
    "spatial-equity-planning": [
        {
            "file": "need-map.svg",
            "title": "Need is spatially clustered rather than randomly scattered",
            "finding": "The tract map and Moran’s I place candidate hubs inside the observed geography of composite need.",
            "boundary": "Tract centroids and straight-line distance are planning-screen approximations.",
        },
        {
            "file": "strategy-coverage.svg",
            "title": "Composite allocation balances multiple dimensions of need",
            "finding": "Every strategy uses the same hub count and radius before population and need coverage are compared.",
            "boundary": "Weights encode a planning priority and require local stakeholder review.",
        },
        {
            "file": "radius-sensitivity.svg",
            "title": "Service assumptions can reverse the apparent advantage",
            "finding": "Radius, need-weight, and coarse-grid sensitivity reveal dependence on spatial scale and access assumptions.",
            "boundary": "Travel networks, capacity, ACS margins of error, and local site feasibility remain outside the screen.",
        },
    ],
}


def _percent(value: float) -> str:
    return f"{value:.1%}"


def _headline_snapshot(result: dict[str, Any]) -> list[str]:
    if result.get("headline_metrics"):
        return [str(item) for item in result["headline_metrics"]]
    project_id = result["project_id"]
    if project_id == "population-health-survival":
        return [
            f"Observed death-event rate: {_percent(result['death_rate'])}",
            f"Observed 180-day survival: {_percent(result['survival']['180'])}",
            (
                "Low-versus-higher ejection-fraction risk difference: "
                f"{_percent(result['risk_difference'])} "
                f"(bootstrap 95% interval "
                f"{_percent(result['risk_difference_bootstrap_95'][0])} to "
                f"{_percent(result['risk_difference_bootstrap_95'][1])})"
            ),
            (
                "Apparent Cox Harrell C-index: "
                f"{result['cox_proportional_hazards']['harrell_c_index_apparent']:.3f}"
            ),
        ]
    if project_id == "behavioral-reading-experiment":
        primary = result["paired_outcomes_with_multiplicity"]["fixation_duration"]
        return [
            f"Complete participant pairs: {result['data']['complete_pairs']}",
            (
                "Mean paired fixation-duration difference: "
                f"{primary['mean_pseudoword_minus_meaningful']:.2f} "
                f"(bootstrap 95% interval {primary['ci95'][0]:.2f} to "
                f"{primary['ci95'][1]:.2f})"
            ),
            f"Holm-adjusted sign-flip p-value: {primary['holm_adjusted_p']:.4g}",
            (
                "80% power design-sensitivity MDE: "
                f"{result['design_sensitivity']['two_sided_80_percent_power_mde_primary_scale']:.2f}"
            ),
        ]
    if project_id == "census-income-ai":
        return [
            f"Independent-test AUC: {result['overall']['auc']:.3f}",
            f"Independent-test Brier score: {result['overall']['brier']:.3f}",
            (
                "Naive Bayes versus sparse-logistic AUC: "
                f"{result['models']['naive_bayes_baseline']['auc']:.3f} versus "
                f"{result['overall']['auc']:.3f}"
            ),
            f"Selected L2: {result['models']['selected_l2']}",
        ]
    if project_id == "bike-demand-operations":
        voi = result["optimization"]["value_of_perfect_information_upper_bound"]
        return [
            (
                "Forecast MAE improvement versus overall-mean baseline: "
                f"{_percent(result['forecast']['relative_mae_improvement'])}"
            ),
            (
                "Held-out robust-policy unmet share: "
                f"{_percent(voi['robust_static_test_unmet_rate'])}"
            ),
            (
                "Perfect-foresight upper-bound improvement: "
                f"{_percent(voi['maximum_avoidable_unmet_share'])}"
            ),
            (
                "Feasible integer allocations checked: "
                f"{result['optimization']['feasible_allocations_enumerated']:,}"
            ),
        ]
    if project_id == "bank-marketing-response":
        recommended = result["capacity_decision"]["recommended_capacity"]
        option = result["capacity_decision"]["options"][recommended]
        return [
            f"Untouched-test AUC: {result['test']['auc']:.3f}",
            f"Untouched-test Brier score: {result['test']['brier']:.3f}",
            (
                f"Recommended exploratory capacity: top {recommended}; "
                f"observed response capture {_percent(option['positive_capture'])}"
            ),
            f"Shared-block P(best): {_percent(option['probability_best'])}",
        ]
    if project_id == "sec-nport-filing-review":
        adaptive = result["strategy_metrics"]["walk-forward inverse-volatility"]
        probabilities = result[
            "probability_best_shared_block_bootstrap"
        ]["probability_best"]
        return [
            (
                "Walk-forward evaluation: "
                f"{result['data']['evaluated_days']:,} common trading days"
            ),
            (
                "Adaptive annualized return / volatility: "
                f"{_percent(adaptive['annualized_return'])} / "
                f"{_percent(adaptive['annualized_volatility'])}"
            ),
            (
                "Adaptive maximum drawdown: "
                f"{_percent(adaptive['maximum_drawdown'])}"
            ),
            (
                "Adaptive shared-block P(best): "
                f"{_percent(probabilities['walk-forward inverse-volatility'])}"
            ),
        ]
    if project_id == "cfpb-fintech-complaint-operations":
        option = result["capacity_validation"]["5%"]
        auc_interval = result["auc_validation"]["block_bootstrap_95_interval"]
        return [
            f"Model decision: {result['deployment_gate']['status'].replace('_', ' ')}",
            f"Later-period untimely-response prevalence: {_percent(result['test']['prevalence'])}",
            (
                f"Later-period AUC: {result['test']['auc']:.3f} "
                f"(block-bootstrap 95% interval "
                f"{auc_interval[0]:.3f} to {auc_interval[1]:.3f})"
            ),
            (
                "Top-5% lift versus random: "
                f"{option['lift_vs_random']:.2f} "
                f"(95% interval "
                f"{option['lift_block_bootstrap_95_interval'][0]:.2f} to "
                f"{option['lift_block_bootstrap_95_interval'][1]:.2f})"
            ),
        ]
    if project_id == "treasury-risk-engineering":
        baseline = result["portfolios"]["short-baseline"]
        return [
            (
                "Short-baseline historical ES95 loss: "
                f"{_percent(baseline['expected_shortfall95_loss'])}"
            ),
            (
                "Short-baseline rolling VaR exceedance rate: "
                f"{_percent(baseline['backtesting']['observed_exceedance_rate'])}"
            ),
            (
                "Kupiec coverage p approximation: "
                f"{baseline['backtesting']['kupiec_unconditional_coverage']['chi_square_1df_p_approx']:.3f}"
            ),
            "Return model: daily carry plus first-order duration response",
        ]
    if project_id == "commercial-real-estate-risk":
        highest = max(
            result["borough_statistics"].items(),
            key=lambda item: item[1]["median_price_per_sqft"],
        )
        financing = result["financing_stress"]["scenarios"][-1]
        return [
            f"Filtered commercial transactions: {result['data']['transactions']:,}",
            f"Observed borough/property-type segments: {result['data']['segments']}",
            (
                "Highest borough median price per square foot: "
                f"{highest[0]} at ${highest[1]['median_price_per_sqft']:,.0f}"
            ),
            (
                f"Break-even cap rate at {financing['interest_rate']:.1%} debt: "
                f"{_percent(financing['break_even_cap_rate_for_target_dscr'])}"
            ),
        ]
    if project_id == "spatial-equity-planning":
        composite = result["location_allocation"]["strategies"]["composite-equity"]
        missingness = result["robustness"]["rent_to_income_missingness"]
        return [
            f"Analyzed tracts: {result['data']['tracts_analyzed']:,}",
            (
                "Composite-need complete cases: "
                f"{missingness['complete_case_tracts']:,}; missing proxy retained "
                f"outside the composite: {missingness['missing_proxy_tracts']:,}"
            ),
            (
                "Poverty-rate Moran's I: "
                f"{result['spatial_autocorrelation']['morans_i']:.3f}"
            ),
            f"Composite-plan need coverage: {_percent(composite['need_coverage'])}",
            (
                "High-poverty population coverage: "
                f"{_percent(composite['high_poverty_coverage'])}"
            ),
        ]
    return [f"Rows analyzed: {result.get('data', {}).get('rows', 'see results.json')}"]


def _reversal_conditions(result: dict[str, Any]) -> list[str]:
    candidates = [
        result.get("implementation", {}).get("reversal_conditions"),
        result.get("planning_delivery", {}).get("reversal_conditions"),
        result.get("decision_support", {}).get("reversal_conditions"),
        result.get("capacity_decision", {}).get("reversal_conditions"),
        result.get("deployment_gate", {}).get("reversal_conditions"),
    ]
    for value in candidates:
        if value:
            return list(value)
    return [
        "A prospective or external validation reverses the observed ranking.",
        "A missing local constraint changes feasibility or the outcome definition.",
        "A domain owner rejects the analyst-defined threshold, scale, or trade-off.",
    ]


def _md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _snapshot_rows(headline: list[str]) -> list[str]:
    rows: list[str] = []
    for index, item in enumerate(headline, start=1):
        if ":" in item:
            label, value = item.split(":", 1)
        else:
            label, value = f"Evidence signal {index}", item
        rows.append(f"| {_md_cell(label.strip())} | {_md_cell(value.strip())} |")
    return rows


def _append_visual(
    lines: list[str],
    project_root: Path,
    visual: dict[str, str],
) -> None:
    figure = project_root / "outputs/figures" / visual["file"]
    if not figure.exists():
        return
    lines.extend(
        [
            f"### {visual['title']}",
            "",
            visual["finding"],
            "",
            f"![{visual['title']}](figures/{figure.name})",
            "",
            f"> **Interpretation boundary:** {visual['boundary']}",
            "",
        ]
    )


def _decision_visual(project_root: Path) -> tuple[str, str] | None:
    figure_dir = project_root / "outputs/decision/report/figures"
    candidates = (
        ("decision-summary.svg", "Case-specific downstream decision status"),
        ("decision-scorecard.svg", "Case-specific downstream decision scorecard"),
    )
    for filename, alt in candidates:
        if (figure_dir / filename).exists():
            return f"decision/report/figures/{filename}", alt
    return None


def _reproducibility_method_note(project_id: str) -> str:
    if project_id == "social-norm-field-experiment":
        return (
            "`prepare_data.py` and `analyze.py` reproduce the public report from "
            "three committed, hash-locked, non-identifying snapshots. The treatment "
            "aggregate and household-clustered estimates are first recreated from "
            "the terms-governed participant file with `python3 "
            "scripts/build_tailored_source_snapshots.py social --social-csv "
            "/absolute/path/to/reviewed-file.csv --accept-isps-terms`; participant "
            "rows are never "
            "committed to the repository."
        )
    return (
        "All shipped metrics are regenerated by `prepare_data.py` and "
        "`analyze.py`. Random procedures use fixed seeds, and committed raw "
        "files are checked against the SHA-256 values in `source-manifest.json`."
    )


def render_project_report(project_root: Path, result: dict[str, Any]) -> str:
    manifest = load_json(project_root / "source-manifest.json")
    copy = REPORT_COPY[result["project_id"]]
    quality = load_json(project_root / "data/quality-report.json")
    headline = _headline_snapshot(result)
    parameter_register = result.get("parameter_register", [])
    visuals = VISUAL_COPY[result["project_id"]]
    lines = [
        f"# {manifest.get('project_title', manifest['title'])}: analytical project",
        "",
        f"> **Bottom line:** {copy['answer']}",
        "",
        "## Executive Summary",
        "",
        "This source-backed project connects the decision question to its data, "
        "validation design, visual evidence, and explicit claim boundary. The "
        "report structure follows this case rather than a fixed universal template.",
        "",
        "### Evidence at a glance",
        "",
        "| Signal | Observed result |",
        "|---|---|",
        *_snapshot_rows(headline),
        "",
        "## Key findings with visual evidence",
        "",
        "The visual sequence is interleaved with source, design, and limitation "
        "notes so each result stays adjacent to the evidence that supports it.",
        "",
    ]
    _append_visual(lines, project_root, visuals[0])

    lines.extend(
        [
            "## Scope, source, and metric definitions",
            "",
            "| Evidence contract | Recorded value |",
            "|---|---|",
            f"| Source | {_md_cell(manifest['citation'])} |",
            f"| Version | {_md_cell(manifest['version'])} |",
            f"| Accessed | {manifest['accessed_at']} |",
            f"| License | [{manifest['license']}]({manifest['license_url']}) |",
            f"| Analytical grain | {_md_cell(manifest['grain'])} |",
            f"| Expected rows | {manifest['expected_rows']:,} |",
            "| Results | [`results.json`](results.json) |",
            "| Definitions | [`../data/data-dictionary.json`](../data/data-dictionary.json) |",
            "| Quality | [`../data/quality-report.json`](../data/quality-report.json) |",
            "",
        ]
    )
    if len(visuals) > 1:
        _append_visual(lines, project_root, visuals[1])

    lines.extend(
        [
            "## Research design and data quality",
            "",
            "### Design and estimand",
            "",
            "| Design element | Project definition |",
            "|---|---|",
        ]
    )
    design = result.get("study_design")
    if design:
        for key, value in design.items():
            rendered = ", ".join(value) if isinstance(value, list) else str(value)
            lines.append(
                f"| {key.replace('_', ' ').title()} | "
                f"{_md_cell(rendered)} |"
            )
    else:
        lines.append(
            "| Claim class | Unit, time split, target, constraints, and claim class "
            "are defined in `results.json`; no causal estimand is claimed unless "
            "the design explicitly supports one. |"
        )
    lines.extend(
        [
            "",
            "### Data-quality gate",
            "",
            "| Check | Result |",
            "|---|---|",
            f"| Prepared shape | {quality['rows']:,} rows × {quality['columns']} columns |",
            f"| Duplicate primary keys | {quality['duplicate_key_count']} |",
            (
                "| Missing values under declared tokens | "
                f"{sum(quality['missing_count_by_column'].values()):,} |"
            ),
            f"| Privacy review | {quality['privacy_review']['status']} |",
            f"| Quality disposition | **{quality['quality_status']}** |",
            "",
        ]
    )
    if len(visuals) > 2:
        _append_visual(lines, project_root, visuals[2])

    human_system = result.get("human_in_the_loop_system")
    if human_system:
        lines.extend(
            [
                "## Human-in-the-loop system contract",
                "",
                "The validated analytical endpoint is translated into an auditable "
                "workflow without overriding the negative model result.",
                "",
                "| System element | Recorded design |",
                "|---|---|",
                f"| Decision owner | {_md_cell(human_system['decision_owner'])} |",
                f"| Automation status | `{human_system['automation_status']}` |",
                f"| Individual model signal | {_md_cell(human_system['individual_ranking_signal'])} |",
                "",
                "### Review lanes from observed workflow fields",
                "",
                "| Review lane | Records | Rule |",
                "|---|---:|---|",
            ]
        )
        for lane, count in human_system["queue_lanes"].items():
            lines.append(
                f"| `{lane}` | {count:,} | "
                f"{_md_cell(human_system['lane_rule'][lane])} |"
            )
        lines.extend(
            [
                "",
                "The lane counts are workflow observations. They are not findings "
                "about complaint merit, consumer harm, company quality, or compliance. "
                "The complete machine-readable contract is in "
                "[`system-contract.json`](system-contract.json).",
                "",
            ]
        )

    product_contract = result.get("decision_product_contract")
    if product_contract:
        lines.extend(
            [
                "## Decision-product contract",
                "",
                f"Terminal status: `{product_contract['terminal_status']}`. "
                "The same evidence is rendered differently for each role without "
                "changing the underlying numbers or claim boundary.",
                "",
                "| Reader | Evidence view | Permitted action |",
                "|---|---|---|",
            ]
        )
        for role, view in product_contract["stakeholder_views"].items():
            lines.append(
                f"| {role.replace('_', ' ').title()} | "
                f"{_md_cell('; '.join(view['primary_artifacts']))} | "
                f"{_md_cell(view['permitted_action'])} |"
            )
        lines.extend(
            [
                "",
                "The complete role and evidence contract is in "
                "[`decision-product-contract.json`](decision-product-contract.json).",
                "",
            ]
        )

    lines.extend(
        [
            "## Methodology",
            "",
            copy["methods"],
            "",
            _reproducibility_method_note(result["project_id"]),
            "",
        ]
    )
    if len(visuals) > 3:
        _append_visual(lines, project_root, visuals[3])

    if len(visuals) > 4:
        lines.extend(
            [
                "## Additional validation and robustness views",
                "",
                "These views test a separate diagnostic, sensitivity, or evidence "
                "boundary; they do not create a new causal or operational claim.",
                "",
            ]
        )
        for visual in visuals[4:]:
            _append_visual(lines, project_root, visual)

    lines.extend(
        [
            "## Parameter provenance and review",
            "",
            f"{len(parameter_register)} configured or derived parameters are "
            "recorded with their source, uncertainty class, provisional approval, "
            "reviewer status, and use boundary.",
            "",
            "<details>",
            "<summary><strong>Open the complete parameter-level source and review register</strong></summary>",
            "",
            "| Parameter path | Value or distribution | Uncertainty | Source | Approval | Reviewer | Boundary |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for item in parameter_register:
        lines.append(
            "| "
            + " | ".join(
                str(value).replace("|", "\\|")
                for value in (
                    item.get("parameter_path", ""),
                    item.get("value_or_distribution", ""),
                    item.get("uncertainty_type", ""),
                    item.get("source_id", ""),
                    item.get("approval_status", "unreviewed"),
                    item.get("reviewer", "not_assigned"),
                    item.get("notes", ""),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "</details>",
            "",
            "## Limitations, uncertainty, and robustness",
            "",
            copy["limits"],
            "",
            "Bootstrap or scenario stability remains conditional on the observed "
            "sample and declared assumptions; it does not upgrade exploratory "
            "evidence into operational authorization.",
            "",
        ]
    )

    decision_visual = _decision_visual(project_root)
    lines.extend(
        [
            "## What this study cannot establish",
            "",
            "| Boundary | Not established by this project |",
            "|---|---|",
            "| Causality | A causal effect unless the stated design and identification assumptions support it |",
            "| Transport | Performance or effects in an unobserved population, institution, or future regime |",
            "| Authorization | Permission for a clinical, policy, financial, engineering, marketing, or automated action |",
            "",
            "## Decision implications and reversal conditions",
            "",
            "The analysis can prioritize validation, diligence, or a bounded pilot; "
            "it is not itself permission to act. Reconsider the interpretation when:",
            "",
        ]
    )
    lines.extend(f"- {condition}" for condition in _reversal_conditions(result))
    if decision_visual:
        path, alt = decision_visual
        lines.extend(
            [
                "",
                "## Conditional downstream decision layer",
                "",
                "The Evidence Intelligence Report remains the primary record. The "
                "separate Decision Intelligence Brief applies case-specific gates "
                "and may end in a pilot, evidence request, non-deployment, or stop.",
                "",
                f"![{alt}]({path})",
                "",
                "[Open the complete Decision Intelligence Brief](decision/report/decision-report.md).",
            ]
        )
    lines.extend(
        [
            "",
            "## Recommended next steps",
            "",
            "| Step | Action |",
            "|---:|---|",
            "| 1 | Re-run on a newly reviewed source version and compare the source hash, schema, and headline metrics. |",
            "| 2 | Obtain domain-owner review of definitions, thresholds, exclusions, and action constraints. |",
            "| 3 | Pre-register the next prospective or experimental validation before using any decision rule. |",
            "",
            "## Further questions",
            "",
            "- Which missing local variable could reverse the current ranking or interpretation?",
            "- What prospective evidence would be required before operational use?",
            "- Which subgroup, period, or spatial unit is least well represented?",
            "",
            "<details>",
            "<summary><strong>Reproducibility receipt</strong></summary>",
            "",
            f"- Project ID: `{result['project_id']}`",
            f"- Source manifest: [`../source-manifest.json`](../source-manifest.json)",
            f"- Result SHA-256: `{sha256(project_root / 'outputs/results.json')}`",
            "",
            "</details>",
        ]
    )
    return "\n".join(lines) + "\n"


def analyze_project(project_root: Path) -> dict[str, Any]:
    manifest = load_json(project_root / "source-manifest.json")
    config = load_json(project_root / "config.json")
    if config.get("project_id") != manifest["project_id"]:
        raise ValueError("config.json project_id does not match source-manifest.json.")
    processed = project_root / "data/processed/analysis.csv"
    if not processed.exists():
        prepare_project(project_root)
    (project_root / "outputs" / "figures").mkdir(parents=True, exist_ok=True)
    result = ANALYZERS[manifest["project_id"]](project_root)
    result["provenance"] = {
        "source_id": manifest["source_id"],
        "citation": manifest["citation"],
        "version": manifest["version"],
        "license": manifest["license"],
        "accessed_at": manifest["accessed_at"],
        "raw_sha256": {
            Path(item["path"]).name: item["sha256"] for item in manifest["raw_files"]
        },
        "config_sha256": sha256(project_root / "config.json"),
    }
    result["parameter_register"] = _resolve_project_parameter_provenance(
        config,
        manifest,
    )
    write_json(
        project_root / "outputs/parameter-provenance.json",
        {
            "schema_version": "1.0",
            "project_id": result["project_id"],
            "decision_use": "exploratory",
            "records": result["parameter_register"],
            "coverage": {
                "configured_parameter_count": len(config.get("parameters", {})) + 1,
                "resolved_parameter_count": len(
                    [
                        item
                        for item in result["parameter_register"]
                        if item["parameter_path"].startswith("config.")
                    ]
                ),
                "source_coverage_rate": 1.0,
                "independent_domain_review_rate": 0.0,
            },
            "coverage_boundary": (
                "Complete traceability does not imply external approval or strong "
                "evidence. All records remain exploratory and independently unreviewed."
            ),
        },
    )
    write_json(project_root / "outputs/results.json", result)
    (project_root / "outputs/report.md").write_text(
        render_project_report(project_root, result),
        encoding="utf-8",
    )
    write_json(
        project_root / "outputs/chart-map.json",
        {
            "project_id": result["project_id"],
            "charts": [
                {
                    "path": f"figures/{figure.name}",
                    "question": next(
                        (
                            item["title"]
                            for item in VISUAL_COPY[result["project_id"]]
                            if item["file"] == figure.name
                        ),
                        figure.stem.replace("-", " "),
                    ),
                    "supported_finding": next(
                        (
                            item["finding"]
                            for item in VISUAL_COPY[result["project_id"]]
                            if item["file"] == figure.name
                        ),
                        "Diagnostic or sensitivity evidence.",
                    ),
                    "interpretation_boundary": next(
                        (
                            item["boundary"]
                            for item in VISUAL_COPY[result["project_id"]]
                            if item["file"] == figure.name
                        ),
                        "This visual does not create a causal or operational claim.",
                    ),
                    "source_id": manifest["source_id"],
                    "palette_policy": "single-root preferred; non-color labels retained",
                }
                for figure in sorted((project_root / "outputs/figures").glob("*.svg"))
            ],
        },
    )
    return result


def _resolve_project_parameter_provenance(
    config: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    """Expand project configuration into one traceable record per parameter."""

    registered = config.get("parameter_register", [])

    def match(key: str) -> dict[str, Any] | None:
        for item in registered:
            tokens = str(item.get("parameter", "")).split("/")
            if key == item.get("parameter") or key in tokens:
                return item
        return None

    values = {"analysis_seed": config.get("analysis_seed")}
    values.update(config.get("parameters", {}))
    records: list[dict[str, Any]] = []
    used_entries: set[int] = set()
    for key, value in values.items():
        item = match(key)
        if item is None:
            item = {
                "parameter": key,
                "source_id": "analysis-protocol",
                "status": "reproducibility choice",
                "approved_by": "repository author self-review",
                "boundary": "Computational setting; it does not increase evidence quality.",
            }
        else:
            used_entries.add(registered.index(item))
        status = str(item.get("status", "unclassified analytical choice"))
        status_folded = status.casefold()
        uncertainty_type = (
            "scenario"
            if any(
                token in status_folded
                for token in ("scenario", "hypothetical", "value judgment")
            )
            else "none"
        )
        evidence_strength = (
            "observed"
            if any(
                token in status_folded
                for token in ("source supplied", "source-defined", "observed")
            )
            else "assumed"
        )
        records.append(
            {
                "parameter_path": (
                    "config.analysis_seed"
                    if key == "analysis_seed"
                    else f"config.parameters.{key}"
                ),
                "label": key.replace("_", " "),
                "value_or_distribution": value,
                "unit": "configuration value",
                "uncertainty_type": uncertainty_type,
                "source_id": item["source_id"],
                "source_fact": (
                    f"Registered project configuration for {key}; source dataset "
                    f"is {manifest['source_id']}."
                ),
                "transformation": "Used directly by the reproducible analysis script.",
                "owner": "Repository analysis author",
                "reviewer": "not_assigned",
                "review_date": "2026-07-27",
                "approval_status": "provisional_self_review",
                "approval_scope": "exploratory",
                "approval_chain": [
                    {
                        "sequence": 1,
                        "role": "model_author",
                        "actor": item.get(
                            "approved_by",
                            "repository author self-review",
                        ),
                        "status": "approved",
                        "date": "2026-07-27",
                        "scope": "Exploratory repository analysis",
                    },
                    {
                        "sequence": 2,
                        "role": "independent_domain_reviewer",
                        "actor": "not_assigned",
                        "status": "not_obtained",
                        "date": None,
                        "scope": "Required before operational use",
                    },
                ],
                "evidence_strength": evidence_strength,
                "notes": item.get("boundary", ""),
            }
        )
    for index, item in enumerate(registered):
        if index in used_entries:
            continue
        records.append(
            {
                "parameter_path": f"derived.{item['parameter'].replace('/', '.')}",
                "label": item["parameter"].replace("_", " ").replace("/", " / "),
                "value_or_distribution": "derived or source-defined field",
                "unit": "project-specific",
                "uncertainty_type": "none",
                "source_id": item["source_id"],
                "source_fact": item.get("status", ""),
                "transformation": "Defined or derived in prepare_data.py or analyze.py.",
                "owner": "Repository analysis author",
                "reviewer": "not_assigned",
                "review_date": "2026-07-27",
                "approval_status": "provisional_self_review",
                "approval_scope": "exploratory",
                "approval_chain": [
                    {
                        "sequence": 1,
                        "role": "model_author",
                        "actor": item.get(
                            "approved_by",
                            "repository author self-review",
                        ),
                        "status": "approved",
                        "date": "2026-07-27",
                        "scope": "Exploratory repository analysis",
                    },
                    {
                        "sequence": 2,
                        "role": "independent_domain_reviewer",
                        "actor": "not_assigned",
                        "status": "not_obtained",
                        "date": None,
                        "scope": "Required before operational use",
                    },
                ],
                "evidence_strength": "observed_or_assumed_as_labeled",
                "notes": item.get("boundary", ""),
            }
        )
    return records


def _criteria_for_project(project_id: str) -> list[dict[str, Any]]:
    if project_id == "population-health-survival":
        return [
            {"id": "high_risk_capture", "label": "Observed event capture", "direction": "maximize", "weight": 0.45, "unit": "share", "scale": {"worst": 0, "best": 1}},
            {"id": "workload_share", "label": "Follow-up workload", "direction": "minimize", "weight": 0.30, "unit": "share", "scale": {"worst": 1, "best": 0}},
            {"id": "sex_selection_gap", "label": "Recorded-sex selection gap", "direction": "minimize", "weight": 0.25, "unit": "absolute share", "scale": {"worst": 0.5, "best": 0}},
        ]
    if project_id == "behavioral-reading-experiment":
        return [
            {"id": "group_separation", "label": "Standardized group separation", "direction": "maximize", "weight": 0.45, "unit": "standardized difference", "scale": {"worst": 0, "best": 2}},
            {"id": "mean_fixation_duration", "label": "Assessment burden", "direction": "minimize", "weight": 0.30, "unit": "mean fixation duration", "scale": {"worst": 600, "best": 150}},
            {"id": "measurement_stability", "label": "Measurement stability", "direction": "maximize", "weight": 0.25, "unit": "index", "scale": {"worst": 0, "best": 1}},
        ]
    if project_id == "bike-demand-operations":
        return [
            {"id": "modeled_residual_imbalance", "label": "Modeled residual imbalance", "direction": "minimize", "weight": 0.45, "unit": "share", "scale": {"worst": 1, "best": 0}},
            {"id": "unserved_station_hour_share", "label": "Station-hours with residual imbalance", "direction": "minimize", "weight": 0.35, "unit": "share", "scale": {"worst": 1, "best": 0}},
            {"id": "allocation_concentration", "label": "Allocation concentration", "direction": "minimize", "weight": 0.20, "unit": "Herfindahl index", "scale": {"worst": 1, "best": 0}},
        ]
    if project_id == "treasury-risk-engineering":
        return [
            {"id": "annualized_mean_return", "label": "Historical annualized return", "direction": "maximize", "weight": 0.30, "unit": "return fraction", "scale": {"worst": -0.10, "best": 0.12}},
            {"id": "expected_shortfall95_loss", "label": "Historical ES95 loss", "direction": "minimize", "weight": 0.45, "unit": "daily loss fraction", "scale": {"worst": 0.08, "best": 0}},
            {"id": "worst_day_loss", "label": "Worst historical day", "direction": "minimize", "weight": 0.25, "unit": "daily loss fraction", "scale": {"worst": 0.10, "best": 0}},
        ]
    if project_id == "sec-nport-filing-review":
        return [
            {"id": "high_risk_capture", "label": "Internal high-score capture", "direction": "maximize", "weight": 0.45, "unit": "share", "scale": {"worst": 0, "best": 1}},
            {"id": "review_share", "label": "Filing-review workload", "direction": "minimize", "weight": 0.35, "unit": "share", "scale": {"worst": 1, "best": 0}},
            {"id": "average_review_score", "label": "Average selected review score", "direction": "maximize", "weight": 0.20, "unit": "percentile index", "scale": {"worst": 0, "best": 1}},
        ]
    if project_id == "commercial-real-estate-risk":
        return [
            {"id": "transaction_share", "label": "Public transaction depth", "direction": "maximize", "weight": 0.45, "unit": "share", "scale": {"worst": 0, "best": 0.60}},
            {"id": "price_dispersion_ratio", "label": "Relative price dispersion", "direction": "minimize", "weight": 0.30, "unit": "MAD/median", "scale": {"worst": 1.5, "best": 0}},
            {"id": "geocoded_share", "label": "Approximate geography coverage", "direction": "maximize", "weight": 0.25, "unit": "share", "scale": {"worst": 0, "best": 1}},
        ]
    return [
        {"id": "need_coverage", "label": "Need-weighted coverage", "direction": "maximize", "weight": 0.45, "unit": "share", "scale": {"worst": 0, "best": 1}},
        {"id": "high_poverty_coverage", "label": "High-poverty population coverage", "direction": "maximize", "weight": 0.35, "unit": "share", "scale": {"worst": 0, "best": 1}},
        {"id": "population_weighted_distance_km", "label": "Population-weighted distance", "direction": "minimize", "weight": 0.20, "unit": "km", "scale": {"worst": 50, "best": 0}},
    ]


def _case_options(project_id: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    if project_id == "population-health-survival":
        source = result["candidate_protocols"]
    elif project_id == "behavioral-reading-experiment":
        source = result["candidate_protocols"]
    elif project_id == "bike-demand-operations":
        source = result["optimization"]["scenario_evaluation"]
    elif project_id == "treasury-risk-engineering":
        source = result["portfolios"]
    elif project_id in {
        "sec-nport-filing-review",
        "commercial-real-estate-risk",
    }:
        source = result["decision_options"]
    else:
        source = result["location_allocation"]["strategies"]
    alternatives = []
    for index, (identifier, item) in enumerate(source.items()):
        metrics = {}
        for criterion in _criteria_for_project(project_id):
            key = criterion["id"]
            samples = item.get("bootstrap", {}).get(key)
            if samples:
                metrics[key] = {
                    "distribution": "empirical",
                    "values": [round(float(value), 8) for value in samples[:250]],
                    "uncertainty_type": "parameter",
                }
            else:
                metrics[key] = {
                    "distribution": "fixed",
                    "value": round(float(item[key]), 8),
                    "uncertainty_type": "none",
                }
        alternatives.append(
            {
                "id": identifier,
                "label": identifier.replace("-", " ").title(),
                "description": "Candidate derived from the source-backed project output.",
                "metrics": metrics,
            }
        )
    if alternatives and not any(
        token in alternatives[0]["id"] for token in ("baseline", "current")
    ):
        alternatives[0]["id"] = "baseline-" + alternatives[0]["id"]
        alternatives[0]["label"] = "Baseline: " + alternatives[0]["label"]
    return alternatives


def _case_question(project_id: str) -> tuple[str, str, str]:
    mapping = {
        "population-health-survival": (
            "Which follow-up triage rule should advance to prospective clinical validation?",
            "Population health and biostatistics",
            "Prospective pilot design; no clinical deployment",
        ),
        "behavioral-reading-experiment": (
            "Which reading-assessment protocol should advance to a larger preregistered validation study?",
            "Behavioral science and experimental design",
            "Next validation study",
        ),
        "bike-demand-operations": (
            "Which fixed-budget station-hour rebalancing scenario should advance to a bounded operations pilot?",
            "Operations research and systems engineering",
            "Prospective operations pilot only",
        ),
        "treasury-risk-engineering": (
            "Which duration profile should remain in exploratory risk review under the historical evidence?",
            "Financial risk engineering",
            "Historical-risk review only",
        ),
        "sec-nport-filing-review": (
            "Which transparent N-PORT review threshold should advance to analyst filing review?",
            "Regulatory filing analytics and financial risk",
            "Targeted filing review only",
        ),
        "commercial-real-estate-risk": (
            "Which borough market should advance first to property-level commercial real-estate diligence?",
            "Real-estate finance and market screening",
            "Pre-acquisition evidence collection only",
        ),
        "spatial-equity-planning": (
            "Which five-hub prioritization rule should advance to local network and stakeholder review?",
            "Urban planning and spatial policy",
            "Pre-feasibility planning",
        ),
    }
    return mapping[project_id]


def build_decision_case(project_root: Path, repository_root: Path) -> Path | None:
    project_id = load_json(project_root / "source-manifest.json")["project_id"]
    if project_id not in PROJECTS_WITH_CASES:
        embedded = (
            project_root / "outputs" / "decision-analysis.json"
        ).exists()
        note = {
            "project_id": project_id,
            "decision_case_created": embedded,
            "public_layer": "embedded_within_real_project" if embedded else "diagnostic_project",
            "reason": (
                "A decision analysis is already embedded in this real-data project."
                if embedded
                else "The project supplies predictive, financial-diagnostic, or "
                "governance evidence without forcing an artificial action comparison."
            ),
        }
        write_json(project_root / "outputs/decision-case-status.json", note)
        return (
            project_root / "outputs" / "decision-analysis.json"
            if embedded
            else None
        )
    results_path = project_root / "outputs/results.json"
    if not results_path.exists():
        analyze_project(project_root)
    result = load_json(results_path)
    manifest = load_json(project_root / "source-manifest.json")
    question, domain, horizon = _case_question(project_id)
    criteria = _criteria_for_project(project_id)
    factors = [
        {
            "id": "shared-adverse-evidence-shock",
            "label": "Shared adverse evidence shock",
            "description": "A common latent shock moves empirical metrics across all alternatives.",
            "loadings": {
                criterion["id"]: (
                    -0.28 if criterion["direction"] == "maximize" else 0.28
                )
                for criterion in criteria
            },
        }
    ]
    project_source_id = f"{project_id}-analysis-output"
    analyst_source_id = "portfolio-author-governance-assumptions"
    sources = [
        {
            "id": project_source_id,
            "citation": (
                f"{manifest['citation']}; project outputs/results.json, generated "
                "from the hash-locked snapshot."
            ),
            "source_type": "reproducible_project_output",
            "as_of": manifest["accessed_at"],
            "owner": "Original publisher and repository analysis author",
            "approved_decision_uses": ["exploratory"],
            "approval_chain": [
                {
                    "sequence": 1,
                    "role": "model_author",
                    "actor": "Repository analysis author",
                    "status": "approved",
                    "date": "2026-07-27",
                    "scope": "Exploratory portfolio demonstration only",
                }
            ],
        },
        {
            "id": analyst_source_id,
            "citation": (
                "Portfolio author governance register: weights, scales, scenario "
                "probabilities, thresholds, and dependence assumptions."
            ),
            "source_type": "analyst_judgment_not_externally_approved",
            "as_of": "2026-07-27",
            "owner": "Repository analysis author",
            "approved_decision_uses": ["exploratory"],
            "approval_chain": [
                {
                    "sequence": 1,
                    "role": "self_review",
                    "actor": "Repository analysis author",
                    "status": "approved",
                    "date": "2026-07-27",
                    "scope": "Exploratory comparison; no institutional approval",
                }
            ],
        },
    ]
    rule_source = {
        "metric_distribution": project_source_id,
        "criterion_weight": analyst_source_id,
        "criterion_scale": analyst_source_id,
        "scenario_probability": analyst_source_id,
        "scenario_adjustment": analyst_source_id,
        "constraint_threshold": analyst_source_id,
        "risk_aversion": analyst_source_id,
        "maximum_violation_rate": analyst_source_id,
        "weight_sensitivity": analyst_source_id,
        "correlation_loading": analyst_source_id,
        "correlation_stress": analyst_source_id,
    }
    case_id = f"real-{project_id}"
    case = {
        "schema_version": "1.3",
        "case_id": case_id,
        "title": question.rstrip("?"),
        "domain": domain,
        "decision_owner": "Hypothetical domain review panel; no real owner authorization",
        "decision_question": question,
        "time_horizon": horizon,
        "evidence": {
            "type": "source-backed exploratory project evidence",
            "decision_use": "exploratory",
            "as_of": manifest["accessed_at"],
            "sources": [
                manifest["citation"],
                f"projects/{project_id}/outputs/results.json",
            ],
            "causal_claim_status": (
                "No causal claim unless explicitly identified in the source design; "
                "the decision comparison is exploratory."
            ),
            "limitations": [
                REPORT_COPY[project_id]["limits"],
                "Weights, scales, scenarios, and correlation loadings are analyst judgments without external approval.",
            ],
        },
        "criteria": criteria,
        "alternatives": _case_options(project_id, result),
        "scenarios": [
            {"id": "observed-evidence", "label": "Observed evidence base", "probability": 0.75, "adjustments": {}},
            {
                "id": "adverse-transfer",
                "label": "Adverse transfer to a new setting",
                "probability": 0.25,
                "adjustments": {
                    "*": {
                        criterion["id"]: {
                            "multiply": 0.92 if criterion["direction"] == "maximize" else 1.08
                        }
                        for criterion in criteria
                    }
                },
            },
        ],
        "uncertainty_model": {
            "method": "latent_factor_gaussian_copula",
            "stress_multiplier": 1.35,
            "factors": factors,
        },
        "parameter_governance": {
            "sources": sources,
            "rules": [
                {"parameter_type": parameter_type, "source_id": source_id}
                for parameter_type, source_id in rule_source.items()
            ],
        },
        "constraints": [],
        "risk_aversion": 0.25,
        "max_constraint_violation_rate": 0.10,
        "sensitivity_weight_multiplier": 1.5,
        "readiness_thresholds": {
            "minimum_probability_best": 0.50,
            "minimum_weight_stability": 0.75,
            "minimum_scenario_stability": 0.75,
            "maximum_scale_clipping_rate": 0.05,
        },
        "decision_notes": [
            "The comparison selects a candidate for further review, not an operational action.",
            "No institutional, clinical, financial, engineering, or policy approval is represented.",
        ],
    }
    case_root = project_root / "outputs" / "decision"
    case_root.mkdir(parents=True, exist_ok=True)
    write_json(case_root / "case.json", case)
    write_json(project_root / "outputs/decision-case.json", case)
    input_rows = [
        (
            "Empirical metric distributions",
            project_source_id,
            "source-backed project output",
            "Exploratory",
            "Bootstrap or empirical values generated by analyze.py",
        ),
        (
            "Criteria weights and reference scales",
            analyst_source_id,
            "analyst judgment",
            "Exploratory only",
            "Not elicited from a real decision owner",
        ),
        (
            "Adverse-transfer scenario",
            analyst_source_id,
            "stress assumption",
            "Exploratory only",
            "Not an estimated forecast probability",
        ),
        (
            "Shared-factor loadings",
            analyst_source_id,
            "dependence assumption",
            "Exploratory only",
            "Stress-tests correlation; not empirically estimated",
        ),
    ]
    lines = [
        f"# Evidence input table: {question.rstrip('?')}",
        "",
        "| Input family | Source ID | Evidence class | Approved use | Boundary |",
        "|---|---|---|---|---|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in input_rows)
    lines.extend(
        [
            "",
            f"Official source: {manifest['citation']}",
            "",
            "The only approval recorded here is the repository author's self-review for "
            "exploratory demonstration. It is not institutional or operational approval.",
        ]
    )
    (case_root / "evidence-input-table.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    write_json(
        project_root / "outputs/decision-case-status.json",
        {
            "project_id": project_id,
            "decision_case_created": True,
            "public_layer": "embedded_within_real_project",
            "case_path": "outputs/decision/case.json",
            "decision_use": "candidate for prospective or domain review only",
        },
    )
    return case_root / "case.json"


def project_main(action: str, project_file: str, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    if action == "download":
        parser.add_argument("--refresh", action="store_true")
    arguments = parser.parse_args(argv)
    project_root = Path(project_file).resolve().parent
    if action == "download":
        receipt = download_project(project_root, refresh=arguments.refresh)
        print(json.dumps(receipt, indent=2))
    elif action == "prepare":
        print(json.dumps(prepare_project(project_root), indent=2))
    elif action == "analyze":
        result = analyze_project(project_root)
        print(json.dumps({"project_id": result["project_id"], "status": "complete"}))
    elif action == "case":
        repository_root = project_root.parents[1]
        path = build_decision_case(project_root, repository_root)
        print(path if path else "No decision case: intentional analytical boundary.")
    else:
        raise ValueError(action)
    return 0

__all__ = [name for name in globals() if not name.startswith("__")]
