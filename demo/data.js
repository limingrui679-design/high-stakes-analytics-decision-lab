window.HSADL_DEMO = {
  "schema_version": "1.0",
  "school_neutral": true,
  "boundary": "Public-data research portfolio; no production deployment, institutional adoption, external review, or achieved real-world impact is implied.",
  "metrics": {
    "cases": 30,
    "routes": 4,
    "capabilities": 8,
    "accessible_figures": 176
  },
  "capabilities": [
    {
      "id": "analytics-to-action",
      "label": "Analytics to action",
      "description": "Connect prediction or diagnosis to capacity, workflow, implementation, communication, and a bounded next step."
    },
    {
      "id": "statistical-research",
      "label": "Statistical research",
      "description": "Define the estimand, preserve the data-generating structure, quantify uncertainty, test robustness, and state the transport boundary."
    },
    {
      "id": "data-systems-governance",
      "label": "Data systems and governance",
      "description": "Make data contracts, semantics, lineage, privacy, human review, failure states, and reproducibility part of the analytical system."
    },
    {
      "id": "ai-validation",
      "label": "AI and model validation",
      "description": "Use leakage-safe validation, baselines, calibration, drift and subgroup checks, including a legitimate non-deployment result."
    },
    {
      "id": "risk-decision",
      "label": "Risk and decision analysis",
      "description": "Compare feasible choices under dependent uncertainty, tail risk, scenario stress, value judgments, and reversal conditions."
    },
    {
      "id": "behavior-policy",
      "label": "Behavior and policy evidence",
      "description": "Separate observed behavior, randomized or associational evidence, mechanisms, intervention claims, ethics, and implementation authority."
    },
    {
      "id": "health-informatics",
      "label": "Population health and informatics",
      "description": "Respect population, cohort, measurement and information-system semantics while separating research validation from individual clinical use."
    },
    {
      "id": "spatial-equity",
      "label": "Spatial equity and planning",
      "description": "Connect place-based evidence, access, distribution, uncertainty and feasibility without turning a screening model into a site or policy decision."
    }
  ],
  "cases": [
    {
      "number": "01",
      "id": "bike-demand-operations",
      "title": "Jersey City Bike Demand and Rebalancing Evidence",
      "domain": "Operations Research",
      "routes": [
        "descriptive",
        "predictive",
        "prescriptive"
      ],
      "question": "Can station-hour history improve held-out pickup forecasts, and which fixed-budget rebalancing scenario deserves a bounded operations pilot?",
      "result": "Held-out station-hour MAE is 0.69 pickups/day, a 33.1% improvement over the hour-only baseline.",
      "endpoint": "claim-bounded decision review",
      "boundary": "Rebalancing outcomes are modeled; no stockout, routing, labor, or achieved-service claim.",
      "capabilities": [
        "analytics-to-action",
        "ai-validation",
        "risk-decision"
      ],
      "capability_labels": [
        "Analytics to action",
        "AI and model validation",
        "Risk and decision analysis"
      ],
      "signals": [
        "temporal holdout",
        "simple baseline",
        "fixed capacity",
        "modeled pilot boundary"
      ],
      "figure": "../examples/real-data-cases/figures/01-bike-demand-operations.svg",
      "figure_alt": "Representative evidence figure for Jersey City Bike Demand and Rebalancing Evidence",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/01-bike-demand-operations.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/bike-demand-operations/PROJECT.md"
    },
    {
      "number": "02",
      "id": "cross-city-311-shift",
      "title": "Cross-City 311 Distribution Shift and Transfer Gate",
      "domain": "Urban Analytics",
      "routes": [
        "descriptive",
        "diagnostic",
        "prescriptive"
      ],
      "question": "Are city service-request distributions sufficiently comparable to transfer an analytical rule between Chicago and New York?",
      "result": "The 2023 cross-city total-variation distance is 58.1%, and the transfer gate is refused.",
      "endpoint": "transfer refused",
      "boundary": "Administrative shift audit only; requests are not latent need or service quality.",
      "capabilities": [
        "data-systems-governance",
        "statistical-research",
        "spatial-equity"
      ],
      "capability_labels": [
        "Data systems and governance",
        "Statistical research",
        "Spatial equity and planning"
      ],
      "signals": [
        "ontology audit",
        "distribution shift",
        "transfer refusal",
        "administrative-data boundary"
      ],
      "figure": "../examples/real-data-cases/figures/02-cross-city-311-shift.svg",
      "figure_alt": "Representative evidence figure for Cross-City 311 Distribution Shift and Transfer Gate",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/02-cross-city-311-shift.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/cross-city-311-shift/PROJECT.md"
    },
    {
      "number": "03",
      "id": "bank-marketing-response",
      "title": "Capacity-Constrained Marketing Pilot",
      "domain": "Business Analytics",
      "routes": [
        "descriptive",
        "predictive",
        "prescriptive"
      ],
      "question": "Can pre-contact information concentrate observed responses under a fixed outreach capacity without using post-contact leakage?",
      "result": "The untouched test yields an AUC of 0.650 and a Brier score of 0.210; the top 5% captures 7.4% of observed responses.",
      "endpoint": "randomized pilot required",
      "boundary": "Observed response concentration is not incremental lift, causal treatment effect, profit, or return on outreach.",
      "capabilities": [
        "analytics-to-action",
        "ai-validation",
        "behavior-policy"
      ],
      "capability_labels": [
        "Analytics to action",
        "AI and model validation",
        "Behavior and policy evidence"
      ],
      "signals": [
        "leakage-safe timing",
        "untouched test",
        "capacity capture",
        "randomized pilot requirement"
      ],
      "figure": "../examples/real-data-cases/figures/03-bank-marketing-response.svg",
      "figure_alt": "Representative evidence figure for Capacity-Constrained Marketing Pilot",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/03-bank-marketing-response.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/bank-marketing-response/PROJECT.md"
    },
    {
      "number": "04",
      "id": "census-income-ai",
      "title": "ACS Employment AI Temporal Transport and Audit",
      "domain": "Artificial Intelligence",
      "routes": [
        "descriptive",
        "predictive"
      ],
      "question": "How well does a protected-attribute-excluded employment model developed on 2019 PUMS transport to 2023?",
      "result": "The untouched 2023 temporal test yields an AUC of 0.640 and a weighted Brier score of 0.158.",
      "endpoint": "do not use for consequential action",
      "boundary": "No eligibility, hiring, credit, benefits, or other consequential action.",
      "capabilities": [
        "ai-validation",
        "statistical-research",
        "data-systems-governance"
      ],
      "capability_labels": [
        "AI and model validation",
        "Statistical research",
        "Data systems and governance"
      ],
      "signals": [
        "temporal transport",
        "survey weights",
        "protected-attribute audit",
        "no consequential use"
      ],
      "figure": "../examples/real-data-cases/figures/04-census-income-ai.svg",
      "figure_alt": "Representative evidence figure for ACS Employment AI Temporal Transport and Audit",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/04-census-income-ai.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/census-income-ai/PROJECT.md"
    },
    {
      "number": "05",
      "id": "treasury-risk-engineering",
      "title": "Treasury Curve and Tail-Risk Decision Engine",
      "domain": "Financial Risk Engineering",
      "routes": [
        "descriptive",
        "predictive",
        "prescriptive"
      ],
      "question": "How do duration choices change historical tail loss, backtest behavior, and sensitivity to dependent market shocks?",
      "result": "Historical ES95 loss rises from 0.4% for the short baseline to 0.9% for the long-duration portfolio; the short-baseline rolling VaR exceedance rate is 6.0%.",
      "endpoint": "claim-bounded decision review",
      "boundary": "First-order duration omits convexity, security selection, costs, financing, taxes, liquidity, and future-regime uncertainty.",
      "capabilities": [
        "risk-decision",
        "statistical-research",
        "analytics-to-action"
      ],
      "capability_labels": [
        "Risk and decision analysis",
        "Statistical research",
        "Analytics to action"
      ],
      "signals": [
        "tail loss",
        "coverage backtest",
        "regime comparison",
        "dependent market shocks"
      ],
      "figure": "../examples/real-data-cases/figures/05-treasury-risk-engineering.svg",
      "figure_alt": "Representative evidence figure for Treasury Curve and Tail-Risk Decision Engine",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/05-treasury-risk-engineering.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/treasury-risk-engineering/PROJECT.md"
    },
    {
      "number": "06",
      "id": "cfpb-fintech-complaint-operations",
      "title": "Human-in-the-Loop Complaint Triage Information System",
      "domain": "Financial Technology",
      "routes": [
        "descriptive",
        "predictive"
      ],
      "question": "Does a privacy-minimized complaint model create reliable ranking gain over random review in a later calendar period?",
      "result": "The later-period AUC is 0.611 (block-bootstrap 95% interval 0.539 to 0.697), while top-5% lift is 1.00 (95% interval 0.33 to 2.46); the ranking model fails the deployment gate.",
      "endpoint": "do not deploy",
      "boundary": "The timely flag is not complaint merit, harm, resolution quality, company quality, or compliance; the 2022 model may not transport.",
      "capabilities": [
        "data-systems-governance",
        "ai-validation",
        "analytics-to-action"
      ],
      "capability_labels": [
        "Data systems and governance",
        "AI and model validation",
        "Analytics to action"
      ],
      "signals": [
        "privacy minimization",
        "calendar holdout",
        "human review",
        "do not deploy"
      ],
      "figure": "../examples/real-data-cases/figures/06-cfpb-fintech-complaint-operations.svg",
      "figure_alt": "Representative evidence figure for Human-in-the-Loop Complaint Triage Information System",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/06-cfpb-fintech-complaint-operations.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/cfpb-fintech-complaint-operations/PROJECT.md"
    },
    {
      "number": "07",
      "id": "commercial-real-estate-risk",
      "title": "Commercial Real Estate Diligence Decision Product",
      "domain": "Real-Estate Finance",
      "routes": [
        "descriptive",
        "diagnostic",
        "prescriptive"
      ],
      "question": "Which borough/property-type segments have enough public transaction evidence for property-level diligence, and how do financing-rate assumptions change the income hurdle?",
      "result": "Across 12,399 filtered commercial transactions, Manhattan has the highest borough median price per square foot at $743; the break-even cap rate at 8.5% debt is 7.5%.",
      "endpoint": "claim-bounded decision review",
      "boundary": "The source does not establish arm's-length status, NOI, expenses, occupancy, condition, appraisal value, debt terms, or causal regeneration effects.",
      "capabilities": [
        "analytics-to-action",
        "risk-decision",
        "spatial-equity"
      ],
      "capability_labels": [
        "Analytics to action",
        "Risk and decision analysis",
        "Spatial equity and planning"
      ],
      "signals": [
        "transaction screening",
        "financing sensitivity",
        "diligence workflow",
        "missing property evidence"
      ],
      "figure": "../examples/real-data-cases/figures/07-commercial-real-estate-risk.svg",
      "figure_alt": "Representative evidence figure for Commercial Real Estate Diligence Decision Product",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/07-commercial-real-estate-risk.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/commercial-real-estate-risk/PROJECT.md"
    },
    {
      "number": "08",
      "id": "wildfire-mitigation-under-uncertainty",
      "title": "Wildfire Mitigation Evidence Allocation Under Uncertainty",
      "domain": "Decision Analysis",
      "routes": [
        "descriptive",
        "diagnostic",
        "prescriptive"
      ],
      "question": "Which exposure-weighted evidence-collection allocation is least fragile across historical, recent, and tail-fire scenarios?",
      "result": "Across 8,892 valid mapped perimeters, recent observed acres is the lowest-regret proxy allocation under the tested scenarios.",
      "endpoint": "evidence request before mitigation allocation",
      "boundary": "No fires-prevented or acres-prevented estimate; mitigation action blocked pending effectiveness and feasibility evidence.",
      "capabilities": [
        "risk-decision",
        "behavior-policy",
        "spatial-equity"
      ],
      "capability_labels": [
        "Risk and decision analysis",
        "Behavior and policy evidence",
        "Spatial equity and planning"
      ],
      "signals": [
        "scenario regret",
        "tail exposure",
        "feasibility gap",
        "evidence request"
      ],
      "figure": "../examples/real-data-cases/figures/08-wildfire-mitigation-under-uncertainty.svg",
      "figure_alt": "Representative evidence figure for Wildfire Mitigation Evidence Allocation Under Uncertainty",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/08-wildfire-mitigation-under-uncertainty.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/wildfire-mitigation-under-uncertainty/PROJECT.md"
    },
    {
      "number": "09",
      "id": "sec-nport-filing-review",
      "title": "SEC N-PORT Liquidity and Crowding Filing Review",
      "domain": "Regulatory Filings",
      "routes": [
        "descriptive",
        "diagnostic",
        "predictive",
        "prescriptive"
      ],
      "question": "Which transparent concentration, liquidity, and redemption indicators should trigger targeted filing review?",
      "result": "Across 11,747 reviewed filings, median top-10 holding concentration is 34.5% and the 90th-percentile Level-3 share is 0.2%.",
      "endpoint": "claim-bounded decision review",
      "boundary": "Filing review only; no expected-return, suitability, fund-quality, or investment recommendation.",
      "capabilities": [
        "risk-decision",
        "data-systems-governance",
        "analytics-to-action"
      ],
      "capability_labels": [
        "Risk and decision analysis",
        "Data systems and governance",
        "Analytics to action"
      ],
      "signals": [
        "transparent indicators",
        "review capacity",
        "filing lineage",
        "fiduciary boundary"
      ],
      "figure": "../examples/real-data-cases/figures/09-sec-nport-filing-review.svg",
      "figure_alt": "Representative evidence figure for SEC N-PORT Liquidity and Crowding Filing Review",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/09-sec-nport-filing-review.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/sec-nport-filing-review/PROJECT.md"
    },
    {
      "number": "10",
      "id": "social-norm-field-experiment",
      "title": "Social-Norm Field Experiment with Household-Clustered Inference",
      "domain": "Field Experiments",
      "routes": [
        "descriptive",
        "diagnostic",
        "prescriptive"
      ],
      "question": "What were the intent-to-treat turnout effects of randomized social-pressure mailings after household clustering?",
      "result": "The Neighbors arm has the largest observed intent-to-treat effect at 8.1%, with a household-clustered 95% interval of 7.5% to 8.8%.",
      "endpoint": "observed field effect no new campaign authorization",
      "boundary": "Causal scope is the historical randomized experiment; no new campaign authorization.",
      "capabilities": [
        "behavior-policy",
        "statistical-research"
      ],
      "capability_labels": [
        "Behavior and policy evidence",
        "Statistical research"
      ],
      "signals": [
        "randomized assignment",
        "household clustering",
        "intent-to-treat",
        "no new campaign authorization"
      ],
      "figure": "../examples/real-data-cases/figures/10-social-norm-field-experiment.svg",
      "figure_alt": "Representative evidence figure for Social-Norm Field Experiment with Household-Clustered Inference",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/10-social-norm-field-experiment.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/social-norm-field-experiment/PROJECT.md"
    },
    {
      "number": "11",
      "id": "population-health-survival",
      "title": "Population Health Risk Transport Across NHIS Cohorts",
      "domain": "Population Health",
      "routes": [
        "descriptive",
        "predictive",
        "prescriptive"
      ],
      "question": "Do simple population-risk cells developed in NHIS 2016 retain discrimination and calibration in the 2017 linked-mortality cohort?",
      "result": "The 2017 temporal test yields an AUC of 0.846 and weighted two-year mortality of 2.32% across 58,754 linked adults.",
      "endpoint": "claim-bounded decision review",
      "boundary": "Population-risk validation only; no individual diagnosis, treatment, or clinical deployment.",
      "capabilities": [
        "health-informatics",
        "ai-validation",
        "data-systems-governance"
      ],
      "capability_labels": [
        "Population health and informatics",
        "AI and model validation",
        "Data systems and governance"
      ],
      "signals": [
        "linked cohorts",
        "temporal transport",
        "workload screen",
        "no individual clinical action"
      ],
      "figure": "../examples/real-data-cases/figures/11-population-health-survival.svg",
      "figure_alt": "Representative evidence figure for Population Health Risk Transport Across NHIS Cohorts",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/11-population-health-survival.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/population-health-survival/PROJECT.md"
    },
    {
      "number": "12",
      "id": "opportunity-zone-policy-evaluation",
      "title": "Opportunity Zone One-Year Policy Evidence Screen",
      "domain": "Public Policy",
      "routes": [
        "descriptive",
        "diagnostic",
        "prescriptive"
      ],
      "question": "How did selected tract outcomes change immediately after QOZ designation relative to observed-covariate matches?",
      "result": "The matched one-year screen contains 1,460 complete tract panels, including 138 designated QOZ tracts and 121 unique matched controls.",
      "endpoint": "associational policy screen only",
      "boundary": "Associational one-year screen; no causal effect because parallel trends are unavailable.",
      "capabilities": [
        "behavior-policy",
        "statistical-research",
        "spatial-equity"
      ],
      "capability_labels": [
        "Behavior and policy evidence",
        "Statistical research",
        "Spatial equity and planning"
      ],
      "signals": [
        "matched change",
        "support diagnostics",
        "control reuse",
        "associational policy screen"
      ],
      "figure": "../examples/real-data-cases/figures/12-opportunity-zone-policy-evaluation.svg",
      "figure_alt": "Representative evidence figure for Opportunity Zone One-Year Policy Evidence Screen",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/12-opportunity-zone-policy-evaluation.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/opportunity-zone-policy-evaluation/PROJECT.md"
    },
    {
      "number": "13",
      "id": "behavioral-reading-experiment",
      "title": "Small-Sample Repeated-Measures Inference",
      "domain": "Statistics",
      "routes": [
        "descriptive",
        "diagnostic"
      ],
      "question": "How does passage type change eye-movement burden within the same participant, and how stable is the contrast across reader groups?",
      "result": "Across 57 complete participant pairs, the mean pseudoword-minus-meaningful fixation-duration difference is 34.25 (bootstrap 95% interval 25.87 to 43.35), with a Holm-adjusted sign-flip p-value of 0.0003.",
      "endpoint": "claim-bounded decision review",
      "boundary": "The public sample is small and does not establish downstream educational outcomes or an intervention effect.",
      "capabilities": [
        "statistical-research",
        "behavior-policy"
      ],
      "capability_labels": [
        "Statistical research",
        "Behavior and policy evidence"
      ],
      "signals": [
        "within-participant contrast",
        "small sample",
        "clustered inference",
        "generalization boundary"
      ],
      "figure": "../examples/real-data-cases/figures/13-behavioral-reading-experiment.svg",
      "figure_alt": "Representative evidence figure for Small-Sample Repeated-Measures Inference",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/13-behavioral-reading-experiment.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/behavioral-reading-experiment/PROJECT.md"
    },
    {
      "number": "14",
      "id": "nhanes-population-transportability",
      "title": "NHANES Mortality Transportability and Population Inequality",
      "domain": "Biostatistics",
      "routes": [
        "descriptive",
        "diagnostic",
        "prescriptive"
      ],
      "question": "Do population mortality risk patterns transport between NHANES cohorts, and what inequality gradient remains visible?",
      "result": "The external-cohort check yields an AUC of 0.804 and a Brier score of 0.022 across 11,820 linked adults.",
      "endpoint": "population research only",
      "boundary": "Population research only; no individual diagnosis or treatment.",
      "capabilities": [
        "health-informatics",
        "statistical-research",
        "ai-validation"
      ],
      "capability_labels": [
        "Population health and informatics",
        "Statistical research",
        "AI and model validation"
      ],
      "signals": [
        "survey weights",
        "external cohort check",
        "calibration",
        "population inequality"
      ],
      "figure": "../examples/real-data-cases/figures/14-nhanes-population-transportability.svg",
      "figure_alt": "Representative evidence figure for NHANES Mortality Transportability and Population Inequality",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/14-nhanes-population-transportability.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/nhanes-population-transportability/PROJECT.md"
    },
    {
      "number": "15",
      "id": "spatial-equity-planning",
      "title": "Spatial Equity Planning with Transit and Site-Evidence Gates",
      "domain": "Urban Planning",
      "routes": [
        "descriptive",
        "prescriptive"
      ],
      "question": "Which tract-level service-hub priorities merit local review after observed rapid-transit proximity is added?",
      "result": "Across 1,597 analyzed tracts and 265 rapid-transit stop records, the high-poverty weighted nearest-stop distance is 40.65 km.",
      "endpoint": "claim-bounded decision review",
      "boundary": "No site recommendation until parcel, zoning, network, cost, and community evidence is supplied.",
      "capabilities": [
        "spatial-equity",
        "behavior-policy",
        "analytics-to-action"
      ],
      "capability_labels": [
        "Spatial equity and planning",
        "Behavior and policy evidence",
        "Analytics to action"
      ],
      "signals": [
        "complete-case route",
        "missingness sensitivity",
        "observed transit proximity",
        "site evidence gate"
      ],
      "figure": "../examples/real-data-cases/figures/15-spatial-equity-planning.svg",
      "figure_alt": "Representative evidence figure for Spatial Equity Planning with Transit and Site-Evidence Gates",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/15-spatial-equity-planning.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/spatial-equity-planning/PROJECT.md"
    },
    {
      "number": "16",
      "id": "blood-pressure-protocol-bridge",
      "title": "When a Blood Pressure Survey Changes Its Measurement Protocol",
      "domain": "Population Health Surveillance",
      "routes": [
        "descriptive",
        "diagnostic"
      ],
      "question": "How much does replacing a blood-pressure measurement protocol change a survey threshold count?",
      "result": "Across 4,614 paired adults, the survey-weighted automatic-minus-manual mean was -1.50 mmHg. At 130 mmHg, 5.32% moved above and 8.15% moved below the cutoff.",
      "endpoint": "measurement protocol review",
      "boundary": "The device and examiner change together. Weighted results describe adults with paired examination records; threshold crossings are survey classifications, not new clinical diagnoses.",
      "capabilities": [
        "health-informatics",
        "statistical-research",
        "risk-decision"
      ],
      "capability_labels": [
        "Population health and informatics",
        "Statistical research",
        "Risk and decision analysis"
      ],
      "signals": [
        "paired protocol crossover",
        "stratified PSU linearization",
        "directional threshold crossings",
        "leave-PSU-out agreement"
      ],
      "figure": "../examples/real-data-cases/figures/16-blood-pressure-protocol-bridge.svg",
      "figure_alt": "Representative evidence figure for When a Blood Pressure Survey Changes Its Measurement Protocol",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/16-blood-pressure-protocol-bridge.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/blood-pressure-protocol-bridge/PROJECT.md"
    },
    {
      "number": "17",
      "id": "wearable-heart-rate-abstention",
      "title": "When Should a Wrist Monitor Withhold a Heart Rate Reading?",
      "domain": "Wearable Biomedical Informatics",
      "routes": [
        "diagnostic",
        "predictive"
      ],
      "question": "When can a wrist monitor's quality gate reduce error without leaving users without readings for too long?",
      "result": "With the DaLiA threshold frozen, WESAD retained 85.2% of 5,544 eligible windows. Subject-averaged absolute error among reported ECG-readable windows was 6.83 bpm.",
      "endpoint": "selective measurement review",
      "boundary": "The ECG reference is algorithm-derived. The external cohort changes the activity setting; both studies use Empatica wrist hardware. Reported accuracy applies only to the activity and ECG eligibility definitions.",
      "capabilities": [
        "health-informatics",
        "ai-validation",
        "statistical-research"
      ],
      "capability_labels": [
        "Population health and informatics",
        "AI and model validation",
        "Statistical research"
      ],
      "signals": [
        "frozen external acceptance rule",
        "paired ECG reference",
        "risk by activity",
        "uninterrupted readout gaps"
      ],
      "figure": "../examples/real-data-cases/figures/17-wearable-heart-rate-abstention.svg",
      "figure_alt": "Representative evidence figure for When Should a Wrist Monitor Withhold a Heart Rate Reading?",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/17-wearable-heart-rate-abstention.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/wearable-heart-rate-abstention/PROJECT.md"
    },
    {
      "number": "18",
      "id": "call-centre-flexible-dispatch",
      "title": "When Should a Call Centre Reallocate Staff After a Demand Shock?",
      "domain": "Systems Engineering",
      "routes": [
        "diagnostic",
        "predictive",
        "prescriptive"
      ],
      "question": "When, within a fixed staffing budget, should a manager release temporary service capacity?",
      "result": "Across 65 held-out mornings, mean simulated abandonment was 17.23% with a fixed reserve and 18.48% under receding-horizon dispatch. Observed abandonment averaged 13.91%.",
      "endpoint": "staffing policy review",
      "boundary": "Historical outcomes describe observed calls. Staffing schedules, patience past the censoring point, operator flexibility and policy-dependent waits are simulated. The five-hour morning replay begins with an empty queue.",
      "capabilities": [
        "analytics-to-action",
        "risk-decision",
        "statistical-research"
      ],
      "capability_labels": [
        "Analytics to action",
        "Risk and decision analysis",
        "Statistical research"
      ],
      "signals": [
        "censored patience distribution",
        "held-out staffing calibration",
        "matched reserve hours",
        "switching cost"
      ],
      "figure": "../examples/real-data-cases/figures/18-call-centre-flexible-dispatch.svg",
      "figure_alt": "Representative evidence figure for When Should a Call Centre Reallocate Staff After a Demand Shock?",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/18-call-centre-flexible-dispatch.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/call-centre-flexible-dispatch/PROJECT.md"
    },
    {
      "number": "19",
      "id": "unemployment-claims-release-revisions",
      "title": "Which State Unemployment Claims Alerts Survive the Next Release?",
      "domain": "Applied Machine Learning",
      "routes": [
        "diagnostic",
        "predictive"
      ],
      "question": "Which state-level claims alerts survive the switch from first publication to claimant-residence reporting?",
      "result": "Across 68 held-out weekly releases at 5 review slots, 83.2% of first-release alerts and 89.7% of revision-adjusted alerts appeared in the next release's residence-based list.",
      "endpoint": "vintage sensitive alerting",
      "boundary": "The advance column is reported by liable state and includes a workshare proxy. The next release uses state of residence. The ranked target is a later published measure, not a directly observed employment shock.",
      "capabilities": [
        "ai-validation",
        "data-systems-governance",
        "statistical-research"
      ],
      "capability_labels": [
        "AI and model validation",
        "Data systems and governance",
        "Statistical research"
      ],
      "signals": [
        "advance and residence-based vintages",
        "publication as-of join",
        "statewise partial pooling",
        "fixed alert capacity"
      ],
      "figure": "../examples/real-data-cases/figures/19-unemployment-claims-release-revisions.svg",
      "figure_alt": "Representative evidence figure for Which State Unemployment Claims Alerts Survive the Next Release?",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/19-unemployment-claims-release-revisions.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/unemployment-claims-release-revisions/PROJECT.md"
    },
    {
      "number": "20",
      "id": "transit-timetable-repair",
      "title": "Maintaining Earliest Arrival Routes Across Timetable Revisions",
      "domain": "Computer Science Algorithms",
      "routes": [
        "diagnostic",
        "prescriptive"
      ],
      "question": "Can a router repair a revised timetable and still return exactly the same earliest arrivals as rebuilding?",
      "result": "Across 10 timetable versions, all 300 route-query results matched a full scan. Revisions changed 4,223 destination arrival labels; checkpoint repair visited 1,969,278 connections versus 8,903,454 for full recomputation.",
      "endpoint": "routing update review",
      "boundary": "The archive assigns each download a non-overlapping archive interval. This is a comparison of overlapping planned calendar service inside those files. Results concern scheduled travel in a selected network, with a stated same-station transfer buffer and no street-walking links.",
      "capabilities": [
        "data-systems-governance",
        "spatial-equity",
        "analytics-to-action"
      ],
      "capability_labels": [
        "Data systems and governance",
        "Spatial equity and planning",
        "Analytics to action"
      ],
      "signals": [
        "exact timetable oracle",
        "query checkpoints",
        "off-path added connection",
        "transfer-aware replay"
      ],
      "figure": "../examples/real-data-cases/figures/20-transit-timetable-repair.svg",
      "figure_alt": "Representative evidence figure for Maintaining Earliest Arrival Routes Across Timetable Revisions",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/20-transit-timetable-repair.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/transit-timetable-repair/PROJECT.md"
    },
    {
      "number": "21",
      "id": "online-edit-review-capacity",
      "title": "The Last Review Slot in an Online Queue",
      "domain": "Operations Research",
      "routes": [
        "predictive",
        "prescriptive"
      ],
      "question": "When should an online reviewer spend the last daily slot on the current edit?",
      "result": "Across 366 held-out publication days, the inventory-value policy captured 308 seven-day identity reverts, versus 287 with a fixed threshold and 1095 for an outcome-aware upper bound.",
      "endpoint": "finite inventory policy",
      "boundary": "An identity revert indicates that previously observed page content returned within seven days. It is a behavioral proxy. The replay assumes no effect of the simulated review on subsequent edits.",
      "capabilities": [
        "risk-decision",
        "analytics-to-action",
        "ai-validation"
      ],
      "capability_labels": [
        "Risk and decision analysis",
        "Analytics to action",
        "AI and model validation"
      ],
      "signals": [
        "finite-horizon slot value",
        "expiring daily inventory",
        "score-only oracle",
        "realized-event oracle"
      ],
      "figure": "../examples/real-data-cases/figures/21-online-edit-review-capacity.svg",
      "figure_alt": "Representative evidence figure for The Last Review Slot in an Online Queue",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/21-online-edit-review-capacity.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/online-edit-review-capacity/PROJECT.md"
    },
    {
      "number": "22",
      "id": "marketplace-delivery-intervention",
      "title": "Where Should a Marketplace Spend Its Delivery Improvement Budget?",
      "domain": "Business Analytics",
      "routes": [
        "diagnostic",
        "prescriptive"
      ],
      "question": "Should a marketplace direct an equal number of review slots to seller handoffs or to post-handoff delivery?",
      "result": "Across 4 future quarters and 2,000 equal review slots per policy, adjusted seller targeting found 86 late deliveries following a missed handoff deadline. Carrier-focused targeting found 225 late deliveries after on-time handoff.",
      "endpoint": "intervention budget review",
      "boundary": "An on-time handoff followed by a late delivery locates delay in the observed sequence. It does not establish fault or show that an intervention prevented lateness.",
      "capabilities": [
        "analytics-to-action",
        "risk-decision",
        "statistical-research"
      ],
      "capability_labels": [
        "Analytics to action",
        "Risk and decision analysis",
        "Statistical research"
      ],
      "signals": [
        "handoff vs last-mile delay",
        "product and geography adjustment",
        "matured quarterly evaluations",
        "cost–effectiveness crossover"
      ],
      "figure": "../examples/real-data-cases/figures/22-marketplace-delivery-intervention.svg",
      "figure_alt": "Representative evidence figure for Where Should a Marketplace Spend Its Delivery Improvement Budget?",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/22-marketplace-delivery-intervention.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/marketplace-delivery-intervention/PROJECT.md"
    },
    {
      "number": "23",
      "id": "drive-failure-policy-fallback",
      "title": "Knowing When to Fall Back After a Drive Fleet Changes",
      "domain": "Machine Learning Engineering",
      "routes": [
        "predictive",
        "prescriptive"
      ],
      "question": "When monitoring signals disappear after a fleet change, is switching to an interpretable rule worth the lost warnings?",
      "result": "With 15 daily review slots across 139 held-out dates, event recall was 21.8% for the pending-sector rule and 9.8% for monitored fallback across 459 observable failures.",
      "endpoint": "reliability handoff",
      "boundary": "A recorded hardware failure is a proxy for replacement need. A late and an absent failure are distinguishable only while the drive remains observed. Alternative dispatch rules are replayed on logged outcomes.",
      "capabilities": [
        "ai-validation",
        "data-systems-governance",
        "risk-decision"
      ],
      "capability_labels": [
        "AI and model validation",
        "Data systems and governance",
        "Risk and decision analysis"
      ],
      "signals": [
        "serial and hardware-family holdout",
        "right-censored device days",
        "episode-level false alerts",
        "delayed-label fallback"
      ],
      "figure": "../examples/real-data-cases/figures/23-drive-failure-policy-fallback.svg",
      "figure_alt": "Representative evidence figure for Knowing When to Fall Back After a Drive Fleet Changes",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/23-drive-failure-policy-fallback.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/drive-failure-policy-fallback/PROJECT.md"
    },
    {
      "number": "24",
      "id": "last-mile-departure-slack",
      "title": "How Much Departure Delay Can a Last-Mile Route Absorb?",
      "domain": "Freight Transportation",
      "routes": [
        "diagnostic",
        "prescriptive"
      ],
      "question": "How late can a dispatcher release a route while still honoring its published windows and a stated end of shift?",
      "result": "On 24 complete published routes, window-focused relocation produced 10 nonnegative departure-delay witnesses; the recorded sequences produced 10. 14 routes remained inconclusive under the search budget.",
      "endpoint": "dispatch feasibility review",
      "boundary": "Package time windows and driver sequences are observed. Travel times are a provided static matrix, service durations are planned, and the depot-return deadline is an eight-hour scenario. Unsolved routes remain undetermined.",
      "capabilities": [
        "risk-decision",
        "analytics-to-action",
        "spatial-equity"
      ],
      "capability_labels": [
        "Risk and decision analysis",
        "Analytics to action",
        "Spatial equity and planning"
      ],
      "signals": [
        "package time windows",
        "verified departure witnesses",
        "independent upper bounds",
        "depot holdout"
      ],
      "figure": "../examples/real-data-cases/figures/24-last-mile-departure-slack.svg",
      "figure_alt": "Representative evidence figure for How Much Departure Delay Can a Last-Mile Route Absorb?",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/24-last-mile-departure-slack.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/last-mile-departure-slack/PROJECT.md"
    },
    {
      "number": "25",
      "id": "food-inspection-exploration",
      "title": "How Much Inspection Capacity Should a City Reserve for Random Audits?",
      "domain": "Technology Policy",
      "routes": [
        "diagnostic",
        "prescriptive"
      ],
      "question": "How much of a city's finite inspection capacity should be reserved for random exploration?",
      "result": "The 25% exploration policy allocated 960 slots over 8 quarters. Historical results were observable for 197 selections, giving full-roster critical-finding bounds of 4.9% to 84.4%.",
      "endpoint": "inspection audit design",
      "boundary": "In the archival data only inspected restaurants reveal violations. The roster requires a known prior restaurant classification; never-classified premises are outside the target. Later inspections do not identify the causal effect of scheduling earlier.",
      "capabilities": [
        "behavior-policy",
        "statistical-research",
        "analytics-to-action"
      ],
      "capability_labels": [
        "Behavior and policy evidence",
        "Statistical research",
        "Analytics to action"
      ],
      "signals": [
        "licensed eligibility roster",
        "selective outcomes",
        "stratified exploration",
        "design probabilities"
      ],
      "figure": "../examples/real-data-cases/figures/25-food-inspection-exploration.svg",
      "figure_alt": "Representative evidence figure for How Much Inspection Capacity Should a City Reserve for Random Audits?",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/25-food-inspection-exploration.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/food-inspection-exploration/PROJECT.md"
    },
    {
      "number": "26",
      "id": "programming-hint-design",
      "title": "Counterexamples or Direct Corrections for Novice Programmers?",
      "domain": "Learning Design",
      "routes": [
        "diagnostic",
        "predictive"
      ],
      "question": "Should a beginner receive an elicited counterexample or a direct correction after a repeatable misconception?",
      "result": "The authors' public file contained 729 learner–problem records. On 584 matched out-of-time learner-held-out observations, first-correct F1 was 0.676 for the past-only model. In the independent code archive, 27 incorrect programs removed from the list being traversed.",
      "endpoint": "prospective experiment",
      "boundary": "The public CSEDM example describes a subset of the 89-learner, 38-task source cohort. It contains aggregated learner/problem outcomes. Actual code examples are from the independent Refactory study. No newly delivered hint or transfer improvement is attributed to either cohort.",
      "capabilities": [
        "behavior-policy",
        "ai-validation",
        "statistical-research"
      ],
      "capability_labels": [
        "Behavior and policy evidence",
        "AI and model validation",
        "Statistical research"
      ],
      "signals": [
        "learner-held-out prediction",
        "observed misconception",
        "two runnable feedback designs",
        "independently scored transfer"
      ],
      "figure": "../examples/real-data-cases/figures/26-programming-hint-design.svg",
      "figure_alt": "Representative evidence figure for Counterexamples or Direct Corrections for Novice Programmers?",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/26-programming-hint-design.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/programming-hint-design/PROJECT.md"
    },
    {
      "number": "27",
      "id": "credit-drawdown-rates-hedge",
      "title": "Cut Credit Exposure or Hedge Rates During a Corporate Bond Drawdown?",
      "domain": "Investment Risk",
      "routes": [
        "diagnostic",
        "prescriptive"
      ],
      "question": "During a credit drawdown, how does reducing corporate exposure compare with matching its expected rate sensitivity using a Treasury hedge?",
      "result": "Over 1097 held-out weeks, the rule triggered 143 times. The modeled net maximum drawdown was -17.02% after cutting credit and -19.21% under the matched-rate hedge.",
      "endpoint": "investment risk review",
      "boundary": "A backtest using fund NAVs is a modeled portfolio. Shorting and funding spreads beyond the stated transaction cost can change the comparison. The non-rate residual includes liquidity and issuer-specific risk.",
      "capabilities": [
        "risk-decision",
        "statistical-research",
        "analytics-to-action"
      ],
      "capability_labels": [
        "Risk and decision analysis",
        "Statistical research",
        "Analytics to action"
      ],
      "signals": [
        "lagged Treasury beta match",
        "self-financing overlay",
        "distribution-adjusted NAV",
        "turnover break-even"
      ],
      "figure": "../examples/real-data-cases/figures/27-credit-drawdown-rates-hedge.svg",
      "figure_alt": "Representative evidence figure for Cut Credit Exposure or Hedge Rates During a Corporate Bond Drawdown?",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/27-credit-drawdown-rates-hedge.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/credit-drawdown-rates-hedge/PROJECT.md"
    },
    {
      "number": "28",
      "id": "overlapping-forecast-comparisons",
      "title": "How Reliable Are Model Comparisons With Overlapping Evaluation Windows?",
      "domain": "Applied Statistics",
      "routes": [
        "diagnostic",
        "predictive"
      ],
      "question": "How wide should a forecast-comparison interval be when adjacent scores reuse six days of observations?",
      "result": "Across 1,520 shared dates after the source-quality screen and 6 balancing authorities, the day-ahead minus seasonal-naive score averaged -5.14 percentage points. The 95% HAC interval spanned 0.943 points versus 0.304 under independence.",
      "endpoint": "dependence aware comparison",
      "boundary": "The public extract contains historical reported observations, including revisions. Known-truth coverage is a simulation estimate with Monte Carlo uncertainty. Estimates concern the six reported balancing areas.",
      "capabilities": [
        "statistical-research",
        "ai-validation",
        "risk-decision"
      ],
      "capability_labels": [
        "Statistical research",
        "AI and model validation",
        "Risk and decision analysis"
      ],
      "signals": [
        "paired calendar dates",
        "overlapping forecast losses",
        "HAC and moving blocks",
        "known-truth coverage"
      ],
      "figure": "../examples/real-data-cases/figures/28-overlapping-forecast-comparisons.svg",
      "figure_alt": "Representative evidence figure for How Reliable Are Model Comparisons With Overlapping Evaluation Windows?",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/28-overlapping-forecast-comparisons.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/overlapping-forecast-comparisons/PROJECT.md"
    },
    {
      "number": "29",
      "id": "earnings-cash-collection",
      "title": "When Reported Earnings Outrun Cash Collections",
      "domain": "Fundamental Analysis",
      "routes": [
        "diagnostic",
        "predictive"
      ],
      "question": "When earnings outrun collections, do receivables and inventory changes improve next-year cash-flow forecasts?",
      "result": "Across 89 out-of-time company-year forecasts, next-year operating-cash-flow MAE was 3.08% of opening assets for cash persistence and 3.07% for the accrual model.",
      "endpoint": "valuation review",
      "boundary": "Predictive associations in a selected panel do not establish manipulation or causality. Vendor non-trade receivables are distinct from customer trade balances. Scenario valuations depend on payout, opening book, abnormal-return persistence and cost of equity.",
      "capabilities": [
        "risk-decision",
        "data-systems-governance",
        "statistical-research"
      ],
      "capability_labels": [
        "Risk and decision analysis",
        "Data systems and governance",
        "Statistical research"
      ],
      "signals": [
        "as-filed accessions",
        "mature competing forecasts",
        "issuer footnote",
        "cash-collection valuation sensitivity"
      ],
      "figure": "../examples/real-data-cases/figures/29-earnings-cash-collection.svg",
      "figure_alt": "Representative evidence figure for When Reported Earnings Outrun Cash Collections",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/29-earnings-cash-collection.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/earnings-cash-collection/PROJECT.md"
    },
    {
      "number": "30",
      "id": "versioned-road-geometry",
      "title": "Consistent Road Geometry During Interrupted Map Updates",
      "domain": "Computer Systems",
      "routes": [
        "diagnostic",
        "prescriptive"
      ],
      "question": "Can an interrupted map update publish mutually consistent node positions and road geometry?",
      "result": "Across 29 consecutive real map releases, dependency-aware repair matched every full rebuild and the next independent snapshot (3,655 highway geometries). Updating only revised ways missed 1 geometry-version discrepancy.",
      "endpoint": "transactional release",
      "boundary": "This is a reproducible experiment on a single regional OSM extract and a local SQLite store. Work counts measure recomputation. System latency and production availability require separate measurement.",
      "capabilities": [
        "data-systems-governance",
        "ai-validation",
        "spatial-equity"
      ],
      "capability_labels": [
        "Data systems and governance",
        "AI and model validation",
        "Spatial equity and planning"
      ],
      "signals": [
        "node-to-road reverse dependencies",
        "SQLite WAL snapshot",
        "replay after rollback",
        "independent source oracle"
      ],
      "figure": "../examples/real-data-cases/figures/30-versioned-road-geometry.svg",
      "figure_alt": "Representative evidence figure for Consistent Road Geometry During Interrupted Map Updates",
      "case_card": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/cases/30-versioned-road-geometry.md",
      "project": "https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/blob/main/examples/real-data-cases/projects/versioned-road-geometry/PROJECT.md"
    }
  ]
};
