# Changelog

All notable public changes are documented here. The repository follows
[Semantic Versioning](https://semver.org/).

## [1.0.4] - 2026-08-12

### Changed

- Refreshed `agents/openai.yaml` using only supported skill-interface metadata:
  a concise user-facing description, the established teal brand color, and a
  122-character default prompt that retains the explicit Skill invocation.
- Kept the repository release version out of agent metadata because it is not a
  supported `agents/openai.yaml` field; release identity remains in citation,
  changelog, tag, manifest, and Release assets.

### Verification

- Added a metadata regression test covering the supported interface keys,
  description and prompt lengths, brand-color format, and named Skill mention.
- No case, raw source, analytical result, report, or figure changed in this
  release.

## [1.0.3] - 2026-08-11

### Fixed

- Allowed no-Git release verification to distinguish recognized non-symlink
  Python and pytest cache files from ordinary unlisted source files, so the
  public tests and portfolio verifier can run consecutively in one extracted
  release tree.
- Kept the exception narrow: unsupported files inside `__pycache__`, cache
  symlinks, ordinary extra files, mode changes, and hash changes remain fatal.

### Verification

- Added a cache allowlist regression test exercised by the existing Python
  3.11–3.14 CI matrix, plus a release-like acceptance run that executes the
  complete test suite before rebuilding all fifteen projects.
- No case, raw source, analytical result, report, or figure changed in this
  release.

## [1.0.2] - 2026-08-11

### Fixed

- Replaced the spatial composite-need zero fill with a 1,495-tract
  complete-case primary route while retaining all 1,597 analyzed tracts for
  poverty, transit, and MBTA-access analyses.
- Added an observed-median sensitivity and retained the v1.0.1 zero-fill hub
  set only as an explicitly invalid release-to-release audit comparison. The
  complete-case and median routes select the same five hubs; the legacy route
  overlaps on four.

### Security

- Made urllib HTTPS reads fail closed when the connected peer address cannot be
  observed, and required the same public-peer check on every redirect response.
- Added regression coverage for unknown final peers and unknown intermediate
  redirect peers while retaining the DNS, size, deadline, and atomic-write
  boundaries.

### Reproducibility

- Upgraded the release manifest to schema 1.1 and made no-Git verification
  reject unlisted source files, unsupported Git modes, and executable-bit
  tampering in addition to path and SHA-256 mismatches.
- Added route-specific spatial missingness metadata to the data-quality report,
  machine results, technical report, figures, and decision artifacts without
  removing any case or raw source.

## [1.0.1] - 2026-08-11

### Fixed

- Normalized and retained audit annotations for 175 ACS special values in the
  Opportunity Zone panel, excluded 84 affected tracts under one complete-case
  rule, and replaced the invalid rent result with a reuse-aware matched-change
  screen.
- Normalized NHANES XPORT missing and subnormal values, documented missing PIR,
  retained both survey weights, and selected `WTINT2YR` for the demographic
  interview-variable analysis.
- Normalized spatial ACS estimate and margin-of-error special values while
  preserving their source codes outside analytical numeric fields.
- Renamed the stale Bike `policies_2012_evaluation` output to
  `scenario_evaluation` without changing its modeled values.

### Security

- Added public-address DNS validation, connection-peer review, DNS-pinned and
  manually validated curl redirects, one monotonic retry deadline, and shared
  nested-archive depth/member/expansion budgets.
- Added negative tests for private DNS answers, private connected peers, slow
  retries, redirect validation, and cross-layer ZIP limits.

### Reproducibility

- Added a self-excluding `RELEASE-MANIFEST.json` and no-Git verifier fallback so
  the published source ZIP can rebuild all fifteen projects directly.
- Replaced the fixed case-quality label with machine-readable missing,
  sentinel, annotation, range, duplicate-key, severity, and gate findings.
- Added domain invariants for QOZ monetary/rate magnitudes, NHANES weights and
  missingness, spatial annotations, and analytical sentinel exclusion.
- Corrected the supported-Python and conditional-brief documentation and
  expanded the public regression suite from 81 to 92 tests.

## [1.0.0] - 2026-08-11

### Added

- Fifteen reproducible real-data evidence projects and ten conditional
  decision briefs with hash-locked inputs and accessible figures.
- A data-readiness gate with bounded CSV, TSV, JSON, JSONL, and NDJSON input;
  value-level privacy signals; and explicit user-confirmation states.
- Structured per-source manifests linking publisher, version, license, URL,
  SHA-256 artifacts, and contributed output fields.
- Python 3.12 verification, targeted branch-coverage checks, and offline source
  builder security fixtures.

### Security

- Centralized HTTPS-only downloads with redirect, response-size, timeout, and
  atomic-write limits.
- Centralized ZIP validation for archive size, member count, member size,
  total expansion, compression ratio, unsafe paths, duplicate names,
  encryption, and symbolic links.
- Added upstream request locks for the cross-city 311 source and compressed and
  decompressed LODES locks for the Opportunity Zone panel.

### Verification

- Verified all committed source hashes, portfolio rebuilds, generated reports,
  numerical tests, package integrity, and security-specific input fixtures on
  the release commit.

[1.0.4]: https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/releases/tag/v1.0.0
