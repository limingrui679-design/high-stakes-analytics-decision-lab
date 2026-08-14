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
make verify
make quality
```

The Make targets are convenience entry points, not a second build system. The
equivalent direct commands and the CI matrix are documented in
[`docs/verification.md`](docs/verification.md).

## Documentation structure

- Keep `README.md` focused on product value, the shortest useful path, the
  portfolio, and public verification.
- Put onboarding, architecture, repository orientation, and maintainer
  procedures in `docs/`.
- Treat `references/` as the executable Skill contract library. Changes there
  can alter runtime behavior and require corresponding tests.
- Keep `SKILL.md` at the repository root so Agent Skills-compatible runtimes
  can discover it.

See [`docs/repository-layout.md`](docs/repository-layout.md) for the complete
canonical-versus-generated file map.

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
make visuals
```

If a source manifest or raw-source lock changes, rerun the affected project's
download, preparation, analysis, and decision-case commands before running the
full test suite. Generated case cards, galleries, reports, figures, manifests,
and receipts should never be edited as isolated copies.

The portfolio verifier rebuilds all fifteen projects in a temporary copy. It
requires exact agreement for sources, strings, labels, counts, and documented
hashes; it permits only bounded cross-version floating-point differences and
their derived artifact receipts. See
[`references/reproducibility-contract.md`](references/reproducibility-contract.md).

Documentation-only changes must still pass the local-link, package-integrity,
and spelling checks. A visual change must begin in the canonical generator or
shared visual helper; do not hand-edit generated SVGs, galleries, reports, or
case cards.

## Pull requests

Keep changes focused. Explain the decision or evidence problem being solved,
list generated artifacts, report exact verification commands, and identify any
claim-boundary or source-license implications. If a change is unreleased, add
it under `Unreleased` in [`CHANGELOG.md`](CHANGELOG.md); do not rewrite the
manifest of an already tagged release.
