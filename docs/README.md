# Documentation

High-Stakes Analytics & Decision Lab separates the public landing page, the
human documentation, and the executable Skill contract so each audience has a
clear entry point.

## Choose a path

| I want to… | Start here |
|---|---|
| Install the Skill or run a first question | [Getting started](getting-started.md) |
| Understand the evidence-gated design | [Architecture](architecture.md) |
| Browse the fifteen complete projects | [Real-data portfolio](../examples/real-data-cases/README.md) |
| Understand the repository before changing it | [Repository layout](repository-layout.md) |
| Reproduce tests, figures, and release checks | [Verification](verification.md) |
| Read the complete Agent Skill instructions | [SKILL.md](../SKILL.md) |
| Contribute a fix, case, or source review | [Contributing](../CONTRIBUTING.md) |
| Report a vulnerability | [Security policy](../SECURITY.md) |

## Documentation layers

The repository deliberately has three documentation layers:

1. **`README.md` is the product entrance.** It explains the problem, the
   fastest useful path, the portfolio, and the current evidence boundary.
2. **`docs/` is the human guide.** It contains onboarding, architecture,
   repository orientation, and verification instructions.
3. **`references/` is the runtime contract library.** These documents define
   data gates, method boundaries, provenance, reporting, and visual rules used
   by the Skill. They are not marketing pages and should remain precise.

The machine-readable case index is
[`examples/real-data-cases/cases.json`](../examples/real-data-cases/cases.json).
The public release identity is recorded in [`CITATION.cff`](../CITATION.cff),
[`CHANGELOG.md`](../CHANGELOG.md), and the release manifest.

## Core contracts

| Contract | Purpose |
|---|---|
| [Data Quality Gate](../references/data-quality-gate.md) | Decide whether data are ready, limited, confirmation-dependent, or blocked |
| [Adaptive Method Routing](../references/method-routing.md) | Select the smallest defensible descriptive, diagnostic, predictive, or prescriptive route |
| [Method Modules](../references/method-modules.md) | Define executable analytical modules and their limits |
| [Provenance Contract](../references/provenance-contract.md) | Trace governed parameters to sources and decision-use approval |
| [Reporting Standard](../references/reporting-standard.md) | Keep evidence, uncertainty, limitations, and decisions adjacent |
| [Editorial Evidence System](../references/editorial-visual-system.md) | Preserve the shared chart language, accessibility, and claim boundaries |
| [Reproducibility Contract](../references/reproducibility-contract.md) | Separate exact artifact identity from bounded numerical equivalence |

