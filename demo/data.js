window.HSADL_DEMO = {
  "schema_version": "1.0",
  "school_neutral": true,
  "boundary": "Public-data research portfolio; no production deployment, institutional adoption, external review, or achieved real-world impact is implied.",
  "metrics": {
    "cases": 15,
    "routes": 4,
    "capabilities": 8,
    "accessible_figures": 119
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
    }
  ]
};
