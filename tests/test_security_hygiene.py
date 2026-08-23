from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import check_tracked_secrets  # noqa: E402


class SecurityHygieneTests(unittest.TestCase):
    def test_secret_scan_detects_content_and_filename_without_echoing_value(self) -> None:
        with tempfile.TemporaryDirectory(prefix="hsadl-secret-scan-") as temporary:
            root = Path(temporary)
            token = "gh" + "p_" + "A" * 36
            content_path = root / "settings.txt"
            content_path.write_text(
                f"risk-based language is not a key\ntoken={token}\n",
                encoding="utf-8",
            )
            filename_path = root / ".env.production"
            filename_path.write_text("MODE=test\n", encoding="utf-8")
            findings = check_tracked_secrets.scan_paths(
                root,
                [content_path, filename_path],
            )
            self.assertEqual(
                [(item.path, item.rule, item.line) for item in findings],
                [
                    ("settings.txt", "github-token", 2),
                    (".env.production", "secret-shaped-filename", None),
                ],
            )
            rendered = check_tracked_secrets.format_findings(findings)
            self.assertNotIn(token, rendered)
            self.assertIn("settings.txt:2 [github-token]", rendered)

    def test_secret_scan_supports_no_git_release_manifest_discovery(self) -> None:
        with tempfile.TemporaryDirectory(prefix="hsadl-secret-release-") as temporary:
            root = Path(temporary)
            document = root / "README.md"
            document.write_text("Public release fixture.\n", encoding="utf-8")
            manifest = root / "RELEASE-MANIFEST.json"
            manifest.write_text(
                json.dumps({"files": [{"path": "README.md"}]}) + "\n",
                encoding="utf-8",
            )
            paths = check_tracked_secrets.tracked_paths(root)
            self.assertEqual(
                {path.relative_to(root).as_posix() for path in paths},
                {"README.md", "RELEASE-MANIFEST.json"},
            )
            self.assertEqual(check_tracked_secrets.scan_paths(root, paths), [])


if __name__ == "__main__":
    unittest.main()
