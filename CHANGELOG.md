# Changelog

All notable public changes are documented here. The repository follows
[Semantic Versioning](https://semver.org/).

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

[1.0.0]: https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/releases/tag/v1.0.0
