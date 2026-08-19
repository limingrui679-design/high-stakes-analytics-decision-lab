from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import build_portfolio_demo  # noqa: E402
import build_skill_bundle  # noqa: E402
import quickstart_demo  # noqa: E402

SKILL_NAME = "high-stakes-analytics-decision-lab"
SKILL_ROOT = ROOT / "skills" / SKILL_NAME


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class UserExperienceTests(unittest.TestCase):
    def test_unified_cli_exposes_the_complete_command_surface(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "hsadl.py"), "--help"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        for command in (
            "doctor",
            "demo",
            "start",
            "route",
            "profile",
            "prepare",
            "evidence",
            "predict",
            "allocate",
            "validate",
            "run",
        ):
            with self.subTest(command=command):
                self.assertRegex(result.stdout, rf"(?m)^  {command}\s{{2,}}")

    def test_compact_skill_doctor_reports_ready(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SKILL_ROOT / "scripts" / "doctor.py"),
                "--json",
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["layout"], "installed_skill")
        self.assertLessEqual(len(list(SKILL_ROOT.rglob("*"))), 64)
        self.assertLessEqual(
            sum(path.stat().st_size for path in SKILL_ROOT.rglob("*") if path.is_file()),
            2 * 1024 * 1024,
        )

    def test_quickstart_demo_is_safe_reproducible_setup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="hsadl-demo-test-") as temporary:
            output = Path(temporary) / "demo"
            first = quickstart_demo.build_demo(output)
            source = output / "source" / "support-demand-demo.csv"
            first_hash = sha256(source)
            second = quickstart_demo.build_demo(output)
            self.assertEqual(first["quality_gate"], "ready")
            self.assertEqual(second["quality_gate"], "ready")
            self.assertEqual(sha256(source), first_hash)
            metadata = json.loads(
                (output / "demo-metadata.json").read_text(encoding="utf-8")
            )
            self.assertTrue(metadata["synthetic_engineering_fixture"])
            self.assertFalse(metadata["empirical_claims_permitted"])
            self.assertFalse(metadata["model_fitted"])
            self.assertFalse(metadata["recommendation_generated"])
            self.assertEqual(len(source.read_text(encoding="utf-8").splitlines()), 9)
            self.assertTrue((output / "readiness" / "data-quality-report.json").is_file())
            self.assertTrue((output / "route" / "analysis-blueprint.json").is_file())

    def test_quickstart_refuses_to_overwrite_an_unowned_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="hsadl-demo-refusal-") as temporary:
            output = Path(temporary) / "existing"
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("user-owned\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                quickstart_demo.build_demo(output)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "user-owned\n")

    def test_capability_map_is_complete_valid_and_school_neutral(self) -> None:
        path = ROOT / "examples" / "real-data-cases" / "capability-map.json"
        text = path.read_text(encoding="utf-8")
        payload = json.loads(text)
        cases = json.loads(
            (ROOT / "examples" / "real-data-cases" / "cases.json").read_text(
                encoding="utf-8"
            )
        )["cases"]
        capability_ids = {item["id"] for item in payload["capabilities"]}
        self.assertTrue(payload["policy"]["school_neutral"])
        self.assertEqual(set(payload["cases"]), {case["id"] for case in cases})
        for mapping in payload["cases"].values():
            self.assertIn(mapping["primary"], capability_ids)
            self.assertTrue(set(mapping["supporting"]).issubset(capability_ids))
            self.assertGreaterEqual(len(mapping["signals"]), 3)
        self.assertNotRegex(text.casefold(), r'"(?:school|program|university)"\s*:')

    def test_skill_bundle_is_exactly_reproducible_from_canonical_sources(self) -> None:
        expected = build_skill_bundle.build_bundle()
        manifest = json.loads(
            (SKILL_ROOT / "bundle-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest, expected)
        listed = {entry["path"] for entry in manifest["files"]}
        observed = {
            path.relative_to(SKILL_ROOT).as_posix()
            for path in SKILL_ROOT.rglob("*")
            if path.is_file() and path.name != "bundle-manifest.json"
        }
        self.assertEqual(listed, observed)
        for entry in manifest["files"]:
            with self.subTest(path=entry["path"]):
                path = SKILL_ROOT / entry["path"]
                self.assertEqual(entry["bytes"], path.stat().st_size)
                self.assertEqual(entry["sha256"], sha256(path))

    def test_interactive_explorer_is_complete_synced_and_school_neutral(self) -> None:
        payload = build_portfolio_demo.build_payload()
        data_path = ROOT / "demo" / "data.js"
        self.assertEqual(
            data_path.read_text(encoding="utf-8"),
            build_portfolio_demo.render_data(payload),
        )
        self.assertTrue(payload["school_neutral"])
        self.assertEqual(payload["metrics"]["cases"], 15)
        self.assertEqual(len(payload["cases"]), 15)
        self.assertEqual(len({item["id"] for item in payload["cases"]}), 15)
        self.assertEqual(
            {route for item in payload["cases"] for route in item["routes"]},
            {"descriptive", "diagnostic", "predictive", "prescriptive"},
        )
        for item in payload["cases"]:
            with self.subTest(case=item["id"], target="figure"):
                self.assertTrue((ROOT / "demo" / item["figure"]).resolve().is_file())
            for key in ("case_card", "project"):
                with self.subTest(case=item["id"], target=key):
                    self.assertTrue(item[key].startswith("https://github.com/"))
        public_demo = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in sorted((ROOT / "demo").glob("*"))
            if path.is_file()
        ).casefold()
        self.assertNotRegex(
            public_demo,
            r'"(?:school|program|university)"\s*:',
        )

    def test_pages_workflow_is_pinned_and_deploys_only_the_explorer(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(
            encoding="utf-8"
        )
        uses = re.findall(r"(?m)^\s+uses:\s+([^#\s]+)", workflow)
        self.assertEqual(len(uses), 4)
        for action in uses:
            with self.subTest(action=action):
                self.assertRegex(action, r"^[^@]+@[0-9a-f]{40}$")
        self.assertIn("cp -R demo/. _site/demo/", workflow)
        self.assertIn(
            "cp -R examples/real-data-cases/figures/. "
            "_site/examples/real-data-cases/figures/",
            workflow,
        )
        self.assertNotIn("cp -R . _site", workflow)
        self.assertTrue((ROOT / "pages" / "index.html").is_file())
        self.assertIn(
            "https://limingrui679-design.github.io/"
            "high-stakes-analytics-decision-lab/demo/",
            (ROOT / "README.md").read_text(encoding="utf-8"),
        )

    def test_codeql_action_updates_are_pinned_atomic_and_grouped(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "codeql.yml").read_text(
            encoding="utf-8"
        )
        references = re.findall(
            r"github/codeql-action/(?:init|analyze)@([0-9a-f]{40})", workflow
        )
        self.assertEqual(len(references), 2)
        self.assertEqual(len(set(references)), 1)
        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(
            encoding="utf-8"
        )
        self.assertRegex(
            dependabot,
            r'(?ms)^\s+codeql:\s*$.*?^\s+- "github/codeql-action/\*"\s*$',
        )


if __name__ == "__main__":
    unittest.main()
