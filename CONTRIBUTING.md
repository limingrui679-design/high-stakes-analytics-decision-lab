# Contributing

Thank you for helping improve High-Stakes Analytics & Decision Lab. Changes are
welcome when they preserve the repository's central contract: every conclusion
must remain traceable to source data, code, validation, and an explicit claim
boundary.

## Development baseline

- Use Python 3.11 or newer.
- Keep runtime paths standard-library only unless a dependency is essential and
  documented.
- Install the pinned quality tools with
  `python3 -m pip install -r requirements-dev.txt`.
- Install `requirements-maintenance.txt` only when rebuilding external source
  snapshots that require pandas.

Before opening a pull request, run:

```bash
python3 -m unittest discover -s tests -v
ruff check scripts tests
mypy scripts
```

## Evidence and claim rules

- Do not present synthetic fixtures, modeled scenarios, proposed metrics, or
  private previews as observed real-world outcomes.
- Preserve the distinction between individual and team work, prototype and
  deployment, and validation evidence and a future plan.
- Keep dataset licenses, access dates, hashes, row counts, and redistribution
  boundaries visible.
- Never remove a limitation merely to strengthen a result.
- Quantitative summary text must be supported by the project's machine-readable
  results or report.

## Generated artifacts

Edit canonical scripts or source metadata first, then regenerate their outputs.
The principal commands are:

```bash
python3 scripts/configure_tailored_portfolio.py
python3 scripts/build_readme_visuals.py
python3 scripts/build_terminal_decision_reports.py
python3 scripts/build_case_examples.py
```

If a source manifest or raw-source lock changes, rerun the affected project's
download, preparation, analysis, and decision-case commands before running the
full test suite. Generated case cards, galleries, reports, figures, manifests,
and receipts should never be edited as isolated copies.

## Pull requests

Keep changes focused. Explain the decision or evidence problem being solved,
list generated artifacts, report exact verification commands, and identify any
claim-boundary or source-license implications.
