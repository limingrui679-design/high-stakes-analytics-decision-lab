from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import build_tailored_source_snapshots as snapshot_builder  # noqa: E402
import verify_portfolio_reproducibility as reproducibility  # noqa: E402


class ReproducibilityAndSourceSecurityTests(unittest.TestCase):
    def test_semantic_json_limits_float_and_hash_exemptions(self) -> None:
        expected = {
            "metric": 0.123456789,
            "count": 12,
            "status": "do_not_deploy",
            "analytical_results_sha256": "a" * 64,
            "source_manifest_sha256": "c" * 64,
        }
        observed = {
            **expected,
            "metric": expected["metric"] + 5e-9,
            "analytical_results_sha256": "b" * 64,
        }
        failures, normalized_hashes = reproducibility._semantic_json_differences(
            expected,
            observed,
        )
        self.assertEqual(failures, [])
        self.assertEqual(normalized_hashes, 1)

        outside_tolerance = {**observed, "metric": expected["metric"] + 1e-5}
        failures, _ = reproducibility._semantic_json_differences(
            expected,
            outside_tolerance,
        )
        self.assertTrue(failures)

        changed_source_hash = {**observed, "source_manifest_sha256": "d" * 64}
        failures, _ = reproducibility._semantic_json_differences(
            expected,
            changed_source_hash,
        )
        self.assertTrue(failures)

        changed_integer_type = {**observed, "count": 12.0}
        failures, _ = reproducibility._semantic_json_differences(
            expected,
            changed_integer_type,
        )
        self.assertTrue(failures)

    def test_report_hash_normalization_is_label_scoped(self) -> None:
        first = "Result SHA-256: `" + "a" * 64 + "`"
        second = "Result SHA-256: `" + "b" * 64 + "`"
        self.assertEqual(
            reproducibility._normalize_report_hashes(first),
            reproducibility._normalize_report_hashes(second),
        )
        source_first = "Source SHA-256: `" + "a" * 64 + "`"
        source_second = "Source SHA-256: `" + "b" * 64 + "`"
        self.assertNotEqual(
            reproducibility._normalize_report_hashes(source_first),
            reproducibility._normalize_report_hashes(source_second),
        )

    def test_safe_xlsx_parser_accepts_minimal_workbook_and_rejects_dtd(self) -> None:
        try:
            from defusedxml.common import DTDForbidden
        except ImportError:
            self.skipTest("defusedxml is installed only for maintenance security tests")
        shared_strings = b"""<?xml version="1.0"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <si><t>State/Territory</t></si><si><t>Census Tract Number</t></si>
  <si><t>Massachusetts</t></si><si><t>25025000100</t></si>
</sst>"""
        safe_sheet = b"""<?xml version="1.0"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row><c t="s"><v>0</v></c><c t="s"><v>1</v></c></row>
    <row><c t="s"><v>2</v></c><c t="s"><v>3</v></c></row>
  </sheetData>
</worksheet>"""
        malicious_sheet = b"""<?xml version="1.0"?>
<!DOCTYPE worksheet [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData><row><c><v>&xxe;</v></c></row></sheetData>
</worksheet>"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            safe = root / "safe.xlsx"
            with zipfile.ZipFile(safe, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("xl/sharedStrings.xml", shared_strings)
                archive.writestr("xl/worksheets/sheet1.xml", safe_sheet)
            self.assertEqual(
                snapshot_builder._xlsx_first_sheet(safe),
                [
                    ["State/Territory", "Census Tract Number"],
                    ["Massachusetts", "25025000100"],
                ],
            )

            malicious = root / "malicious.xlsx"
            with zipfile.ZipFile(
                malicious,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:
                archive.writestr("xl/worksheets/sheet1.xml", malicious_sheet)
            with self.assertRaises(DTDForbidden):
                snapshot_builder._xlsx_first_sheet(malicious)

    def test_archive_paths_and_external_input_paths_are_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unsafe = root / "unsafe.xlsx"
            with zipfile.ZipFile(unsafe, "w") as archive:
                archive.writestr("../sheet1.xml", b"not used")
            with self.assertRaisesRegex(ValueError, "Unsafe XLSX member path"):
                snapshot_builder._xlsx_first_sheet(unsafe)

            source = root / "source.csv"
            source.write_text("value\n1\n", encoding="utf-8")
            self.assertEqual(
                snapshot_builder._required_input(source, "--source"),
                source.resolve(),
            )
            with self.assertRaisesRegex(SystemExit, "--source is required"):
                snapshot_builder._required_input(None, "--source")


if __name__ == "__main__":
    unittest.main()
