# Reproducibility contract

The repository distinguishes source integrity, within-environment
determinism, and cross-version numerical equivalence. They answer different
questions and are not interchangeable.

## 1. Source integrity is byte-exact

Every committed raw or minimized source must match its `source-manifest.json`
and download receipt SHA-256. Source files, manifest hashes, configuration
hashes, labels, categories, integer counts, report language, and decision
statuses receive no numerical tolerance.

## 2. A fixed environment is deterministic

Project scripts use committed source snapshots, sorted iteration where order
matters, fixed random seeds, and a standard-library runtime. Repeating a build
with the same Python interpreter and toolchain must produce the same artifact
bytes and receipts.

## 3. Supported Python versions are semantically equivalent

Different CPython versions may accumulate or serialize the final few bits of a
floating-point calculation differently. The public verification workflow
therefore rebuilds all fifteen projects on Python 3.11, 3.12, 3.13, and 3.14 and
enforces:

- absolute tolerance: `2e-8`;
- relative tolerance: `1e-12`;
- exact list lengths, dictionary keys, labels, categories, counts, boundaries,
  and decision statuses;
- exact raw-source, source-manifest, and configuration hashes;
- derived analytical or case hashes may differ only when the complete
  underlying structured artifact passes every semantic comparison.

The tolerance is a comparison rule, not a license to round, suppress, or alter
published metrics. Full-precision committed results remain the evidence
record.

## Verification

```bash
python3 scripts/verify_portfolio_reproducibility.py
```

The verifier copies only verified release files to an isolated temporary directory,
runs the complete fifteen-project preparation, analysis, decision-case, report,
visual, and gallery build, and fails on any unapproved difference or unexpected
generated file. In a Git checkout, the allowlist comes from `git ls-files`; in
a source ZIP without `.git`, the same paths and SHA-256 values come from the
self-excluding root `RELEASE-MANIFEST.json`. Manifest schema 1.1 additionally
requires the source tree to contain exactly the listed files and, on POSIX
systems, verifies the Git executable-bit mode before any project code runs.
