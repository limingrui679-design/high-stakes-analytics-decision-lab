"""One reproducible reporting contract; individual studies own their methods and decisions."""

import csv
import gzip
import importlib.util
import io
import sys
from html import escape
from pathlib import Path

from applied_reporting import decision_brief, extra_evidence
from portfolio_core import _quality, load_json, sha256, verify_raw_files, write_json
from portfolio_reporting import _resolve_project_parameter_provenance


def rounded(obj):
    if isinstance(obj, float):
        return round(obj, 8)
    if isinstance(obj, dict):
        return {k: rounded(v) for k, v in obj.items()}
    if isinstance(obj, (tuple, list)):
        return [rounded(v) for v in obj]
    return obj


def bars(chart):
    title, unit = chart["title"], chart["unit"]
    vals = chart["values"]
    low = min(0, *vals.values())
    high = max(0, *vals.values())
    span = high - low or 1

    def x(value):
        return 237 + 420 * (value - low) / span

    height = 90 + 34 * len(vals)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 825 {height}" role="img" aria-labelledby="t d">',
        f'<title id="t">{escape(title)}</title><desc id="d">{escape(chart["note"])}</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="sans-serif" fill="#172d43">',
        f'<text x="16" y="25" font-size="18" font-weight="bold">{escape(title)}</text>',
        f'<text x="16" y="47" font-size="13">{escape(unit)}</text>',
        f'<path d="M {x(0):.2f} 55 V {height - 19}" stroke="#8495a3"/>',
    ]
    for i, (label, value) in enumerate(vals.items()):
        y = 62 + 34 * i
        a, b = sorted((x(0), x(value)))
        parts.extend(
            [
                f'<text x="16" y="{y + 15}" font-size="13">{escape(str(label))}</text>',
                f'<rect x="{a:.2f}" y="{y}" width="{b - a:.2f}" height="18" fill="#166c77"/>',
                f'<text x="683" y="{y + 15}" font-size="14">{value:,.3f}</text>',
            ]
        )
    return "\n".join(parts + ["</g></svg>\n"])


def load_study(project):
    spec = importlib.util.spec_from_file_location(project.name, project / "study.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(project, d, m):
    records = verify_raw_files(project)
    raw = project / "data/raw/observations.csv.gz"
    source = gzip.decompress(raw.read_bytes())
    with io.StringIO(source.decode("utf-8"), newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(d["fields"]):
            raise ValueError("Field contract mismatch")
        rows = list(reader)
    quality = _quality(rows, key=d["key"])
    quality.update(
        expected_rows=m["expected_rows"], row_count_matches_manifest=len(rows) == m["expected_rows"]
    )
    if not quality["row_count_matches_manifest"] or quality["duplicate_key_count"]:
        raise ValueError("Primary key or row count mismatch")
    out = project / "data/processed/analysis.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(source)
    write_json(
        project / "data/data-dictionary.json",
        dict(grain=d["grain"], primary_key=d["key"], fields=d["fields"]),
    )
    write_json(project / "data/quality-report.json", quality)
    write_json(
        project / "data/download-receipt.json",
        dict(
            status="verified",
            source_id=m["source_id"],
            files=records,
            basis="Bundled source hashes checked before preparation",
        ),
    )
    return rows


def run(project, action):
    d = load_json(project / "study-design.json")
    m = load_json(project / "source-manifest.json")
    cfg = load_json(project / "config.json")
    outputs = project / "outputs"
    if action in ("prepare", "download"):
        prepare(project, d, m)
        return
    if action == "decision":
        r = load_json(outputs / "results.json")
        decision_brief(project, d, r, bars)
        write_json(
            outputs / "decision-case-status.json",
            dict(
                status=d["endpoint"],
                owner=d["owner"],
                evidence=r["conclusion"],
                next_decision=r["next_decision"],
                boundary=d["boundary"],
            ),
        )
        return
    verify_raw_files(project)
    prepared = project / "data/processed/analysis.csv"
    if sha256(prepared) != m["raw_files"][0]["uncompressed_sha256"]:
        raise ValueError("Prepared data differs from verified snapshot")
    with prepared.open(newline="", encoding="utf-8") as h:
        r = rounded(
            load_study(project).evaluate(
                list(csv.DictReader(h)), cfg["parameters"], cfg["analysis_seed"]
            )
        )
    r.update(
        project_id=project.name,
        study_design=dict(route=d["route"], protocol=d["design"]),
        data=dict(rows=m["expected_rows"], grain=d["grain"], snapshot_sha256=sha256(prepared)),
        decision_support=dict(status=d["endpoint"]),
    )
    write_json(outputs / "results.json", r)
    provenance = _resolve_project_parameter_provenance(cfg, m)
    for rec in provenance:
        rec["review_date"] = d["accessed_at"]
        for review in rec["approval_chain"]:
            if review["role"] == "model_author":
                review["date"] = d["accessed_at"]
    write_json(
        outputs / "parameter-provenance.json", dict(project_id=project.name, records=provenance)
    )
    charts = []
    lines = [
        "# " + d["title"],
        "",
        "## Executive Summary",
        "",
        r["conclusion"],
        "",
        "## Decision and evaluation design",
        "",
        f"**Decision owner.** {d['owner']}.",
        "",
        d["question"],
        "",
        d["design"],
        "",
        f"**Data.** {m['expected_rows']:,} rows. {d['grain']}. [{d['dataset']}]({d['landing_page']}).",
        "",
        "## Evidence",
        "",
    ]
    (outputs / "figures").mkdir(parents=True, exist_ok=True)
    for slug, chart in r["figures"].items():
        path = f"figures/{slug}.svg"
        (outputs / path).write_text(bars(chart), encoding="utf-8")
        charts.append(
            dict(
                path=path,
                question=chart["title"],
                supported_finding=chart["note"],
                interpretation_boundary=d["boundary"],
                source_id=m["source_id"],
            )
        )
        lines.extend(
            [
                "### " + chart["title"],
                "",
                chart["note"],
                "",
                f"![{chart['title']}]({path})",
                "",
                f"| Comparison | {chart['unit']} |",
                "|---|---:|",
            ]
        )
        lines.extend(f"| {name} | {v:,.3f} |" for name, v in chart["values"].items())
        lines.append("")
    lines.extend(["## Reading the underlying evidence", "", *extra_evidence(d["number"], r)])
    feedback_url = "https://limingrui679-design.github.io/high-stakes-analytics-decision-lab/demo/learning-feedback/"
    supplemental = {
        20: [("Measured routing latency and cache size", "benchmark-host.json")],
        24: [
            (
                "Certified orders from the equal-wall-time solver comparison",
                "../solver-witnesses.json",
            )
        ],
        26: [
            ("Try the counterexample variant", feedback_url + "#counterexample"),
            ("Try the direct-correction variant", feedback_url + "#correction"),
            ("Download the offline prototype", "../learning-prototype.html"),
        ],
        30: [("Measured query latency, recovery time and storage", "benchmark-host.json")],
    }
    if d["number"] in supplemental:
        lines.extend(
            [" · ".join(f"[{title}]({target})" for title, target in supplemental[d["number"]]), ""]
        )
    if d["number"] in (18, 21, 22, 24, 25, 27):
        lines.extend(["[Read the decision brief](decision/report/decision-report.md)", ""])
    lines.extend(
        [
            "## Next decision",
            "",
            r["next_decision"],
            "",
            "## What this study cannot establish",
            "",
            d["boundary"],
            "",
            "The [machine-readable audit](results.json) contains denominators, subgroup results and additional diagnostics.",
            "",
            "Result SHA-256: " + chr(96) + sha256(outputs / "results.json") + chr(96),
            "",
        ]
    )
    (outputs / "report.md").write_text("\n".join(lines))
    write_json(outputs / "chart-map.json", dict(project_id=project.name, charts=charts))
    (project / "PROJECT.md").write_text(
        "\n".join(
            [
                "# " + d["title"],
                "",
                d["question"],
                "",
                d["design"],
                "",
                r["conclusion"],
                "",
                "[Read the results](outputs/report.md) · [Study protocol](study-design.json) · [Publisher and data terms](source-manifest.json)",
                "",
                "## Reproduce",
                "",
                "From this directory run the commands below with Python 3.11 or newer.",
                "",
                "~~~sh",
                "python prepare_data.py",
                "python analyze.py",
                "python build_decision_case.py",
                "~~~",
                "",
                "To check the upstream extraction, see the [source rebuild instructions](../../source_tools/README.md).",
                "",
            ]
        )
    )


def entry(action, filename):
    if len(sys.argv) != 1:
        raise SystemExit("For upstream reconstruction use source_tools/replay_extract.py --help.")
    run(Path(filename).resolve().parent, action)
