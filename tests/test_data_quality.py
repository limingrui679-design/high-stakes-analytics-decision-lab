from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import data_quality as dq  # noqa: E402
from data_quality import (  # noqa: E402
    apply_cleaning_plan,
    build_cleaning_plan,
    load_contract,
    profile_dataset,
    read_dataset,
    render_quality_report,
    sha256_file,
    write_quality_bundle,
)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class DataQualityGateTests(unittest.TestCase):
    def _contract(self, path: Path) -> dict:
        payload = {
            "schema_version": "1.0",
            "dataset_name": "dirty-case",
            "intended_use": "predictive",
            "grain": "one row per case",
            "required_columns": ["case_id", "amount", "event_date", "segment"],
            "primary_key": ["case_id"],
            "date_columns": ["event_date"],
            "numeric_columns": ["amount"],
            "categorical_columns": {"segment": ["A", "B"]},
            "target_column": "segment",
            "feature_columns": ["amount"],
            "forbidden_columns": [],
            "direct_identifier_columns": ["email"],
            "sensitive_columns": [],
            "missing_tokens": ["", "NA", "N/A", "null"],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return load_contract(path, dataset_name="dirty-case")

    def test_dirty_data_blocks_analysis_and_never_echoes_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "dirty.csv"
            _write_csv(
                source,
                [
                    {
                        "case_id": "1",
                        "email": "person@example.com",
                        "amount": " 10 ",
                        "event_date": "2024-01-01",
                        "segment": "A",
                    },
                    {
                        "case_id": "1",
                        "email": "person@example.com",
                        "amount": " 10 ",
                        "event_date": "2024-01-01",
                        "segment": "A",
                    },
                    {
                        "case_id": "2",
                        "email": "NA",
                        "amount": "bad",
                        "event_date": "2999-01-01",
                        "segment": "C",
                    },
                    {
                        "case_id": "3",
                        "email": "other@example.com",
                        "amount": "1000",
                        "event_date": "not-a-date",
                        "segment": "B",
                    },
                ],
            )
            profile = profile_dataset(source, self._contract(root / "contract.json"))
            codes = {item["code"] for item in profile["findings"]}
            self.assertEqual(profile["quality_gate"]["status"], "blocked")
            self.assertIn("primary_key_duplicates", codes)
            self.assertIn("invalid_numeric", codes)
            self.assertIn("invalid_datetime", codes)
            self.assertIn("future_dates", codes)
            self.assertIn("invalid_category", codes)
            self.assertIn("direct_identifiers_present", codes)
            self.assertNotIn("person@example.com", json.dumps(profile))

    def test_plan_separates_safe_actions_from_user_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.csv"
            _write_csv(
                source,
                [
                    {
                        "case_id": "1",
                        "email": "a@example.com",
                        "amount": " 10 ",
                        "event_date": "2024-01-01",
                        "segment": "A",
                    },
                    {
                        "case_id": "1",
                        "email": "a@example.com",
                        "amount": " 10 ",
                        "event_date": "2024-01-01",
                        "segment": "A",
                    },
                ],
            )
            contract = self._contract(root / "contract.json")
            profile = profile_dataset(source, contract)
            plan = build_cleaning_plan(profile)
            modes = {item["action"]: item["mode"] for item in plan["actions"]}
            self.assertEqual(modes["trim_whitespace"], "safe_auto")
            self.assertEqual(modes["remove_exact_duplicates"], "requires_confirmation")
            self.assertEqual(modes["drop_columns"], "requires_confirmation")

            original_hash = sha256_file(source)
            with mock.patch.object(
                dq,
                "sha256_file",
                side_effect=[original_hash, "changed-during-read"],
            ):
                with self.assertRaisesRegex(ValueError, "cleaning copy"):
                    apply_cleaning_plan(source, profile, plan, root / "changed-during-read")
            safe_output = root / "safe"
            log = apply_cleaning_plan(source, profile, plan, safe_output)
            self.assertEqual(sha256_file(source), original_hash)
            self.assertEqual(log["after"]["rows"], 2)
            self.assertEqual(log["after"]["columns"], 5)
            self.assertEqual(log["quality_gate_after"], "blocked")

            action_ids = {
                item["action"]: item["id"]
                for item in plan["actions"]
                if item["executable"]
            }
            approved_output = root / "approved"
            approved_log = apply_cleaning_plan(
                source,
                profile,
                plan,
                approved_output,
                approvals=[
                    action_ids["remove_exact_duplicates"],
                    action_ids["drop_columns"],
                ],
            )
            self.assertEqual(approved_log["after"], {"rows": 1, "columns": 4})
            self.assertEqual(approved_log["quality_gate_after"], "ready")
            with (
                approved_output / "processed/analysis.csv"
            ).open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertNotIn("email", rows[0])
            self.assertEqual(rows[0]["amount"], "10")

    def test_non_executable_and_hash_mismatch_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.csv"
            _write_csv(
                source,
                [
                    {
                        "case_id": "1",
                        "email": "",
                        "amount": "bad",
                        "event_date": "2024-01-01",
                        "segment": "A",
                    }
                ],
            )
            profile = profile_dataset(source, self._contract(root / "contract.json"))
            plan = build_cleaning_plan(profile)
            manual = next(item for item in plan["actions"] if not item["executable"])
            with self.assertRaisesRegex(ValueError, "cannot be executed generically"):
                apply_cleaning_plan(
                    source,
                    profile,
                    plan,
                    root / "manual",
                    approvals=[manual["id"]],
                )
            source.write_text(source.read_text() + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                apply_cleaning_plan(source, profile, plan, root / "changed")

    def test_bundle_contains_machine_readable_and_accessible_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.csv"
            _write_csv(
                source,
                [
                    {
                        "case_id": "1",
                        "amount": "10",
                        "event_date": "2024-01-01",
                        "segment": "A",
                    },
                    {
                        "case_id": "2",
                        "amount": "20",
                        "event_date": "2024-01-02",
                        "segment": "B",
                    },
                ],
            )
            output = root / "quality"
            profile, _ = write_quality_bundle(
                source,
                output,
                contract=self._contract(root / "contract.json"),
            )
            self.assertEqual(profile["quality_gate"]["status"], "ready")
            for relative in (
                "data-quality-report.md",
                "data-quality-report.json",
                "data-contract.json",
                "cleaning-plan.json",
                "figures/data-quality-overview.svg",
            ):
                self.assertTrue((output / relative).is_file(), relative)
            svg = ET.parse(output / "figures/data-quality-overview.svg").getroot()
            tags = {item.tag.rsplit("}", 1)[-1] for item in svg.iter()}
            self.assertIn("title", tags)
            self.assertIn("desc", tags)

    def test_default_contract_pauses_and_user_missing_tokens_are_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.csv"
            _write_csv(source, [{"id": "1", "status": "NA"}])

            inferred = profile_dataset(
                source,
                load_contract(None, dataset_name="input"),
            )
            self.assertEqual(
                inferred["quality_gate"]["status"],
                "needs_user_confirmation",
            )
            self.assertEqual(inferred["columns"]["status"]["missing_count"], 1)

            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "dataset_name": "input",
                        "intended_use": "descriptive",
                        "grain": "one row per record",
                        "primary_key": ["id"],
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            declared = profile_dataset(
                source,
                load_contract(contract_path, dataset_name="input"),
            )
            self.assertEqual(declared["columns"]["status"]["missing_count"], 0)
            self.assertEqual(declared["quality_gate"]["status"], "ready")

            omitted_path = root / "contract-with-inferred-sentinels.json"
            omitted_path.write_text(
                json.dumps(
                    {
                        "dataset_name": "input",
                        "intended_use": "descriptive",
                        "grain": "one row per record",
                        "primary_key": ["id"],
                    }
                ),
                encoding="utf-8",
            )
            omitted_contract = load_contract(omitted_path, dataset_name="input")
            omitted_profile = profile_dataset(source, omitted_contract)
            omitted_plan = build_cleaning_plan(omitted_profile)
            missing_action = next(
                item
                for item in omitted_plan["actions"]
                if item["action"] == "normalize_missing_tokens"
            )
            self.assertEqual(missing_action["mode"], "requires_confirmation")

    def test_duplicate_headers_and_ragged_rows_are_blocked_without_value_loss(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "ambiguous.csv"
            source.write_text("id,id,value\n1,2,3,4\n", encoding="utf-8")
            rows, fields, metadata = read_dataset(source)
            self.assertEqual(len(fields), 4)
            self.assertEqual(rows[0]["id"], "1")
            self.assertEqual(rows[0]["id__duplicate_2"], "2")
            self.assertEqual(rows[0]["__extra_column_1"], "4")
            self.assertIn("duplicate_header", metadata["shape_warnings"])
            self.assertIn("extra_fields_without_header", metadata["shape_warnings"])

            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "dataset_name": "ambiguous",
                        "intended_use": "descriptive",
                        "grain": "one row per record",
                        "primary_key": ["id"],
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            profile = profile_dataset(
                source,
                load_contract(contract_path, dataset_name="ambiguous"),
            )
            self.assertEqual(profile["quality_gate"]["status"], "blocked")
            self.assertIn(
                "ambiguous_schema",
                {item["code"] for item in profile["findings"]},
            )

    def test_value_level_privacy_signals_force_confirmation_without_echoing_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "privacy.csv"
            rows = [
                {
                    "record_key": "r1",
                    "opaque_a": "+1 (212) 555-0182",
                    "opaque_b": "123-45-6789",
                    "opaque_c": "110105199001011234",
                    "opaque_d": "10.1.2.3",
                    "opaque_e": "10 Main Street",
                    "opaque_f": "123456789",
                    "cohort_date": "1988-02-03",
                    "cohort_alt": "02/03/1988",
                    "note": "diabetes treatment",
                },
                {
                    "record_key": "r2",
                    "opaque_a": "+1 (212) 555-0183",
                    "opaque_b": "219099999",
                    "opaque_c": "110105199202022345",
                    "opaque_d": "10.1.2.4",
                    "opaque_e": "11 Main Street",
                    "opaque_f": "219099999",
                    "cohort_date": "1990-04-05",
                    "cohort_alt": "04/05/1990",
                    "note": "asthma medication",
                },
            ]
            _write_csv(source, rows)
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "dataset_name": "privacy",
                        "intended_use": "descriptive",
                        "grain": "one row per record",
                        "primary_key": ["record_key"],
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            profile = profile_dataset(
                source,
                load_contract(contract_path, dataset_name="privacy"),
            )
            codes = {item["code"] for item in profile["findings"]}
            self.assertEqual(profile["quality_gate"]["status"], "needs_user_confirmation")
            self.assertIn("direct_identifiers_present", codes)
            self.assertIn("sensitive_fields_present", codes)
            self.assertIn("small_sample_reidentification_risk", codes)
            self.assertIn("cohort_date", profile["privacy"]["sensitive_columns_detected"])
            self.assertIn("cohort_alt", profile["privacy"]["sensitive_columns_detected"])
            self.assertIn("note", profile["privacy"]["sensitive_columns_detected"])
            for field in ("opaque_c", "opaque_f"):
                numeric = profile["columns"][field]["numeric"]
                self.assertTrue(
                    {"minimum", "q1", "median", "q3", "maximum"}.isdisjoint(numeric)
                )
            date_summary = profile["columns"]["cohort_date"]["datetime"]
            self.assertNotIn("minimum", date_summary)
            self.assertNotIn("maximum", date_summary)
            rendered = json.dumps(profile, ensure_ascii=False)
            for row in rows:
                for field, value in row.items():
                    if field != "record_key":
                        self.assertNotIn(value, rendered)

    def test_input_resource_limits_and_jsonl_streaming_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            oversized = root / "oversized.csv"
            oversized.write_text("a\n12\n", encoding="utf-8")
            with mock.patch.object(dq, "MAX_INPUT_FILE_BYTES", 2):
                with self.assertRaisesRegex(ValueError, "Input file"):
                    read_dataset(oversized)

            too_many_rows = root / "rows.csv"
            too_many_rows.write_text("a\n1\n2\n", encoding="utf-8")
            with mock.patch.object(dq, "MAX_DATASET_ROWS", 1):
                with self.assertRaisesRegex(ValueError, "exceeds 1 rows"):
                    read_dataset(too_many_rows)

            too_many_columns = root / "columns.csv"
            too_many_columns.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
            with mock.patch.object(dq, "MAX_DATASET_COLUMNS", 2):
                with self.assertRaisesRegex(ValueError, "2 columns"):
                    read_dataset(too_many_columns)

            long_cell = root / "cell.csv"
            long_cell.write_text("a\nabcd\n", encoding="utf-8")
            with mock.patch.object(dq, "MAX_CELL_CHARACTERS", 3):
                with self.assertRaisesRegex(ValueError, "contains 4 characters"):
                    read_dataset(long_cell)

            nested = root / "nested.json"
            nested.write_text('[{"a":{"b":{"c":1}}}]', encoding="utf-8")
            with mock.patch.object(dq, "MAX_JSON_DEPTH", 3):
                with self.assertRaisesRegex(ValueError, "nesting depth"):
                    read_dataset(nested)

            array = root / "array.json"
            array.write_text('[{"a":1}]', encoding="utf-8")
            with mock.patch.object(dq, "MAX_IN_MEMORY_JSON_BYTES", 2):
                with self.assertRaisesRegex(ValueError, "Convert it to JSONL"):
                    read_dataset(array)

            jsonl = root / "rows.jsonl"
            jsonl.write_text('{"a":1}\n{"a":2}\n', encoding="utf-8")
            rows, fields, metadata = read_dataset(jsonl)
            self.assertEqual(fields, ["a"])
            self.assertTrue(metadata["streaming_input"])
            self.assertEqual(list(rows), list(rows))
            self.assertEqual(len(rows), 2)

            contract_path = root / "stable-contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "dataset_name": "rows",
                        "intended_use": "descriptive",
                        "grain": "one row per record",
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.object(
                dq,
                "sha256_file",
                side_effect=["before", "after"],
            ):
                with self.assertRaisesRegex(ValueError, "changed while"):
                    profile_dataset(
                        jsonl,
                        load_contract(contract_path, dataset_name="rows"),
                    )

    def test_predictive_contract_blocks_target_leakage_and_missing_features(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "prediction.csv"
            _write_csv(source, [{"id": "1", "outcome": "1"}])
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "dataset_name": "prediction",
                        "intended_use": "predictive",
                        "grain": "one row per entity before outcome",
                        "primary_key": ["id"],
                        "target_column": "outcome",
                        "feature_columns": ["outcome", "missing_feature"],
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            profile = profile_dataset(
                source,
                load_contract(contract_path, dataset_name="prediction"),
            )
            codes = {item["code"] for item in profile["findings"]}
            self.assertEqual(profile["quality_gate"]["status"], "blocked")
            self.assertIn("target_feature_overlap", codes)
            self.assertIn("feature_columns_absent", codes)

    def test_declared_numeric_ranges_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "ranges.csv"
            _write_csv(source, [{"id": "1", "age": "-1"}, {"id": "2", "age": "45"}])
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "dataset_name": "ranges",
                        "intended_use": "descriptive",
                        "grain": "one row per person",
                        "primary_key": ["id"],
                        "numeric_columns": ["age"],
                        "numeric_ranges": {"age": {"minimum": 0, "maximum": 120}},
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            profile = profile_dataset(
                source,
                load_contract(contract_path, dataset_name="ranges"),
            )
            self.assertEqual(
                profile["columns"]["age"]["numeric"]["outside_declared_range_count"],
                1,
            )
            self.assertIn(
                "numeric_range_violation",
                {item["code"] for item in profile["findings"]},
            )

    def test_safe_canonicalization_preserves_large_numbers_and_date_precision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "precision.csv"
            _write_csv(
                source,
                [
                    {
                        "id": "1",
                        "amount": "9007199254740993.000",
                        "period": "2024",
                    },
                    {
                        "id": "2",
                        "amount": "0.1000000000000000001",
                        "period": "2024-05",
                    },
                ],
            )
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "dataset_name": "precision",
                        "intended_use": "descriptive",
                        "grain": "one row per period",
                        "primary_key": ["id"],
                        "numeric_columns": ["amount"],
                        "date_columns": ["period"],
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            contract = load_contract(contract_path, dataset_name="precision")
            profile = profile_dataset(source, contract)
            plan = build_cleaning_plan(profile)
            apply_cleaning_plan(source, profile, plan, root / "prepared")
            with (root / "prepared/processed/analysis.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["amount"], "9007199254740993")
            self.assertEqual(rows[1]["amount"], "0.1000000000000000001")
            self.assertEqual([row["period"] for row in rows], ["2024", "2024-05"])

    def test_tampered_plan_safe_action_approval_and_source_collision_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            processed = root / "processed"
            processed.mkdir()
            source = processed / "analysis.csv"
            _write_csv(source, [{"id": " 1 "}])
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "dataset_name": "collision",
                        "intended_use": "descriptive",
                        "grain": "one row per record",
                        "primary_key": ["id"],
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            contract = load_contract(contract_path, dataset_name="collision")
            profile = profile_dataset(source, contract)
            plan = build_cleaning_plan(profile)
            safe_id = next(
                item["id"] for item in plan["actions"] if item["mode"] == "safe_auto"
            )
            with self.assertRaisesRegex(ValueError, "Only requires_confirmation"):
                apply_cleaning_plan(
                    source,
                    profile,
                    plan,
                    root / "elsewhere",
                    approvals=[safe_id],
                )

            tampered = json.loads(json.dumps(plan))
            tampered["actions"][0]["action"] = "drop_columns"
            with self.assertRaisesRegex(ValueError, "no longer match"):
                apply_cleaning_plan(source, profile, tampered, root / "elsewhere")

            with self.assertRaisesRegex(ValueError, "raw source path"):
                apply_cleaning_plan(source, profile, plan, root)

    def test_markdown_report_escapes_dynamic_table_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.csv"
            _write_csv(source, [{"id": "1", "risk|score": "3"}])
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "dataset_name": "input",
                        "intended_use": "descriptive",
                        "grain": "one row per record | verified",
                        "primary_key": ["id"],
                        "numeric_columns": ["risk|score"],
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            profile = profile_dataset(
                source,
                load_contract(contract_path, dataset_name="input"),
            )
            report = render_quality_report(profile, build_cleaning_plan(profile))
            self.assertIn("record \\| verified", report)
            self.assertIn("<code>risk&#124;score</code>", report)

    def test_command_line_profile_and_prepare_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "input.csv"
            _write_csv(source, [{"id": "1", "amount": " 10 "}])
            contract = root / "contract.json"
            contract.write_text(
                json.dumps(
                    {
                        "dataset_name": "input",
                        "intended_use": "descriptive",
                        "grain": "one row per record",
                        "primary_key": ["id"],
                        "numeric_columns": ["amount"],
                        "missing_tokens": [""],
                    }
                ),
                encoding="utf-8",
            )
            readiness = root / "readiness"
            profile_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "profile_dataset.py"),
                    str(source),
                    "--contract",
                    str(contract),
                    "--output-dir",
                    str(readiness),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(profile_result.returncode, 0, profile_result.stderr)
            self.assertIn("Quality gate: ready", profile_result.stdout)

            prepared = root / "prepared"
            prepare_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "prepare_dataset.py"),
                    str(source),
                    "--quality-report",
                    str(readiness / "data-quality-report.json"),
                    "--cleaning-plan",
                    str(readiness / "cleaning-plan.json"),
                    "--output-dir",
                    str(prepared),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(prepare_result.returncode, 0, prepare_result.stderr)
            self.assertIn("Quality gate after: ready", prepare_result.stdout)
            self.assertTrue((prepared / "processed/analysis.csv").is_file())

    def test_contract_rejects_conflicts_and_unknown_or_unbounded_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = {
                "dataset_name": "invalid-contract",
                "intended_use": "descriptive",
                "grain": "one row per record",
                "missing_tokens": [""],
            }
            invalid_contracts = [
                (
                    {**base, "numeric_columns": ["value"], "date_columns": ["value"]},
                    "conflicting declared types",
                ),
                (
                    {**base, "thresholds": {"misspelled_threshold": 0.1}},
                    "unknown keys",
                ),
                (
                    {
                        **base,
                        "numeric_ranges": {
                            "value": {"minimum": 0, "maximum": 10**1000}
                        },
                    },
                    "finite numeric",
                ),
            ]
            for index, (payload, message) in enumerate(invalid_contracts):
                with self.subTest(case=index):
                    path = root / f"invalid-{index}.json"
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        load_contract(path, dataset_name="invalid-contract")


if __name__ == "__main__":
    unittest.main()
