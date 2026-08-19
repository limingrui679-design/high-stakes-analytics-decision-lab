# Fifteen case precedents

These school-neutral precedents are navigation aids. Reuse a method contract, not a saved empirical result, threshold, subgroup, weight, causal claim, or recommendation. Follow the linked report for full sources and limitations.

| # | Case | Route | Capability path | Valid endpoint |
|---:|---|---|---|---|
| 01 | [Jersey City Bike Demand and Rebalancing Evidence](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/01-bike-demand-operations.md) | descriptive / predictive / prescriptive | Analytics to action → AI and model validation → Risk and decision analysis | claim-bounded decision review |
| 02 | [Cross-City 311 Distribution Shift and Transfer Gate](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/02-cross-city-311-shift.md) | descriptive / diagnostic / decision | Data systems and governance → Statistical research → Spatial equity and planning | transfer refused |
| 03 | [Capacity-Constrained Marketing Pilot](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/03-bank-marketing-response.md) | descriptive / predictive / prescriptive | Analytics to action → AI and model validation → Behavior and policy evidence | randomized pilot required |
| 04 | [ACS Employment AI Temporal Transport and Audit](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/04-census-income-ai.md) | descriptive / predictive | AI and model validation → Statistical research → Data systems and governance | do not use for consequential action |
| 05 | [Treasury Curve and Tail-Risk Decision Engine](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/05-treasury-risk-engineering.md) | descriptive / predictive / prescriptive | Risk and decision analysis → Statistical research → Analytics to action | claim-bounded decision review |
| 06 | [Human-in-the-Loop Complaint Triage Information System](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/06-cfpb-fintech-complaint-operations.md) | descriptive / predictive | Data systems and governance → AI and model validation → Analytics to action | do not deploy |
| 07 | [Commercial Real Estate Diligence Decision Product](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/07-commercial-real-estate-risk.md) | descriptive / diagnostic / prescriptive | Analytics to action → Risk and decision analysis → Spatial equity and planning | claim-bounded decision review |
| 08 | [Wildfire Mitigation Evidence Allocation Under Uncertainty](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/08-wildfire-mitigation-under-uncertainty.md) | descriptive / diagnostic / decision | Risk and decision analysis → Behavior and policy evidence → Spatial equity and planning | evidence request before mitigation allocation |
| 09 | [SEC N-PORT Liquidity and Crowding Filing Review](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/09-sec-nport-filing-review.md) | descriptive / diagnostic / predictive / prescriptive | Risk and decision analysis → Data systems and governance → Analytics to action | claim-bounded decision review |
| 10 | [Social-Norm Field Experiment with Household-Clustered Inference](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/10-social-norm-field-experiment.md) | descriptive / diagnostic / decision | Behavior and policy evidence → Statistical research | observed field effect no new campaign authorization |
| 11 | [Population Health Risk Transport Across NHIS Cohorts](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/11-population-health-survival.md) | descriptive / predictive / prescriptive | Population health and informatics → AI and model validation → Data systems and governance | claim-bounded decision review |
| 12 | [Opportunity Zone One-Year Policy Evidence Screen](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/12-opportunity-zone-policy-evaluation.md) | descriptive / diagnostic / decision | Behavior and policy evidence → Statistical research → Spatial equity and planning | associational policy screen only |
| 13 | [Small-Sample Repeated-Measures Inference](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/13-behavioral-reading-experiment.md) | descriptive / inferential | Statistical research → Behavior and policy evidence | claim-bounded decision review |
| 14 | [NHANES Mortality Transportability and Population Inequality](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/14-nhanes-population-transportability.md) | descriptive / diagnostic / decision | Population health and informatics → Statistical research → AI and model validation | population research only |
| 15 | [Spatial Equity Planning with Transit and Site-Evidence Gates](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/15-spatial-equity-planning.md) | descriptive / prescriptive | Spatial equity and planning → Behavior and policy evidence → Analytics to action | claim-bounded decision review |

## Selection notes

### 01 · Jersey City Bike Demand and Rebalancing Evidence

- Question: Can station-hour history improve held-out pickup forecasts, and which fixed-budget rebalancing scenario deserves a bounded operations pilot?
- Reviewer signals: temporal holdout; simple baseline; fixed capacity; modeled pilot boundary.
- Boundary: Rebalancing outcomes are modeled; no stockout, routing, labor, or achieved-service claim.
- Full reproducible project: [bike-demand-operations](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/bike-demand-operations)

### 02 · Cross-City 311 Distribution Shift and Transfer Gate

- Question: Are city service-request distributions sufficiently comparable to transfer an analytical rule between Chicago and New York?
- Reviewer signals: ontology audit; distribution shift; transfer refusal; administrative-data boundary.
- Boundary: Administrative shift audit only; requests are not latent need or service quality.
- Full reproducible project: [cross-city-311-shift](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/cross-city-311-shift)

### 03 · Capacity-Constrained Marketing Pilot

- Question: Can pre-contact information concentrate observed responses under a fixed outreach capacity without using post-contact leakage?
- Reviewer signals: leakage-safe timing; untouched test; capacity capture; randomized pilot requirement.
- Boundary: Observed response concentration is not incremental lift, causal treatment effect, profit, or return on outreach.
- Full reproducible project: [bank-marketing-response](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/bank-marketing-response)

### 04 · ACS Employment AI Temporal Transport and Audit

- Question: How well does a protected-attribute-excluded employment model developed on 2019 PUMS transport to 2023?
- Reviewer signals: temporal transport; survey weights; protected-attribute audit; no consequential use.
- Boundary: No eligibility, hiring, credit, benefits, or other consequential action.
- Full reproducible project: [census-income-ai](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/census-income-ai)

### 05 · Treasury Curve and Tail-Risk Decision Engine

- Question: How do duration choices change historical tail loss, backtest behavior, and sensitivity to dependent market shocks?
- Reviewer signals: tail loss; coverage backtest; regime comparison; dependent market shocks.
- Boundary: First-order duration omits convexity, security selection, costs, financing, taxes, liquidity, and future-regime uncertainty.
- Full reproducible project: [treasury-risk-engineering](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/treasury-risk-engineering)

### 06 · Human-in-the-Loop Complaint Triage Information System

- Question: Does a privacy-minimized complaint model create reliable ranking gain over random review in a later calendar period?
- Reviewer signals: privacy minimization; calendar holdout; human review; do not deploy.
- Boundary: The timely flag is not complaint merit, harm, resolution quality, company quality, or compliance; the 2022 model may not transport.
- Full reproducible project: [cfpb-fintech-complaint-operations](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/cfpb-fintech-complaint-operations)

### 07 · Commercial Real Estate Diligence Decision Product

- Question: Which borough/property-type segments have enough public transaction evidence for property-level diligence, and how do financing-rate assumptions change the income hurdle?
- Reviewer signals: transaction screening; financing sensitivity; diligence workflow; missing property evidence.
- Boundary: The source does not establish arm's-length status, NOI, expenses, occupancy, condition, appraisal value, debt terms, or causal regeneration effects.
- Full reproducible project: [commercial-real-estate-risk](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/commercial-real-estate-risk)

### 08 · Wildfire Mitigation Evidence Allocation Under Uncertainty

- Question: Which exposure-weighted evidence-collection allocation is least fragile across historical, recent, and tail-fire scenarios?
- Reviewer signals: scenario regret; tail exposure; feasibility gap; evidence request.
- Boundary: No fires-prevented or acres-prevented estimate; mitigation action blocked pending effectiveness and feasibility evidence.
- Full reproducible project: [wildfire-mitigation-under-uncertainty](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/wildfire-mitigation-under-uncertainty)

### 09 · SEC N-PORT Liquidity and Crowding Filing Review

- Question: Which transparent concentration, liquidity, and redemption indicators should trigger targeted filing review?
- Reviewer signals: transparent indicators; review capacity; filing lineage; fiduciary boundary.
- Boundary: Filing review only; no expected-return, suitability, fund-quality, or investment recommendation.
- Full reproducible project: [sec-nport-filing-review](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/sec-nport-filing-review)

### 10 · Social-Norm Field Experiment with Household-Clustered Inference

- Question: What were the intent-to-treat turnout effects of randomized social-pressure mailings after household clustering?
- Reviewer signals: randomized assignment; household clustering; intent-to-treat; no new campaign authorization.
- Boundary: Causal scope is the historical randomized experiment; no new campaign authorization.
- Full reproducible project: [social-norm-field-experiment](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/social-norm-field-experiment)

### 11 · Population Health Risk Transport Across NHIS Cohorts

- Question: Do simple population-risk cells developed in NHIS 2016 retain discrimination and calibration in the 2017 linked-mortality cohort?
- Reviewer signals: linked cohorts; temporal transport; workload screen; no individual clinical action.
- Boundary: Population-risk validation only; no individual diagnosis, treatment, or clinical deployment.
- Full reproducible project: [population-health-survival](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/population-health-survival)

### 12 · Opportunity Zone One-Year Policy Evidence Screen

- Question: How did selected tract outcomes change immediately after QOZ designation relative to observed-covariate matches?
- Reviewer signals: matched change; support diagnostics; control reuse; associational policy screen.
- Boundary: Associational one-year screen; no causal effect because parallel trends are unavailable.
- Full reproducible project: [opportunity-zone-policy-evaluation](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/opportunity-zone-policy-evaluation)

### 13 · Small-Sample Repeated-Measures Inference

- Question: How does passage type change eye-movement burden within the same participant, and how stable is the contrast across reader groups?
- Reviewer signals: within-participant contrast; small sample; clustered inference; generalization boundary.
- Boundary: The public sample is small and does not establish downstream educational outcomes or an intervention effect.
- Full reproducible project: [behavioral-reading-experiment](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/behavioral-reading-experiment)

### 14 · NHANES Mortality Transportability and Population Inequality

- Question: Do population mortality risk patterns transport between NHANES cohorts, and what inequality gradient remains visible?
- Reviewer signals: survey weights; external cohort check; calibration; population inequality.
- Boundary: Population research only; no individual diagnosis or treatment.
- Full reproducible project: [nhanes-population-transportability](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/nhanes-population-transportability)

### 15 · Spatial Equity Planning with Transit and Site-Evidence Gates

- Question: Which tract-level service-hub priorities merit local review after observed rapid-transit proximity is added?
- Reviewer signals: complete-case route; missingness sensitivity; observed transit proximity; site evidence gate.
- Boundary: No site recommendation until parcel, zoning, network, cost, and community evidence is supplied.
- Full reproducible project: [spatial-equity-planning](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/tree/main/examples/real-data-cases/projects/spatial-equity-planning)
