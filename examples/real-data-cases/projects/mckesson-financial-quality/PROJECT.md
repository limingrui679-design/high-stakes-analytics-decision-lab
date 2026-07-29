# R6B · SEC Peer Financial Quality and Cash Conversion

**Skill coverage:** financial-statement analysis, accounting data engineering, peer benchmarking, and scenario diagnostics  
**Decision boundary:** identify diligence priorities from reported statements—not issue an investment recommendation, valuation, or assurance opinion.

## Analytical question

How do profitability, cash conversion, and working-capital intensity differ across three public drug distributors over a common eight-year fiscal window, and which apparent gaps warrant filing-level follow-up?

## Evidence and methods

- Official SEC XBRL Companyfacts snapshots for McKesson, Cardinal Health, and Cencora.
- A 24-observation company-year panel with entity-specific fiscal ends and accession-level lineage.
- Common-size margins, cash-earnings quality, free-cash-flow proxy, and working-capital-cycle decomposition.
- Fiscal-year peer ranks, median gaps, dispersion, persistence, and margin stress with explicit comparison limits.

## Reproduce

```bash
python3 download_data.py
python3 prepare_data.py
python3 analyze.py
python3 build_decision_case.py
```

Read the [technical report](outputs/report.md), [machine-readable results](outputs/results.json), and [fact-lineage table](outputs/fact-lineage.csv).

## Transferable methods

The case demonstrates how to reconcile filing facts before comparing firms, how to distinguish scale from common-size economics, and how to turn a peer gap into a bounded diligence question rather than an investment conclusion.

## Non-negotiable limitation

XBRL standardization and a shared SIC code do not remove accounting-judgment, taxonomy, restatement, fiscal-calendar, segment, acquisition, or business-mix risk. The project does not reproduce the full footnotes or management discussion.
