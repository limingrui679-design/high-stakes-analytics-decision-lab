# Repository Layout

The repository is both an Agent Skill and a reproducible research portfolio.
Its structure therefore keeps a compact installable Skill separate from human
guides, canonical runtime sources, interactive navigation, and generated evidence.

## Top-level map

```text
high-stakes-analytics-decision-lab/
├── README.md                       # concise public product entrance
├── skills/high-stakes-analytics-decision-lab/
│   ├── SKILL.md                    # executable Agent Skill contract
│   ├── scripts/                    # compact copied runtime
│   ├── references/                 # compact copied contracts and case precedents
│   └── bundle-manifest.json        # exact lightweight package file/hash contract
├── demo/                           # dependency-free interactive case explorer
├── docs/                           # human onboarding and architecture guides
├── references/                     # runtime quality, method, provenance, and report contracts
├── assets/                         # templates and canonical README visuals
├── scripts/                        # profiling, preparation, analysis, generation, verification
├── examples/real-data-cases/       # fifteen complete reproducible evidence projects
├── tests/                          # standalone contract and regression suite
├── .github/                        # CI, security, issue, and pull-request workflows
├── Makefile                        # memorable maintainer commands
├── CHANGELOG.md                    # release history
├── CITATION.cff                    # citation and public version identity
├── CONTRIBUTING.md                 # contribution and evidence rules
├── SECURITY.md                     # private vulnerability reporting
├── VERSIONING.md                   # release and component namespaces
└── RELEASE-MANIFEST.json           # no-Git release file and hash contract
```

## Why the Skill is nested

Compatible installers discover `skills/<name>/SKILL.md` as a named package.
Keeping the contract there prevents installation from copying the complete
research portfolio. `scripts/build_skill_bundle.py` copies the reviewed runtime,
templates, and references into that self-contained directory and records every
file hash. Root scripts and references remain canonical; copied bundle files
must not be hand-edited.

The executable Python remains in `scripts/` because each command is a
standalone, standard-library-first interface. Shared portfolio implementation
lives under `examples/real-data-cases/projects/_shared/` so each empirical
project can rebuild from the same reviewed runtime without pretending to be an
independently deployed product.

## Human docs versus runtime references

| Directory | Audience | Change rule |
|---|---|---|
| `docs/` | Users, reviewers, and contributors | Explain how to navigate, use, and verify the project |
| `references/` | The Skill and technical reviewers | Define enforceable quality, method, provenance, reporting, and visual contracts |
| `skills/high-stakes-analytics-decision-lab/` | Agent Skills-compatible installers | Generated compact package; change canonical sources and rebuild |
| `demo/` | Portfolio readers and reviewers | Interactive, school-neutral navigation across routes and capabilities |
| `examples/real-data-cases/cases/` | Portfolio readers | Generated case cards; edit canonical case metadata or builders first |
| `examples/real-data-cases/projects/` | Reproducers and domain reviewers | Preserve source, code, outputs, and claim boundary together |

## Canonical and generated files

| If you need to change… | Edit first | Then run |
|---|---|---|
| README hero or architecture visuals | `scripts/build_readme_visuals.py` or shared visual helpers | `make visuals` |
| Case cards, landscape, or case-gallery README | `cases.json` and `scripts/build_case_examples.py` | `make visuals` |
| Capability paths | `capability-map.json` and `scripts/build_case_examples.py` | `make visuals` |
| Interactive explorer data | `cases.json`, `capability-map.json`, and `scripts/build_portfolio_demo.py` | `make visuals` |
| Installable Skill runtime | Root scripts, references, templates, nested `SKILL.md`, or agent metadata | `make bundle` |
| Evidence or decision report figures | Project source/configuration and reporting builders | The affected project pipeline, then `make verify` |
| Data-quality behavior | `scripts/data_quality.py` and the relevant contract/tests | `make verify` |
| Decision behavior | `scripts/decision_engine.py`, schemas, and numerical tests | `make verify` |
| Public documentation only | `README.md` or `docs/` | Link check, codespell, and the package-integrity tests |

Generated artifacts must not be edited as isolated copies. The repository
tests compare canonical generators with committed cards, galleries, reports,
and SVG output.

## Project-local structure

Each real-data project follows the same evidence package shape while allowing
case-specific methods and terminal outcomes:

```text
<project-id>/
├── PROJECT.md
├── source-manifest.json
├── config.json
├── download_data.py
├── prepare_data.py
├── analyze.py
├── build_decision_case.py
├── data/
│   ├── raw/
│   ├── processed/
│   ├── data-dictionary.json
│   ├── download-receipt.json
│   └── quality-report.json
└── outputs/
    ├── report.md
    ├── results.json
    ├── chart-map.json
    ├── figures/
    └── decision/                   # present only when a separate decision layer is justified
```

The common shape is an evidence contract, not a requirement that every case
use the same model, report sections, or decision endpoint.
