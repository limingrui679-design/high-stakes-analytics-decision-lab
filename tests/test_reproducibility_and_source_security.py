from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import stat
import sys
import tempfile
import unittest
import warnings
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
SHARED_DIR = ROOT / "examples/real-data-cases/projects/_shared"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SHARED_DIR))

import build_tailored_source_snapshots as snapshot_builder  # noqa: E402
import safe_external_io as safe_io  # noqa: E402
import verify_portfolio_reproducibility as reproducibility  # noqa: E402


class ReproducibilityAndSourceSecurityTests(unittest.TestCase):
    def test_https_policy_rejects_unsafe_urls_and_bounds_responses(self) -> None:
        for url in (
            "http://example.com/data.csv",
            "file:///tmp/data.csv",
            "https://user:secret@example.com/data.csv",
            "https://localhost/data.csv",
            "https://127.0.0.1/data.csv",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    safe_io.ensure_https_url(url)
        self.assertEqual(safe_io.HttpsOnlyRedirectHandler.max_redirections, 5)
        handler = safe_io.HttpsOnlyRedirectHandler()
        request = safe_io.urllib.request.Request("https://example.com/start")
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            handler.redirect_request(
                request,
                io.BytesIO(),
                302,
                "Found",
                {},
                "http://example.com/downgrade",
            )

        class PublicSocket:
            def getpeername(self):
                return ("93.184.216.34", 443)

        class Response(io.BytesIO):
            def __init__(self, payload: bytes, final_url: str) -> None:
                super().__init__(payload)
                self.headers: dict[str, str] = {}
                self._final_url = final_url
                self.fp = SimpleNamespace(
                    raw=SimpleNamespace(_sock=PublicSocket())
                )

            def geturl(self) -> str:
                return self._final_url

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()

        opener = SimpleNamespace(
            open=lambda *args, **kwargs: Response(b"1234", "https://example.com/final")
        )
        public_addresses = frozenset({"93.184.216.34"})
        with (
            mock.patch.object(
                safe_io,
                "_resolve_public_addresses",
                return_value=public_addresses,
            ),
            mock.patch.object(
                safe_io.urllib.request,
                "build_opener",
                return_value=opener,
            ),
        ):
            with self.assertRaisesRegex(ValueError, "exceeds 3 bytes"):
                safe_io.read_https_bytes(
                    "https://example.com/data",
                    maximum_bytes=3,
                    attempts=1,
                )

        with (
            mock.patch.object(
                safe_io,
                "_resolve_public_addresses",
                return_value=public_addresses,
            ),
            mock.patch.object(safe_io.urllib.request, "build_opener", return_value=opener),
            mock.patch.object(
                safe_io.time,
                "monotonic",
                side_effect=[0.0, 0.0, 2.0],
            ),
        ):
            with self.assertRaisesRegex(TimeoutError, "total time limit"):
                safe_io.read_https_bytes(
                    "https://example.com/data",
                    timeout=1,
                    attempts=1,
                )

        downgraded = SimpleNamespace(
            open=lambda *args, **kwargs: Response(b"ok", "http://example.com/final")
        )
        with (
            mock.patch.object(
                safe_io,
                "_resolve_public_addresses",
                return_value=public_addresses,
            ),
            mock.patch.object(
                safe_io.urllib.request,
                "build_opener",
                return_value=downgraded,
            ),
        ):
            with self.assertRaisesRegex(ValueError, "must use HTTPS"):
                safe_io.read_https_bytes(
                    "https://example.com/data",
                    attempts=1,
                )

    def test_dns_and_connected_peer_must_both_be_public(self) -> None:
        private_answer = [
            (
                safe_io.socket.AF_INET,
                safe_io.socket.SOCK_STREAM,
                6,
                "",
                ("10.0.0.7", 443),
            )
        ]
        with mock.patch.object(
            safe_io.socket,
            "getaddrinfo",
            return_value=private_answer,
        ):
            with self.assertRaisesRegex(ValueError, "non-public IP"):
                safe_io._resolve_public_addresses("https://public.example/data")

        handler = safe_io.HttpsOnlyRedirectHandler()
        request = safe_io.urllib.request.Request("https://public.example/start")
        with self.assertRaisesRegex(ValueError, "Could not verify"):
            handler.redirect_request(
                request,
                io.BytesIO(),
                302,
                "Found",
                {},
                "https://cdn.example/final",
            )

        class FakeSocket:
            def getpeername(self):
                return ("127.0.0.1", 443)

        private_redirect = SimpleNamespace(
            raw=SimpleNamespace(_sock=FakeSocket())
        )
        with self.assertRaisesRegex(ValueError, "non-public peer"):
            handler.redirect_request(
                request,
                private_redirect,
                302,
                "Found",
                {},
                "https://cdn.example/final",
            )

        class Response(io.BytesIO):
            def __init__(self) -> None:
                super().__init__(b"ok")
                self.headers: dict[str, str] = {}
                self.fp = SimpleNamespace(
                    raw=SimpleNamespace(_sock=FakeSocket())
                )

            def geturl(self) -> str:
                return "https://public.example/final"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()

        opener = SimpleNamespace(open=lambda *args, **kwargs: Response())
        with (
            mock.patch.object(
                safe_io,
                "_resolve_public_addresses",
                return_value=frozenset({"93.184.216.34"}),
            ),
            mock.patch.object(
                safe_io.urllib.request,
                "build_opener",
                return_value=opener,
            ),
        ):
            with self.assertRaisesRegex(ValueError, "non-public peer"):
                safe_io.read_https_bytes(
                    "https://public.example/data",
                    attempts=1,
                )

        class UnknownPeerResponse(io.BytesIO):
            def __init__(self) -> None:
                super().__init__(b"ok")
                self.headers: dict[str, str] = {}

            def geturl(self) -> str:
                return "https://public.example/final"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()

        unknown_opener = SimpleNamespace(
            open=lambda *args, **kwargs: UnknownPeerResponse()
        )
        with (
            mock.patch.object(
                safe_io,
                "_resolve_public_addresses",
                return_value=frozenset({"93.184.216.34"}),
            ),
            mock.patch.object(
                safe_io.urllib.request,
                "build_opener",
                return_value=unknown_opener,
            ),
        ):
            with self.assertRaisesRegex(ValueError, "Could not verify"):
                safe_io.read_https_bytes(
                    "https://public.example/data",
                    attempts=1,
                )

    def test_retry_timeout_is_one_global_deadline(self) -> None:
        clock = [0.0]

        def monotonic() -> float:
            return clock[0]

        def sleep(seconds: float) -> None:
            clock[0] += seconds

        opening = mock.Mock(side_effect=OSError("slow upstream"))
        with (
            mock.patch.object(safe_io.time, "monotonic", side_effect=monotonic),
            mock.patch.object(safe_io.time, "sleep", side_effect=sleep),
            mock.patch.object(safe_io, "open_https_stream", opening),
        ):
            with self.assertRaisesRegex(TimeoutError, "total time limit"):
                safe_io.read_https_bytes(
                    "https://example.com/data",
                    timeout=2.5,
                    attempts=3,
                )
        self.assertEqual(opening.call_count, 2)

    def test_curl_fallback_keeps_protocol_redirect_and_size_guards(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "payload.bin"

            def fake_run(command, **kwargs):
                output = Path(command[command.index("--output") + 1])
                headers = Path(command[command.index("--dump-header") + 1])
                output.write_bytes(b"bounded")
                headers.write_text("HTTP/1.1 200 OK\r\n\r\n", encoding="ascii")
                return SimpleNamespace(
                    stdout="200\nhttps://example.com/source",
                    stderr="",
                )

            with (
                mock.patch.object(
                    safe_io,
                    "_resolve_public_addresses",
                    return_value=frozenset({"93.184.216.34"}),
                ),
                mock.patch.object(
                    safe_io.subprocess,
                    "run",
                    side_effect=fake_run,
                ) as run,
            ):
                observed = safe_io.download_https_with_curl(
                    "https://example.com/source",
                    target,
                    maximum_bytes=10,
                )
            self.assertEqual(observed, 7)
            self.assertEqual(target.read_bytes(), b"bounded")
            command = run.call_args.args[0]
            self.assertTrue(Path(command[0]).is_absolute())
            self.assertEqual(Path(command[0]).name, "curl")
            self.assertIn("=https", command)
            self.assertEqual(command[command.index("--max-redirs") + 1], "0")
            self.assertEqual(command[command.index("--max-filesize") + 1], "10")
            self.assertIn("--retry-max-time", command)
            self.assertIn("--resolve", command)

    def test_curl_validates_each_redirect_before_following(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "payload.bin"
            calls = []

            def fake_run(command, **kwargs):
                calls.append(command)
                output = Path(command[command.index("--output") + 1])
                headers = Path(command[command.index("--dump-header") + 1])
                if len(calls) == 1:
                    output.write_bytes(b"")
                    headers.write_text(
                        "HTTP/1.1 302 Found\r\n"
                        "Location: https://cdn.example/final\r\n\r\n",
                        encoding="ascii",
                    )
                    return SimpleNamespace(
                        stdout="302\nhttps://example.com/source",
                        stderr="",
                    )
                output.write_bytes(b"final")
                headers.write_text("HTTP/1.1 200 OK\r\n\r\n", encoding="ascii")
                return SimpleNamespace(
                    stdout="200\nhttps://cdn.example/final",
                    stderr="",
                )

            with (
                mock.patch.object(
                    safe_io,
                    "_resolve_public_addresses",
                    return_value=frozenset({"93.184.216.34"}),
                ) as resolver,
                mock.patch.object(safe_io.subprocess, "run", side_effect=fake_run),
            ):
                observed = safe_io.download_https_with_curl(
                    "https://example.com/source",
                    target,
                    maximum_bytes=10,
                )
            self.assertEqual(observed, 5)
            self.assertEqual(target.read_bytes(), b"final")
            self.assertEqual(len(calls), 2)
            self.assertGreaterEqual(resolver.call_count, 4)

    def test_zip_policy_rejects_path_links_duplicates_and_resource_bombs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            unsafe = root / "unsafe.zip"
            with zipfile.ZipFile(unsafe, "w") as archive:
                archive.writestr("../escape.txt", b"x")
            with self.assertRaisesRegex(ValueError, "Unsafe ZIP member path"):
                with safe_io.open_safe_zip(unsafe):
                    pass

            linked = root / "linked.zip"
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(linked, "w") as archive:
                archive.writestr(info, "target")
            with self.assertRaisesRegex(ValueError, "Symbolic-link"):
                with safe_io.open_safe_zip(linked):
                    pass

            duplicate = root / "duplicate.zip"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(duplicate, "w") as archive:
                    archive.writestr("same.txt", b"a")
                    archive.writestr("same.txt", b"b")
            with self.assertRaisesRegex(ValueError, "Duplicate ZIP member"):
                with safe_io.open_safe_zip(duplicate):
                    pass

            canonical = root / "canonical.zip"
            with zipfile.ZipFile(canonical, "w") as archive:
                archive.writestr("Data.csv", b"a")
                archive.writestr("data.csv", b"b")
            with self.assertRaisesRegex(ValueError, "Canonical ZIP member"):
                with safe_io.open_safe_zip(canonical):
                    pass

            windows_path = root / "windows-path.zip"
            with zipfile.ZipFile(windows_path, "w") as archive:
                archive.writestr("C:\\escape.txt", b"x")
            with self.assertRaisesRegex(ValueError, "Unsafe ZIP member path"):
                with safe_io.open_safe_zip(windows_path):
                    pass

            unsupported = root / "unsupported.zip"
            with zipfile.ZipFile(
                unsupported,
                "w",
                compression=zipfile.ZIP_BZIP2,
            ) as archive:
                archive.writestr("data.csv", b"a,b\n1,2\n")
            with self.assertRaisesRegex(ValueError, "Unsupported ZIP compression"):
                with safe_io.open_safe_zip(unsupported):
                    pass

            many = root / "many.zip"
            with zipfile.ZipFile(many, "w") as archive:
                archive.writestr("a", b"1")
                archive.writestr("b", b"2")
            limits = safe_io.ZipLimits(maximum_members=1)
            with self.assertRaisesRegex(ValueError, "limit is 1"):
                with safe_io.open_safe_zip(many, limits=limits):
                    pass

            large_member = root / "member.zip"
            with zipfile.ZipFile(large_member, "w") as archive:
                archive.writestr("data", b"12345")
            limits = safe_io.ZipLimits(maximum_member_bytes=4)
            with self.assertRaisesRegex(ValueError, "member exceeds 4 bytes"):
                with safe_io.open_safe_zip(large_member, limits=limits):
                    pass

            total = root / "total.zip"
            with zipfile.ZipFile(total, "w") as archive:
                archive.writestr("a", b"123")
                archive.writestr("b", b"456")
            limits = safe_io.ZipLimits(maximum_total_uncompressed_bytes=5)
            with self.assertRaisesRegex(ValueError, "uncompressed content exceeds 5"):
                with safe_io.open_safe_zip(total, limits=limits):
                    pass

            ratio = root / "ratio.zip"
            with zipfile.ZipFile(
                ratio,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:
                archive.writestr("zeros", b"0" * 10_000)
            limits = safe_io.ZipLimits(maximum_expansion_ratio=2.0)
            with self.assertRaisesRegex(ValueError, "expansion ratio"):
                with safe_io.open_safe_zip(ratio, limits=limits):
                    pass

            limits = safe_io.ZipLimits(maximum_archive_bytes=1)
            with self.assertRaisesRegex(ValueError, "archive is"):
                with safe_io.open_safe_zip(large_member, limits=limits):
                    pass

    def test_nested_zip_and_source_builder_lock_fixtures(self) -> None:
        inner_buffer = io.BytesIO()
        with zipfile.ZipFile(inner_buffer, "w") as inner:
            inner.writestr("table.csv", "key,value\na,3\n")
        outer_buffer = io.BytesIO()
        with zipfile.ZipFile(outer_buffer, "w") as outer:
            outer.writestr("inner.zip", inner_buffer.getvalue())
        outer_buffer.seek(0)
        with safe_io.open_safe_zip(outer_buffer) as outer:
            nested = safe_io.read_zip_member(outer, "inner.zip")
        with safe_io.open_safe_zip(io.BytesIO(nested)) as inner:
            self.assertEqual(
                safe_io.read_zip_member(inner, "table.csv"),
                b"key,value\na,3\n",
            )

        nested_budget = safe_io.ArchiveBudget(
            maximum_depth=2,
            maximum_members=2,
            maximum_total_uncompressed_bytes=len(inner_buffer.getvalue()) + 22,
        )
        outer_buffer.seek(0)
        with safe_io.open_safe_zip(
            outer_buffer,
            budget=nested_budget,
            depth=1,
        ) as outer:
            nested = safe_io.read_zip_member(outer, "inner.zip")
        with safe_io.open_safe_zip(
            io.BytesIO(nested),
            budget=nested_budget,
            depth=2,
        ) as inner:
            safe_io.read_zip_member(inner, "table.csv")
        with self.assertRaisesRegex(ValueError, "depth 3"):
            with safe_io.open_safe_zip(
                io.BytesIO(nested),
                budget=nested_budget,
                depth=3,
            ):
                pass

        lodes_payload = b"w_geocode,C000\n250250001001001,2\n250250001001002,3\n"
        compressed = gzip.compress(lodes_payload, mtime=0)
        with mock.patch.object(snapshot_builder, "_request", return_value=compressed):
            jobs, source_lock = snapshot_builder._lodes_jobs(2019)
        self.assertEqual(jobs, {"25025000100": 5})
        self.assertEqual(source_lock["sha256"], hashlib.sha256(compressed).hexdigest())
        self.assertEqual(source_lock["decompressed_sha256"], hashlib.sha256(lodes_payload).hexdigest())
        self.assertEqual(
            source_lock["output_fields"],
            ["geoid", "year", "workplace_jobs"],
        )

        response = b"date,category,requests\n2023-01-01T00:00:00.000,Street,4\n"
        with mock.patch.object(snapshot_builder, "_request", return_value=response):
            rows, source_locks = snapshot_builder._socrata_daily("Chicago", 2023)
        self.assertEqual(rows[0]["requests"], 4)
        self.assertEqual(len(source_locks), 4)
        self.assertTrue(all(item["sha256"] == hashlib.sha256(response).hexdigest() for item in source_locks))
        self.assertTrue(all(item["records"] == 1 for item in source_locks))

        with (
            mock.patch.object(snapshot_builder, "SOCRATA_QUERY_LIMIT", 1),
            mock.patch.object(snapshot_builder, "_request", return_value=response),
        ):
            with self.assertRaisesRegex(ValueError, "paginate"):
                snapshot_builder._socrata_daily("Chicago", 2023)

        with mock.patch.object(snapshot_builder, "MAX_GZIP_UNCOMPRESSED_BYTES", 5):
            with mock.patch.object(
                snapshot_builder,
                "_request",
                return_value=gzip.compress(b"123456", mtime=0),
            ):
                with self.assertRaisesRegex(ValueError, "decompressed bytes"):
                    snapshot_builder._lodes_jobs(2019)

    def test_bike_and_opportunity_zone_builders_use_offline_locked_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)

            def fake_bike_download(url: str, destination: Path) -> None:
                destination.parent.mkdir(parents=True, exist_ok=True)
                year_month = destination.name[3:9]
                timestamp = f"{year_month[:4]}-{year_month[4:]}-01 08:00:00"
                body = (
                    "started_at,ended_at,start_station_id,start_station_name,"
                    "start_lat,start_lng,end_station_id,end_station_name,end_lat,end_lng\n"
                    f"{timestamp},{timestamp},A1,Alpha,40,-74,B1,Beta,41,-73\n"
                )
                with zipfile.ZipFile(
                    destination,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                ) as archive:
                    archive.writestr(destination.stem.removesuffix(".csv") + ".csv", body)

            with mock.patch.object(snapshot_builder, "PROJECTS", project_root):
                with mock.patch.object(
                    snapshot_builder,
                    "_download",
                    side_effect=fake_bike_download,
                ):
                    with redirect_stdout(io.StringIO()):
                        snapshot_builder.build_bike()
            bike_target = (
                project_root
                / "bike-demand-operations/data/raw/citibike-jc-2021-station-hour.csv"
            )
            self.assertEqual(len(bike_target.read_text().splitlines()) - 1, 24)
            bike_lock = json.loads(
                bike_target.with_suffix(".source-lock.json").read_text()
            )
            self.assertEqual(len(bike_lock["files"]), 12)
            self.assertTrue(
                all(len(item["sha256"]) == 64 for item in bike_lock["files"])
            )

            def fake_workbook_download(url: str, destination: Path) -> None:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(b"reviewed workbook fixture")

            def fake_acs(year: int):
                row = {
                    "B01003_E001": "100",
                    "B17001_E001": "90",
                    "B17001_E002": "10",
                    "B19013_E001": "60000",
                    "B25064_E001": "1500",
                    "B23025_E003": "70",
                    "B23025_E005": "4",
                }
                if year == 2019:
                    row["B25064_E001"] = "-666666666"
                lock = {
                    "name": f"acs-{year}.dat",
                    "url": f"https://example.com/acs-{year}.dat",
                    "sha256": str(year)[-1] * 64,
                    "bytes": 10,
                }
                return {"25025000100": row}, [lock]

            def fake_lodes(year: int):
                lock = {
                    "publisher": "U.S. Census Bureau LEHD",
                    "version": str(year),
                    "name": f"lodes-{year}.csv.gz",
                    "url": f"https://example.com/lodes-{year}.csv.gz",
                    "sha256": str(year)[-1] * 64,
                    "bytes": 10,
                    "decompressed_sha256": str(year)[-2] * 64,
                    "decompressed_bytes": 20,
                    "output_fields": ["geoid", "year", "workplace_jobs"],
                }
                return {"25025000100": year}, lock

            workbook_rows = [
                ["State/Territory", "Census Tract Number"],
                ["Massachusetts", "25025000100"],
            ]
            with mock.patch.object(snapshot_builder, "PROJECTS", project_root):
                with mock.patch.object(
                    snapshot_builder,
                    "_download",
                    side_effect=fake_workbook_download,
                ), mock.patch.object(
                    snapshot_builder,
                    "_xlsx_first_sheet",
                    return_value=workbook_rows,
                ), mock.patch.object(
                    snapshot_builder,
                    "_acs_tract",
                    side_effect=fake_acs,
                ), mock.patch.object(
                    snapshot_builder,
                    "_lodes_jobs",
                    side_effect=fake_lodes,
                ):
                    with redirect_stdout(io.StringIO()):
                        snapshot_builder.build_opportunity_zone()
            qoz_target = (
                project_root
                / "opportunity-zone-policy-evaluation/data/raw/"
                "massachusetts-qoz-tract-panel.csv"
            )
            self.assertEqual(len(qoz_target.read_text().splitlines()) - 1, 2)
            qoz_lock = json.loads(qoz_target.with_suffix(".source-lock.json").read_text())
            self.assertEqual(len(qoz_lock["lodes_files"]), 2)
            self.assertEqual(qoz_lock["lodes_years"], [2018, 2019])
            with qoz_target.open(newline="", encoding="utf-8") as handle:
                qoz_rows = list(csv.DictReader(handle))
            self.assertEqual(qoz_rows[1]["median_gross_rent"], "")
            self.assertEqual(
                qoz_rows[1]["median_gross_rent_source_code"],
                "-666666666",
            )
            self.assertEqual(
                qoz_lock["acs_special_value_policy"]["counts"],
                [
                    {
                        "field": "median_gross_rent",
                        "source_code": "-666666666",
                        "count": 1,
                    }
                ],
            )

    def test_sas_decoder_missing_and_subnormal_values_are_normalized(self) -> None:
        self.assertEqual(
            snapshot_builder._normalized_sas_numeric(float("nan")),
            ("", "missing_or_non_finite"),
        )
        self.assertEqual(
            snapshot_builder._normalized_sas_numeric(5.397605e-79),
            (0.0, "xport_subnormal_normalized_to_zero"),
        )
        self.assertEqual(snapshot_builder._normalized_sas_numeric(3.15), (3.15, ""))

    def test_nport_and_social_builders_use_offline_locked_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nport = root / "nport.zip"
            holdings = [
                {
                    "ACCESSION_NUMBER": "A1",
                    "CURRENCY_VALUE": "100",
                    "IS_RESTRICTED_SECURITY": "Y" if index == 0 else "N",
                    "FAIR_VALUE_LEVEL": "3" if index == 1 else "1",
                    "ASSET_CAT": "CASH" if index == 2 else "EC",
                    "ISSUER_CUSIP": f"CUSIP{index}",
                }
                for index in range(10)
            ]

            def tsv(rows: list[dict[str, str]]) -> str:
                fields = list(rows[0])
                values = ["\t".join(fields)]
                values.extend("\t".join(row[field] for field in fields) for row in rows)
                return "\n".join(values) + "\n"

            with zipfile.ZipFile(nport, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(
                    "SUBMISSION.tsv",
                    tsv([{"ACCESSION_NUMBER": "A1", "REPORT_DATE": "2025-12-31"}]),
                )
                archive.writestr(
                    "REGISTRANT.tsv",
                    tsv([{"ACCESSION_NUMBER": "A1", "REGISTRANT_NAME": "Fund Co"}]),
                )
                archive.writestr(
                    "FUND_REPORTED_INFO.tsv",
                    tsv(
                        [
                            {
                                "ACCESSION_NUMBER": "A1",
                                "NET_ASSETS": "2000000",
                                "REDEMPTION_FLOW_MON1": "100",
                                "REDEMPTION_FLOW_MON2": "200",
                                "REDEMPTION_FLOW_MON3": "300",
                                "SERIES_ID": "S1",
                                "SERIES_NAME": "Series",
                            }
                        ]
                    ),
                )
                archive.writestr("FUND_REPORTED_HOLDING.tsv", tsv(holdings))
            with mock.patch.object(snapshot_builder, "PROJECTS", root):
                with redirect_stdout(io.StringIO()):
                    snapshot_builder.build_nport(nport)
            nport_target = root / "sec-nport-filing-review/data/raw/sec-nport-2025q4-fund-risk.csv"
            self.assertEqual(len(nport_target.read_text().splitlines()) - 1, 1)
            self.assertEqual(
                json.loads(nport_target.with_suffix(".source-lock.json").read_text())["sha256"],
                hashlib.sha256(nport.read_bytes()).hexdigest(),
            )

            social = root / "social.csv"
            social.write_text(
                "treatment,p2004,voted,hh_id\n"
                "Control,yes,yes,H1\n"
                "Control,no,no,H2\n"
                "Neighbors,yes,yes,H3\n"
                "Neighbors,no,yes,H4\n",
                encoding="utf-8",
            )
            with mock.patch.object(snapshot_builder, "PROJECTS", root):
                with redirect_stdout(io.StringIO()):
                    snapshot_builder.build_social(social, accepted_terms=True)
            social_lock = json.loads(
                (
                    root
                    / "social-norm-field-experiment/data/raw/external-source-lock.json"
                ).read_text()
            )
            self.assertEqual(social_lock["source_records"], 4)
            with self.assertRaisesRegex(SystemExit, "accept-isps-terms"):
                snapshot_builder.build_social(social, accepted_terms=False)

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

    def test_release_manifest_supports_verified_no_git_source_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.txt"
            payload.write_text("verified\n", encoding="utf-8")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            manifest = {
                "schema_version": "1.1",
                "release": "1.0.3",
                "algorithm": "sha256",
                "files": [
                    {"path": "payload.txt", "mode": "100644", "sha256": digest}
                ],
            }
            (root / "RELEASE-MANIFEST.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            self.assertEqual(
                reproducibility._tracked_files(root),
                [Path("RELEASE-MANIFEST.json"), Path("payload.txt")],
            )
            extra = root / "unlisted.txt"
            extra.write_text("not in manifest\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unlisted files"):
                reproducibility._tracked_files(root)
            extra.unlink()
            if reproducibility.os.name == "posix":
                payload.chmod(0o755)
                with self.assertRaisesRegex(ValueError, "mode mismatch"):
                    reproducibility._tracked_files(root)
                payload.chmod(0o644)
            payload.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                reproducibility._tracked_files(root)

    def test_release_manifest_allows_only_recognized_tool_cache_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.txt"
            payload.write_text("verified\n", encoding="utf-8")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            manifest = {
                "schema_version": "1.1",
                "release": "1.0.3",
                "algorithm": "sha256",
                "files": [
                    {"path": "payload.txt", "mode": "100644", "sha256": digest}
                ],
            }
            (root / "RELEASE-MANIFEST.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            expected = [Path("RELEASE-MANIFEST.json"), Path("payload.txt")]

            python_cache = root / "__pycache__"
            python_cache.mkdir()
            (python_cache / "payload.cpython-313.pyc").write_bytes(b"generated cache")
            pytest_cache = root / ".pytest_cache" / "v" / "cache"
            pytest_cache.mkdir(parents=True)
            (pytest_cache / "nodeids").write_text("[]\n", encoding="utf-8")
            self.assertEqual(reproducibility._tracked_files(root), expected)

            unsupported_cache_file = python_cache / "unlisted.txt"
            unsupported_cache_file.write_text("not a Python cache\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unlisted files"):
                reproducibility._tracked_files(root)
            unsupported_cache_file.unlink()

            if reproducibility.os.name == "posix":
                cache_symlink = python_cache / "linked.cpython-313.pyc"
                cache_symlink.symlink_to(payload)
                with self.assertRaisesRegex(ValueError, "unlisted files"):
                    reproducibility._tracked_files(root)
                cache_symlink.unlink()

            ordinary_extra = root / "unlisted.txt"
            ordinary_extra.write_text("not in manifest\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unlisted files"):
                reproducibility._tracked_files(root)

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
