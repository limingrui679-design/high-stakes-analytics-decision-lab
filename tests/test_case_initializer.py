from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from data_quality import sha256_file  # noqa: E402
from init_case import initialize_workspace  # noqa: E402


class CaseInitializerTests(unittest.TestCase):
    def test_initializer_preserves_source_and_creates_reviewable_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "customer data.csv"
            source.write_text(
                "customer_id,amount\n1, 10 \n2,20\n",
                encoding="utf-8",
            )
            original_bytes = source.read_bytes()
            workspace = root / "workspace"

            manifest = initialize_workspace(
                source,
                "Which customers are likely to respond next month?",
                workspace,
                scope="auto",
            )

            copied_source = workspace / "source" / source.name
            self.assertEqual(copied_source.read_bytes(), original_bytes)
            self.assertEqual(sha256_file(copied_source), sha256_file(source))
            self.assertTrue(manifest["source"]["copied_unchanged"])
            self.assertFalse(manifest["guardrails"]["cleaning_applied"])
            self.assertEqual(
                manifest["data_quality"]["status"],
                "needs_user_confirmation",
            )
            self.assertEqual(manifest["routing"]["primary_mode"], "predictive")

            required_paths = [
                workspace / "README.md",
                workspace / "setup.json",
                workspace / "contract/data-contract.draft.json",
                workspace / "readiness/data-quality-report.md",
                workspace / "readiness/data-quality-report.json",
                workspace / "readiness/cleaning-plan.json",
                workspace / "readiness/figures/data-quality-overview.svg",
                workspace / "route/analysis-blueprint.md",
                workspace / "route/analysis-blueprint.json",
                workspace / "route/figures/analytics-lifecycle.svg",
            ]
            self.assertTrue(all(path.is_file() for path in required_paths))
            self.assertTrue(
                ET.parse(
                    workspace / "route/figures/analytics-lifecycle.svg"
                ).getroot().tag.endswith("svg")
            )

            blueprint = json.loads(
                (workspace / "route/analysis-blueprint.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(blueprint["data_status"], "profiled")
            self.assertEqual(
                blueprint["data_readiness"]["source_sha256"],
                sha256_file(source),
            )
            blueprint_report = (
                workspace / "route/analysis-blueprint.md"
            ).read_text(encoding="utf-8")
            self.assertIn("A dataset was profiled", blueprint_report)
            self.assertNotIn("No dataset was supplied", blueprint_report)
            shared_text = (workspace / "setup.json").read_text(encoding="utf-8")
            self.assertNotIn(str(root), shared_text)

    def test_cli_accepts_confirmed_contract_and_refuses_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.csv"
            source.write_text("id,amount\n1,10\n2,20\n", encoding="utf-8")
            contract = root / "contract.json"
            contract.write_text(
                json.dumps(
                    {
                        "dataset_name": "input",
                        "intended_use": "descriptive",
                        "grain": "one row per customer",
                        "required_columns": ["id", "amount"],
                        "primary_key": ["id"],
                        "numeric_columns": ["amount"],
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            workspace = root / "workspace"
            command = [
                sys.executable,
                str(SCRIPT_DIR / "init_case.py"),
                str(source),
                "--question",
                "What is happening to customer amounts?",
                "--contract",
                str(contract),
                "--output-dir",
                str(workspace),
            ]

            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Quality gate: ready", result.stdout)
            self.assertIn("Primary route: Descriptive analytics", result.stdout)

            repeated = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("Output directory already exists", repeated.stderr)
            self.assertEqual(
                json.loads(
                    (workspace / "setup.json").read_text(encoding="utf-8")
                )["data_quality"]["status"],
                "ready",
            )


if __name__ == "__main__":
    unittest.main()
