from __future__ import annotations

import re
import unittest
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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


if __name__ == "__main__":
    unittest.main()
