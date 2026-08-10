#!/usr/bin/env python3
"""Initialize a traceable workspace for one question and one tabular dataset."""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analytics_router import build_blueprint, write_blueprint
from data_quality import load_contract, sha256_file, write_quality_bundle

SUPPORTED_SUFFIXES = {".csv", ".tsv", ".json", ".jsonl", ".ndjson"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _markdown_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _next_action(status: str) -> str:
    return {
        "ready": (
            "Review the generated blueprint, then continue with the route-specific "
            "analysis."
        ),
        "ready_with_documented_limitations": (
            "Review the documented limitations before continuing with the "
            "route-specific analysis."
        ),
        "needs_user_confirmation": (
            "Complete or confirm the draft data contract and approve only named, "
            "executable cleaning actions before analysis."
        ),
        "blocked": (
            "Correct the source or contract failure and rerun the data-quality gate "
            "before analysis."
        ),
    }[status]


def _unresolved_items(
    profile: dict[str, Any],
    plan: dict[str, Any],
) -> list[dict[str, str]]:
    items = [
        {
            "type": "quality_finding",
            "id": finding["code"],
            "severity": finding["severity"],
            "title": finding["title"],
        }
        for finding in profile["findings"]
        if finding["severity"] in {"critical", "high"}
    ]
    items.extend(
        {
            "type": "cleaning_action",
            "id": action["id"],
            "severity": "requires_confirmation",
            "title": action["action"],
        }
        for action in plan["actions"]
        if action["mode"] == "requires_confirmation"
    )
    return items


def render_workspace_readme(
    manifest: dict[str, Any],
    profile: dict[str, Any],
    plan: dict[str, Any],
    blueprint: dict[str, Any],
) -> str:
    """Render a short, action-oriented guide for the initialized workspace."""

    source_path = manifest["source"]["workspace_path"]
    contract_path = manifest["artifacts"]["contract_draft"]
    readiness_path = manifest["artifacts"]["readiness_report"]
    blueprint_path = manifest["artifacts"]["analysis_blueprint"]
    status = profile["quality_gate"]["status"]
    confirmation_count = sum(
        action["mode"] == "requires_confirmation" for action in plan["actions"]
    )
    safe_count = sum(action["mode"] == "safe_auto" for action in plan["actions"])
    question = _markdown_text(manifest["question"])
    primary = _markdown_text(blueprint["routing"]["primary_label"])
    execution_order = " → ".join(blueprint["routing"]["execution_order"])
    source_argument = shlex.quote(source_path)
    contract_argument = shlex.quote(contract_path)

    lines = [
        "# Custom Dataset Workspace",
        "",
        f"> **Question:** {question}",
        "",
        "| Current signal | Result |",
        "|---|---|",
        f"| Data-quality gate | `{status}` |",
        f"| Suggested primary route | **{primary}** |",
        f"| Execution order | {execution_order} |",
        f"| Safe normalization actions proposed | {safe_count} |",
        f"| Actions requiring confirmation | {confirmation_count} |",
        "",
        "![Data-quality overview](readiness/figures/data-quality-overview.svg)",
        "",
        f"**Next action:** {_next_action(status)}",
        "",
        "## Review these files",
        "",
        f"1. [`{contract_path}`]({contract_path}) — complete the intended use, "
        "grain, key, time, target, features, sensitive fields, and missing-value rules.",
        f"2. [`{readiness_path}`]({readiness_path}) — inspect quality, privacy, "
        "leakage, and proposed cleaning actions.",
        f"3. [`{blueprint_path}`]({blueprint_path}) — confirm that the suggested "
        "analytical route matches the real question.",
        "",
        "![Suggested analytical route](route/figures/analytics-lifecycle.svg)",
        "",
        "## Re-run the quality gate after editing the contract",
        "",
        "Run from the generated workspace directory and replace `/path/to/skill` "
        "with the Skill repository location:",
        "",
        "```bash",
        "python3 /path/to/skill/scripts/profile_dataset.py \\",
        f"  {source_argument} \\",
        f"  --contract {contract_argument} \\",
        "  --output-dir readiness",
        "```",
        "",
        "The copied source is unchanged and hash-verified. This initializer does not "
        "apply cleaning, fit a model, or make a recommendation.",
        "",
    ]
    return "\n".join(lines)


def initialize_workspace(
    dataset: Path,
    question: str,
    output_dir: Path,
    *,
    contract_path: Path | None = None,
    context: str = "",
    scope: str = "auto",
) -> dict[str, Any]:
    """Create a new workspace without transforming the supplied dataset."""

    normalized_question = " ".join(question.split())
    if not normalized_question:
        raise ValueError("question must be non-empty")
    if scope not in {"auto", "full"}:
        raise ValueError("scope must be 'auto' or 'full'")

    source = dataset.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Dataset does not exist or is not a file: {source}")
    if source.suffix.casefold() not in SUPPORTED_SUFFIXES:
        raise ValueError(
            "Supported input formats are CSV, TSV, JSON, JSONL, and NDJSON."
        )

    supplied_contract = (
        contract_path.expanduser().resolve() if contract_path is not None else None
    )
    if supplied_contract is not None and not supplied_contract.is_file():
        raise FileNotFoundError(
            f"Data contract does not exist or is not a file: {supplied_contract}"
        )

    destination = output_dir.expanduser().resolve()
    if destination.exists():
        raise FileExistsError(
            f"Output directory already exists; choose a new directory: {destination}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)

    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.init-",
            dir=destination.parent,
        )
    )
    try:
        source_dir = stage / "source"
        contract_dir = stage / "contract"
        readiness_dir = stage / "readiness"
        route_dir = stage / "route"
        source_dir.mkdir()
        contract_dir.mkdir()

        workspace_source = source_dir / source.name
        source_hash = sha256_file(source)
        shutil.copy2(source, workspace_source)
        if sha256_file(workspace_source) != source_hash:
            raise OSError("The workspace copy does not match the source SHA-256.")

        contract = load_contract(
            supplied_contract,
            dataset_name=source.stem,
        )
        profile, plan = write_quality_bundle(
            workspace_source,
            readiness_dir,
            contract=contract,
        )
        contract_draft = contract_dir / "data-contract.draft.json"
        _write_json(contract_draft, contract)

        blueprint = build_blueprint(
            normalized_question,
            context=context,
            scope=scope,
        )
        blueprint["data_status"] = "profiled"
        blueprint["data_readiness"] = {
            "status": profile["quality_gate"]["status"],
            "source_sha256": source_hash,
            "rows": profile["dataset"]["rows"],
            "columns": profile["dataset"]["columns"],
            "contract_source": contract["contract_source"],
            "report": "../readiness/data-quality-report.md",
        }
        write_blueprint(blueprint, route_dir)

        source_relative = f"source/{source.name}"
        manifest = {
            "schema_version": "1.0",
            "generated_at": _utc_now(),
            "question": normalized_question,
            "context": context.strip(),
            "source": {
                "file_name": source.name,
                "workspace_path": source_relative,
                "sha256": source_hash,
                "bytes": source.stat().st_size,
                "copied_unchanged": True,
                "raw_source_immutable": True,
            },
            "contract": {
                "source": contract["contract_source"],
                "provided_by_user": supplied_contract is not None,
            },
            "data_quality": {
                "status": profile["quality_gate"]["status"],
                "findings": len(profile["findings"]),
                "safe_actions": sum(
                    action["mode"] == "safe_auto" for action in plan["actions"]
                ),
                "confirmation_actions": sum(
                    action["mode"] == "requires_confirmation"
                    for action in plan["actions"]
                ),
            },
            "routing": {
                "primary_mode": blueprint["routing"]["primary_mode"],
                "primary_label": blueprint["routing"]["primary_label"],
                "execution_order": blueprint["routing"]["execution_order"],
                "confidence": blueprint["routing"]["confidence"],
            },
            "unresolved_items": _unresolved_items(profile, plan),
            "next_action": _next_action(profile["quality_gate"]["status"]),
            "artifacts": {
                "contract_draft": "contract/data-contract.draft.json",
                "readiness_report": "readiness/data-quality-report.md",
                "readiness_json": "readiness/data-quality-report.json",
                "cleaning_plan": "readiness/cleaning-plan.json",
                "analysis_blueprint": "route/analysis-blueprint.md",
                "analysis_blueprint_json": "route/analysis-blueprint.json",
            },
            "guardrails": {
                "cleaning_applied": False,
                "model_fitted": False,
                "recommendation_generated": False,
            },
        }
        _write_json(stage / "setup.json", manifest)
        (stage / "README.md").write_text(
            render_workspace_readme(manifest, profile, plan, blueprint),
            encoding="utf-8",
        )
        stage.replace(destination)
        return manifest
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a traceable custom-data workspace without applying cleaning "
            "or fitting a model."
        )
    )
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--question", required=True)
    parser.add_argument("--context", default="")
    parser.add_argument("--scope", choices=("auto", "full"), default="auto")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = initialize_workspace(
            args.dataset,
            args.question,
            args.output_dir,
            contract_path=args.contract,
            context=args.context,
            scope=args.scope,
        )
    except (FileExistsError, FileNotFoundError, OSError, ValueError) as error:
        raise SystemExit(f"init_case.py: error: {error}") from error

    print(f"Workspace: {args.output_dir.expanduser().resolve()}")
    print(f"Source SHA-256: {manifest['source']['sha256']}")
    print(f"Quality gate: {manifest['data_quality']['status']}")
    print(f"Primary route: {manifest['routing']['primary_label']}")
    print(f"Next action: {manifest['next_action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
