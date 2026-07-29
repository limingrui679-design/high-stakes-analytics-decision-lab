# Real-Evidence Workflow

Use this workflow whenever the output will be presented as an empirical project.

## 1. Source selection

Prefer, in order:

1. official statistical, regulatory, administrative, or market data;
2. an academic repository with a persistent identifier and explicit license;
3. an authoritative open dataset with documented provenance.

Reject a source when its license is unknown, redistribution is prohibited, the
version cannot be fixed, or the available fields cannot answer the question
without inventing essential variables.

## 2. Source manifest

Create `source-manifest.json` before analysis. Record:

- stable project and source identifiers;
- title, publisher, landing page, download endpoint, DOI when available;
- version or closed extraction window and access date;
- license, license URL, redistribution rule, and citation;
- expected rows, grain, raw file paths, and SHA-256 hashes;
- privacy review, sensitive fields, intended treatment, and permitted output.

The manifest describes the evidence that exists. It must not claim that a
publisher approves the analysis.

## 3. Reproducible acquisition

`download_data.py` should verify a committed snapshot by default. Network
refresh must be explicit. A `download-receipt.json` records whether each file
was reused or refreshed and whether its hash matched.

If the source contains personal text or direct identifiers, minimize it before
repository storage. Record dropped fields and the sanitized-file hash in a
privacy receipt.

## 4. Prepared-data contract

For user-uploaded data, run `scripts/profile_dataset.py` before source-specific
preparation and follow
[data-quality-gate.md](data-quality-gate.md). `prepare_data.py` or
`scripts/prepare_dataset.py` then produces:

- one documented analysis table;
- a data dictionary;
- row and column counts;
- missingness by field;
- duplicate-key checks;
- range, category, and temporal-order checks appropriate to the source;
- a quality status and documented limitations.

Safe normalization, substantive cleaning, and manual review must remain
separate. Never silently impute, deduplicate, delete outliers, drop fields, or
recode. Preserve the original file, cleaning plan, approvals,
`transformation-log.json`, and the complete post-cleaning quality gate.

## 5. Analysis boundary

Define before modeling:

- research question, target population, unit of analysis, horizon, and estimand;
- inclusion and exclusion rules;
- decision-time information set;
- train, validation, and test boundaries;
- primary outcome and planned secondary analyses;
- claims the design can and cannot support.

## 6. Public project outputs

Each real project should contain:

```text
PROJECT.md
source-manifest.json
config.json
download_data.py
prepare_data.py
analyze.py
build_decision_case.py
data/download-receipt.json
data/quality-report.json
outputs/results.json
outputs/report.md
outputs/figures/*.svg
```

Add models, predictions, lineage tables, privacy receipts, or decision outputs
when relevant. Synthetic fixtures belong only under `tests/fixtures/`.
