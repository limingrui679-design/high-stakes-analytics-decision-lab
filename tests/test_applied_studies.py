"""Regression tests for decisions where a plausible implementation gives a different answer."""

from __future__ import annotations

import importlib.util
import itertools
import json
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "examples" / "real-data-cases" / "projects"
sys.path.insert(0, str(PROJECTS / "_shared"))


def module(slug):
    spec = importlib.util.spec_from_file_location(
        "test_study_" + slug, PROJECTS / slug / "study.py"
    )
    assert spec is not None and spec.loader is not None
    study = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(study)
    return study


class AppliedStudyTests(unittest.TestCase):
    def test_signed_threshold_switches_can_cancel(self):
        s = module("blood-pressure-protocol-bridge")
        rows = [
            (20, 1, 1, 1.0, 1, 129, 131),
            (28, 1, 2, 1.0, 1, 131, 129),
            (75, 1, 1, 1.0, 1, 139, 140),
            (78, 1, 2, 1.0, 1, 139, 139),
        ]
        up = s.survey_summary(rows, lambda r: float(r[5] < 130 <= r[6]), lambda r: r[0] < 40)
        net = s.survey_summary(rows, lambda r: int(r[6] >= 130) - int(r[5] >= 130))
        self.assertEqual(up["estimate"], 0.5)
        self.assertGreater(up["se"], 0)
        self.assertEqual(net["estimate"], 0)

    def test_off_path_shortcut_insertion_and_removal_after_midnight(self):
        s = module("transit-timetable-repair")
        start = 86400
        step = 60
        e1 = (start + 10, "one", 0, "A", "B", start + 200, 1, 1)
        e2 = (start + 20, "shortcut", 0, "A", "B", start + 100, 1, 1)

        def buckets(edges):
            out = defaultdict(list)
            for e in sorted(edges):
                out[e[0] // step * step].append(e)
            out["end"] = max(out)
            return out

        base, _ = s.scan(buckets([e1]), "A", start, 0, step)
        fast, _ = s.scan(buckets([e1, e2]), "A", start, 0, step, base, e2[0])
        self.assertEqual(fast[1]["B"], start + 100)
        labels, _, boarded = s.label_setting(s.network_index([e1]), "A", start, 0)
        self.assertTrue(s.affected((labels, boarded), [e2], start, 0))
        updated, _ = s.scan(buckets([e1]), "A", start, 0, step, fast, e2[0])
        self.assertEqual(updated[1], base[1])
        self.assertEqual(s.label_setting(s.network_index([e1, e2]), "A", start, 0)[0], fast[1])

    def test_waiting_and_vehicle_continuity_across_no_boarding_edge(self):
        s = module("transit-timetable-repair")
        start = 30
        e = [
            (35, "through", 0, "A", "B", 50, 1, 0),
            (51, "through", 1, "B", "C", 70, 0, 1),
            (40, "unreachable", 0, "B", "Z", 45, 1, 1),
        ]
        d, _, _ = s.label_setting(s.network_index(e), "A", start, 120)
        self.assertEqual(d["C"], 70)
        self.assertNotIn("B", d)
        self.assertNotIn("Z", d)

    def test_route_upper_bound_dominates_exhaustive_oracle(self):
        s = module("last-mile-departure-slack")
        mat = [[0, 9, 3, 5], [5, 0, 3, 8], [3, 7, 0, 2], [3, 4, 2, 0]]
        svc = [0, 3, 5, 3]
        lo = [0, 5, 8, 2]
        hi = [80, 38, 40, 42]
        scores = [
            s.latest([0, *perm], mat, svc, lo, hi, 48) for perm in itertools.permutations([1, 2, 3])
        ]
        feasible = [x for x in scores if x is not None]
        self.assertTrue(feasible)
        self.assertGreaterEqual(s.bound(0, mat, svc, hi, 48), max(feasible))
        self.assertIsNone(s.latest([0, 1, 2, 3], mat, svc, [0, 60, 8, 2], hi, 48))

    def test_drive_observation_gaps_cannot_connect_future_failure_to_prior_spell(self):
        s = module("drive-failure-policy-fallback")

        def row(start, end, failed):
            return dict(
                drive="d",
                model="m",
                **{"from": start},
                until=end,
                reallocated="0",
                uncorrectable="0",
                pending="-1",
                offline="0",
                failure=str(failed),
            )

        records = list(
            s.intervals([row("2016-01-01", "2016-01-05", 0), row("2016-01-08", "2016-01-12", 1)])
        )
        early = next(x for x in records if x[3] == min(v[3] for v in records))
        self.assertEqual(early[-1], 0)
        self.assertEqual(early[4], early[5])
        self.assertNotEqual(s.features([0, 0, 0, 0]), s.features([0, 0, -1, 0]))

    def test_learning_demo_is_linked_to_two_independent_public_records(self):
        p = PROJECTS / "programming-hint-design"
        m = json.loads((p / "source-manifest.json").read_text())
        self.assertEqual({s["source_id"] for s in m["sources"]}, {"csedm-itap", "refactory"})
        a = json.loads((p / "outputs/results.json").read_text())["audit"]
        self.assertLess(a["matched_count"], a["public_evaluation_rows"])
        self.assertIn("Prospective", a["planned_experiment"]["status"])
        context = (p / "learning-prototype.html").read_text()
        for key in ("counterexample", "correction", "transfer", "60 seconds", "first-attempt"):
            self.assertIn(key, context)
        self.assertNotIn("fetch(", context)

    def test_observed_load_error_is_retained_in_the_unscreened_result(self):
        p = PROJECTS / "overlapping-forecast-comparisons"
        a = json.loads((p / "outputs/results.json").read_text())["audit"]
        self.assertTrue(a["excluded_source_days"])
        self.assertTrue(
            all(x["max_input_MW"] > a["gross_error_screen_mw"] for x in a["excluded_source_days"])
        )
        self.assertLess(a["raw_unscreened_pp"], a["intervals"]["HAC"][0])
        self.assertLess(a["intervals"]["HAC"][1], 0)

    def test_versioned_geometry_changes_without_an_edited_way(self):
        s = module("versioned-road-geometry")
        nodes = {1: (0, 0), 2: (1, 1)}
        self.assertNotEqual(
            s.signature((True, (1, 2)), nodes), s.signature((True, (1, 2)), {**nodes, 2: (2, 2)})
        )
        self.assertIsNone(s.signature((False, (1, 2)), nodes))
        a = json.loads((PROJECTS / "versioned-road-geometry" / "outputs/results.json").read_text())[
            "audit"
        ]
        self.assertEqual(a["oracle_mismatches"], 0)
        self.assertGreater(a["direct_only_misses"], 0)
        self.assertEqual(a["pinned_reader_checks"], len(a["per_sequence"]))
        self.assertGreater(a["writer_process_crash_checks"], 0)

    def test_predicate_for_inclusion_at_an_inspection_cutoff(self):
        import random

        s = module("food-inspection-exploration")
        rows = [{"license": str(i), "area": "A" if i < 5 else "B"} for i in range(12)]
        selected, strata = s.offer(
            rows, {str(i): 12 - i for i in range(12)}, 4, 0.5, random.Random(5)
        )
        self.assertEqual(len({r["license"] for r in selected}), 4)
        self.assertAlmostEqual(
            sum(x["pi"] * x["eligible_after_exploitation"] for x in strata.values()), 2
        )

    def test_skipped_calendar_dates_cannot_create_a_seven_day_window(self):
        s = module("overlapping-forecast-comparisons")
        self.assertEqual(s.window({i: 1.0 for i in (0, 1, 2, 3, 4, 5, 7, 8)}, 7), {})

    def test_source_replay_stops_if_upstream_url_or_digest_changes(self):
        scripts = PROJECTS.parent / "source_tools"
        sys.path.insert(0, str(scripts))
        try:
            import replay_extract

            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                cache = root / "cache"
                cache.mkdir()
                proj = root / "example"
                proj.mkdir()
                src = cache / "file"
                src.write_text("x")
                h = replay_extract.sha256(src)
                fake = "https://example.org/new"
                (cache / "file.origin.json").write_text(
                    json.dumps({"name": "file", "url": fake, "sha256": h})
                )
                (proj / "study-design.json").write_text(
                    json.dumps({"fields": {"x": "observation"}})
                )
                (proj / "extract.py").write_text(
                    'def rows(src):\n    yield (src.get("file").read_text(),)\n'
                )
                (proj / "source-manifest.json").write_text(
                    json.dumps(
                        {
                            "sources": [
                                {
                                    "artifacts": [
                                        {
                                            "name": "file",
                                            "url": "https://example.org/original",
                                            "sha256": h,
                                        }
                                    ]
                                }
                            ]
                        }
                    )
                )
                with self.assertRaisesRegex(ValueError, "publisher input set"):
                    replay_extract.process(proj, cache, False, False)
        finally:
            sys.path.remove(str(scripts))
