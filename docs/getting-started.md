# Getting Started

This guide covers the shortest supported paths from installation to a
reviewable evidence product. High-Stakes Analytics & Decision Lab can be used
as an Agent Skill or directly from a repository checkout.

## Requirements

- Python 3.11 or newer for direct repository commands.
- An Agent Skills-compatible runtime for named Skill invocation.
- A real, permitted source for empirical analysis. The bundled portfolio can
  be used as a method precedent, but saved empirical results must not be copied
  into a new decision.

## Install as an Agent Skill

Install globally across detected compatible runtimes:

```bash
npx skills add limingrui679-design/high-stakes-analytics-decision-lab -g
```

Target Codex explicitly:

```bash
npx skills add limingrui679-design/high-stakes-analytics-decision-lab -g -a codex -y
```

Inspect the exposed Skill before installing:

```bash
npx skills add limingrui679-design/high-stakes-analytics-decision-lab --list
```

Generate a temporary prompt without installing:

```bash
npx skills use limingrui679-design/high-stakes-analytics-decision-lab@high-stakes-analytics-decision-lab
```

## Ask for the right outcome

After installation, start with the decision or evidence question rather than a
preferred model.

```text
$high-stakes-analytics-decision-lab
Run the data-readiness gate on this source, preserve the original file, and
select only the analytical routes the evidence supports. Produce an Evidence
Intelligence Report. Add a Decision Intelligence Brief only if the evidence
and decision context justify one.
```

Valid outcomes include a bounded action, a pilot requirement, targeted
diligence, an evidence request, negative validation, or `do_not_deploy`.

## Start from a question

When no row-level data are available, generate an analysis blueprint instead
of inventing results:

```bash
python3 scripts/route_question.py \
  "How should limited review capacity be allocated?" \
  --scope full \
  --output-dir /absolute/path/to/blueprint
```

The blueprint defines the question, routes, required evidence, methods,
validity checks, handoffs, and an accessible lifecycle figure.

## Start from a question and data

Initialize a reviewable workspace:

```bash
python3 scripts/init_case.py /absolute/path/to/input.csv \
  --question "Which customers are likely to respond next month?" \
  --output-dir /absolute/path/to/customer-response-workspace
```

The initializer preserves and hash-checks the source, drafts a contract,
profiles quality, routes the question, and records unresolved decisions. It
does not clean data, fit a model, or generate a recommendation.

To run the gate separately, complete
[`assets/data-contract-template.json`](../assets/data-contract-template.json)
and run:

```bash
python3 scripts/profile_dataset.py /absolute/path/to/input.csv \
  --contract /absolute/path/to/data-contract.json \
  --output-dir /absolute/path/to/readiness
```

For XLSX, Parquet, database, or multi-table inputs, preserve and hash the
original source and create a traceable tabular extract with a conversion
receipt, declared relationships, join checks, and separate hashes.

## Prepare data only after review

Safe normalization may run automatically. Deletion, imputation, outlier
treatment, category merging, unit conversion, target correction, and grain
changes require approval by action ID.

```bash
python3 scripts/prepare_dataset.py /absolute/path/to/input.csv \
  --quality-report /absolute/path/to/readiness/data-quality-report.json \
  --cleaning-plan /absolute/path/to/readiness/cleaning-plan.json \
  --approve clean-003 \
  --output-dir /absolute/path/to/prepared
```

The processed copy never overwrites the source. A complete post-cleaning gate
must still permit the intended route.

## Validate and run a decision case

```bash
python3 scripts/validate_case.py /absolute/path/to/case.json

python3 scripts/run_case.py /absolute/path/to/case.json \
  --output-dir /absolute/path/to/output \
  --samples 10000 \
  --seed 20260726
```

The engine reports expected and tail performance, feasibility, shared-shock
stress, sensitivity, provenance coverage, group impacts, and reversal
conditions. Numerical stability never upgrades the permitted use of weak
evidence.

## Know the output contract

Data readiness produces a quality report, machine-readable findings, a data
contract, a dry-run cleaning plan, and an accessible overview figure.

A complete evidence project produces:

```text
report.md                    # primary Evidence Intelligence Report
results.json                 # machine-readable analytical result
chart-map.json               # figure-to-question and source contract
figures/*.svg                # every material analytical visual
```

A justified decision layer additionally produces:

```text
decision-report.md
decision-results.json
figures/chart-map.json
figures/*.svg
```

Continue with [Architecture](architecture.md) for the system design or open the
[fifteen-project portfolio](../examples/real-data-cases/README.md) for worked
precedents.

