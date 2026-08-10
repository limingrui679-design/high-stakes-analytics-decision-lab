# Verification Suite

The public Skill ships its complete standalone regression suite:

| Test group | Checks |
|---|---:|
| Data readiness, workspace initialization, preprocessing safety, privacy, malformed input, and CLI round-trip | 15 |
| Decision engine, routing, evidence, prediction, and optimization | 20 |
| Fifteen-project source hashes, evidence contracts, and claim boundaries | 12 |
| Independent numerical benchmarks, properties, and extreme inputs | 16 |
| Package naming, links, SVG accessibility, and repository hygiene | 4 |
| **Total** | **67** |

Run from the Skill directory:

```bash
python3 -m unittest discover -s tests -v
```

`tests/fixtures/synthetic-cases/` contains deterministic engineering fixtures,
not empirical portfolio projects. The fifteen public research projects remain in
`examples/real-data-cases/projects/`.
