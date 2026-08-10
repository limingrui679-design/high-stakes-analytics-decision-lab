# Versioning Policy

The repository uses semantic versioning for public releases, but its internal
components keep separate version namespaces because they describe different
contracts.

| Version field | Scope |
|---|---|
| Repository release | The installable Skill, public documentation, tests, and bundled portfolio |
| `engine_version` | Decision-engine input, simulation, and output behavior |
| `portfolio_version` | The fifteen-project catalog and evidence-package contract |
| `router_version` | Question-routing schema and method-selection behavior |

Component versions are not expected to match one another. A component version
changes only when that component's contract changes; the repository release
version records the tested combination shipped together.

Until the first tagged repository release, `main` is the supported development
line. A release should be tagged only after the complete verification suite,
static quality checks, source-hash validation, and generated-artifact checks
pass on the release commit.
