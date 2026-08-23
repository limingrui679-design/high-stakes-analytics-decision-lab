# Security Policy

## Supported versions

Security updates apply to the latest `v1.1.x` release and the current `main`
branch. The supported Python baseline is 3.11 or newer, with CI coverage on
Python 3.11, 3.12, 3.13, and 3.14.

## Reporting a vulnerability

Report vulnerabilities through the repository's
[private vulnerability reporting form](https://github.com/limingrui679-design/high-stakes-analytics-decision-lab/security/advisories/new).
Do not include sensitive exploit details, private data, or credentials in a
public issue.

Security reports may include unsafe path handling, unintended command
execution, privacy leakage, or evidence and artifact tampering. Questions about
empirical claims, source suitability, or data quality are usually better filed
as regular source or quality issues unless they expose a security weakness.

CI rejects high-confidence credential patterns and secret-shaped tracked file
names without printing suspected credential values. This narrow gate complements
Bandit, dependency auditing, hardened input tests, and CodeQL; it is not a claim
of exhaustive secret detection or security certification.

Please include the affected file or workflow, a minimal reproduction, the
observed impact, and any suggested mitigation when those details can be shared
safely.
