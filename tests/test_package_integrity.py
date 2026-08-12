from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import build_case_examples  # noqa: E402
from build_readme_visuals import (  # noqa: E402
    _portfolio_metrics,
    adaptive_system_svg,
    hero_svg,
    report_layers_svg,
)

SKILL_NAME = "high-stakes-analytics-decision-lab"
LEGACY_NAME = "high-stakes-" + "decision-lab"


class PackageIntegrityTests(unittest.TestCase):
    def test_skill_frontmatter_and_install_command_use_one_name(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", skill, flags=re.DOTALL)
        self.assertIsNotNone(match)
        assert match is not None
        lines = [
            line
            for line in match.group(1).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(
            [line.split(":", 1)[0].strip() for line in lines],
            ["name", "description"],
        )
        self.assertIn(f"name: {SKILL_NAME}", match.group(1))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            f"npx skills add limingrui679-design/{SKILL_NAME} -g",
            readme,
        )
        citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        version_match = re.search(r"(?m)^version: ([0-9]+\.[0-9]+\.[0-9]+)$", citation)
        self.assertIsNotNone(version_match)
        assert version_match is not None
        release_version = version_match.group(1)
        self.assertIn(
            f"releases/tag/v{release_version}",
            readme,
        )
        self.assertIn(
            f"## [{release_version}]",
            (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
        )
        test_count = sum(
            len(re.findall(r"^\s+def test_", path.read_text(encoding="utf-8"), re.MULTILINE))
            for path in (ROOT / "tests").glob("test_*.py")
        )
        self.assertIn(f"The {test_count} public tests", readme)
        self.assertIn(f"complete {test_count}-test", readme)
        metrics = _portfolio_metrics()
        normalized_readme = " ".join(readme.split())
        self.assertNotRegex(readme, r"\S<br/>\S")
        portfolio_sentence = (
            f'The public portfolio contains {metrics["primary_reports"]} primary '
            f'reports and {metrics["conditional_briefs"]} conditional briefs—'
            f'{metrics["intelligence_products"]} intelligence products in total—'
            f'plus {metrics["accessible_figures"]} canonical accessible figures: '
            f'{metrics["evidence_figures"]} evidence figures and '
            f'{metrics["decision_figures"]} decision figures.'
        )
        self.assertIn(portfolio_sentence, normalized_readme)

    def test_agent_interface_metadata_is_supported_and_compact(self) -> None:
        agent_metadata = (ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertTrue(agent_metadata.startswith("interface:\n"))
        self.assertNotRegex(agent_metadata, r"(?m)^\s*version:")
        interface = dict(
            re.findall(r'^  ([a-z_]+): "([^"\n]*)"$', agent_metadata, re.MULTILINE)
        )
        self.assertEqual(
            list(interface),
            ["display_name", "short_description", "brand_color", "default_prompt"],
        )
        self.assertEqual(interface["display_name"], "High-Stakes Analytics & Decision Lab")
        self.assertLessEqual(len(interface["short_description"]), 30)
        self.assertRegex(interface["brand_color"], r"^#[0-9A-F]{6}$")
        self.assertLessEqual(len(interface["default_prompt"]), 128)
        self.assertIn(f"${SKILL_NAME}", interface["default_prompt"])

    def test_local_markdown_and_html_links_resolve(self) -> None:
        missing: list[str] = []
        markdown_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
        html_pattern = re.compile(r"""(?:href|src)=["']([^"']+)["']""")
        for document in ROOT.rglob("*.md"):
            content = document.read_text(encoding="utf-8")
            targets = markdown_pattern.findall(content) + html_pattern.findall(content)
            for raw_target in targets:
                target = raw_target.strip().strip("<>").split("#", 1)[0]
                if (
                    not target
                    or target.startswith(("http://", "https://", "mailto:", "data:"))
                ):
                    continue
                target = target.split(maxsplit=1)[0]
                resolved = document.parent / urllib.parse.unquote(target)
                if not resolved.exists():
                    missing.append(
                        f"{document.relative_to(ROOT)} -> {target}"
                    )
        self.assertEqual(missing, [])

    def test_every_svg_is_valid_and_accessible(self) -> None:
        failures: list[str] = []
        for svg_path in ROOT.rglob("*.svg"):
            try:
                root = ET.parse(svg_path).getroot()
            except ET.ParseError as error:
                failures.append(f"{svg_path.relative_to(ROOT)}: {error}")
                continue
            tags = {node.tag.rsplit("}", 1)[-1] for node in root.iter()}
            if "title" not in tags or "desc" not in tags:
                failures.append(
                    f"{svg_path.relative_to(ROOT)}: missing title or desc"
                )
        self.assertEqual(failures, [])
        self.assertEqual(
            _portfolio_metrics(),
            {
                "real_data_projects": 15,
                "primary_reports": 15,
                "conditional_briefs": 10,
                "intelligence_products": 25,
                "evidence_figures": 50,
                "decision_figures": 69,
                "accessible_figures": 119,
                "adaptive_routes": 4,
            },
        )
        generated_visuals = {
            "readme-hero.svg": hero_svg(),
            "report-layers.svg": report_layers_svg(),
            "adaptive-reporting-system.svg": adaptive_system_svg(),
        }
        for name, expected in generated_visuals.items():
            with self.subTest(generated_visual=name):
                self.assertEqual(
                    (ROOT / "assets" / name).read_text(encoding="utf-8"),
                    expected,
                )
        cases = build_case_examples.load_cases()
        for case in cases:
            with self.subTest(generated_case_card=case["id"]):
                self.assertEqual(
                    (
                        build_case_examples.CASE_DIR
                        / build_case_examples.card_filename(case)
                    ).read_text(encoding="utf-8"),
                    build_case_examples.case_card(case),
                )
        self.assertEqual(
            (build_case_examples.CASE_ROOT / "README.md").read_text(
                encoding="utf-8"
            ),
            build_case_examples.gallery_readme(cases),
        )
        self.assertEqual(
            (
                build_case_examples.FIGURE_DIR / "case-landscape.svg"
            ).read_text(encoding="utf-8"),
            build_case_examples.gallery_svg(cases),
        )

    def test_package_has_no_mac_metadata_or_legacy_name(self) -> None:
        forbidden_paths = [
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.name == ".DS_Store"
        ]
        self.assertEqual(forbidden_paths, [])
        legacy_hits: list[str] = []
        for path in ROOT.rglob("*"):
            if path.suffix not in {".md", ".json", ".yaml", ".yml", ".py", ".txt"}:
                continue
            if LEGACY_NAME in path.read_text(encoding="utf-8", errors="ignore"):
                legacy_hits.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(legacy_hits, [])

    def test_release_manifest_hashes_every_listed_source_file(self) -> None:
        manifest_path = ROOT / "RELEASE-MANIFEST.json"
        self.assertTrue(manifest_path.is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "1.1")
        self.assertEqual(manifest["algorithm"], "sha256")
        paths = [entry["path"] for entry in manifest["files"]]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len({path.casefold() for path in paths}))
        self.assertNotIn("RELEASE-MANIFEST.json", paths)
        for required in (
            "README.md",
            "SKILL.md",
            "scripts/verify_portfolio_reproducibility.py",
            "scripts/build_release_manifest.py",
        ):
            self.assertIn(required, paths)
        for entry in manifest["files"]:
            with self.subTest(path=entry["path"]):
                self.assertIn(entry["mode"], {"100644", "100755"})
                source = ROOT / entry["path"]
                self.assertTrue(source.is_file())
                self.assertFalse(source.is_symlink())
                self.assertEqual(
                    hashlib.sha256(source.read_bytes()).hexdigest(),
                    entry["sha256"],
                )


if __name__ == "__main__":
    unittest.main()
