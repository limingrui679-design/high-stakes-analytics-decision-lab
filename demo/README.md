# Interactive case explorer

Open [`index.html`](index.html) directly or serve the repository root with any
static HTTP server. The explorer has no external runtime dependency, sends no
data, and works from the generated [`data.js`](data.js) payload.

Rebuild the payload after changing `cases.json` or `capability-map.json`:

```bash
python3 scripts/build_portfolio_demo.py
```

The explorer is school-neutral. It surfaces existing public-data evidence,
valid terminal states, and claim boundaries; it does not create new empirical
results or imply deployment, adoption, external review, or achieved impact.
