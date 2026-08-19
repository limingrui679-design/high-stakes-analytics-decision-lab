# Verification

The repository treats tests, portfolio reproduction, source identity, release
identity, and empirical validity as separate checks. Passing one layer does not
silently imply another.

## Fast path

Run the complete standalone test suite and rebuild all fifteen projects:

```bash
make verify
```

The equivalent direct commands are:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify_portfolio_reproducibility.py
```

## Verification layers

| Layer | What is checked | What it does not prove |
|---|---|---|
| Unit and contract tests | Data gates, routing, numerical behavior, package integrity, security boundaries, links, and SVG accessibility | Empirical validity of a new dataset |
| Portfolio rebuild | Fifteen reviewed projects regenerate in an isolated verified-file copy | Real-world adoption or impact |
| Source and artifact identity | Hashes, modes, exact file set, manifests, and source receipts | That a publisher's data answer a causal question |
| Numerical equivalence | Declared cross-version tolerances for structured floating-point results | Permission to normalize categorical, integer, source, or ordinary artifact differences |
| Static and security checks | Ruff, mypy, codespell, Bandit, dependency audit, and CodeQL | Absolute security or production authorization |

## Current supported matrix

- Python 3.11 is the minimum supported version.
- CI runs the public suite and portfolio rebuild on Python 3.11, 3.12, 3.13,
  and 3.14.
- Static quality runs on Python 3.14.
- Security checks include Bandit, dependency auditing, hardened source-builder
  tests, targeted branch coverage, and CodeQL.

The 103 public tests cover data-readiness safety, custom-workspace
initialization, CLI round-trips, adaptive routing, the decision engine,
generator idempotence, all source hashes, evidence contracts, independent
numerical benchmarks, properties, extreme inputs, package naming, local links,
SVG accessibility, compact Skill identity and footprint, safe quickstart
behavior, interactive explorer synchronization, semantic regeneration, ACS
special values, survey-weight policy, no-Git release verification, DNS and SSRF
boundaries, and external source-parser security.

## Static quality

Install the pinned development tools and run the quality target:

```bash
python3 -m pip install -r requirements-dev.txt
make quality
```

The target runs:

```bash
ruff check scripts tests examples/real-data-cases/projects/_shared/safe_external_io.py
mypy
codespell --config .codespellrc README.md CHANGELOG.md CONTRIBUTING.md \
  SECURITY.md VERSIONING.md demo docs references scripts skills tests
```

## Rebuild generated documentation and figures

Canonical source or generator changes must be followed by regeneration:

```bash
make visuals
```

This runs the README visual builder, terminal decision-report builder,
case-card/gallery builder, interactive explorer data builder, and compact Skill
builder. The generated files are then checked by the test suite. Do not
manually restyle generated case figures or report figures.

## Portfolio reproducibility

The portfolio verifier works in two modes:

1. A Git checkout uses the tracked file set and Git modes.
2. A published source ZIP without `.git` validates the self-excluding root
   `RELEASE-MANIFEST.json` before copying or executing project code.

Raw sources, labels, categories, counts, configuration, and ordinary artifacts
must agree exactly. Cross-version floating-point outputs may differ only within
the documented absolute and relative tolerances. A derived result hash can be
exempted only after the underlying structured result passes semantic
comparison.

See the full
[`Reproducibility Contract`](../references/reproducibility-contract.md).

## Release verification

The current stable release is
[`v1.1.1`](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/releases/tag/v1.1.1).
The release page publishes the versioned source ZIP and its SHA-256 checksum.
`CITATION.cff`, `CHANGELOG.md`, the annotated tag, and the release manifest must
identify the same release.

In a Git checkout, the package-integrity test verifies the manifest against its
declared content commit and confirms that the annotated release tag adds only
the self-excluding manifest. This lets `main` advance without relabeling
development changes as an older release. In a published source tree without
Git metadata, the verifier instead checks the extracted files, modes, exact
allowlist, and hashes directly against the bundled manifest.

The complete 103-test standalone regression suite, fifteen-project rebuild,
static quality checks, security checks, archive inspection, and public
redownload comparison are separate release gates.
