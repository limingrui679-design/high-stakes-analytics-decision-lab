"""Replay actual map versions and publish dependency repairs in SQLite WAL transactions."""

import hashlib
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

from applied_metrics import figure, result


def signature(way, nodes):
    if not way or not way[0]:
        return None
    return hashlib.sha256("|".join(f"{n}:{nodes.get(n)}" for n in way[1]).encode()).hexdigest()[:24]


def apply_raw(row, nodes, ways):
    kind = row["kind"]
    if kind == "header":
        return
    key = int(row["id"])
    target = nodes if kind == "node" else ways
    if row["op"] == "delete":
        target.pop(key, None)
    elif kind == "node":
        nodes[key] = (int(row["x"]), int(row["y"]))
    else:
        ways[key] = (bool(int(row["road"])), tuple(map(int, row["refs"].split())))


def snapshot(ways, nodes):
    return {w: signature(v, nodes) for w, v in ways.items() if v[0]}


class Interrupted(Exception):
    pass


def evaluate(rows, p, seed, telemetry=None):
    nodes = {}
    ways = {}
    truthnodes = {}
    truthways = {}
    edits = defaultdict(list)
    for row in rows:
        stage = row["stage"]
        if stage == "base":
            apply_raw(row, nodes, ways)
        elif stage == "oracle":
            apply_raw(row, truthnodes, truthways)
        else:
            edits[int(row["seq"])].append(row)
    geom = snapshot(ways, nodes)
    base = len(geom)
    rev = defaultdict(set)
    for w, (_, refs) in ways.items():
        for n in refs:
            rev[n].add(w)
    counts = Counter()
    per = {}
    seq0 = min(edits) - 1
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "geo.sqlite"
        db = sqlite3.connect(path)
        reader = sqlite3.connect(path)
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
        CREATE TABLE road(id INTEGER PRIMARY KEY, geometry TEXT NOT NULL);
        CREATE TABLE version(seq INTEGER NOT NULL);
        CREATE TABLE history(id INTEGER, seq INTEGER, geometry TEXT, PRIMARY KEY(id,seq)) WITHOUT ROWID;
        CREATE TABLE way_node(way INTEGER,node INTEGER,PRIMARY KEY(way,node)) WITHOUT ROWID;
        CREATE INDEX parent_way ON way_node(node,way);
        """)
        db.execute("INSERT INTO version VALUES (?)", (seq0,))
        db.executemany("INSERT INTO road VALUES (?,?)", geom.items())
        db.executemany(
            "INSERT INTO history VALUES (?,?,?)", ((k, seq0, g) for k, g in geom.items())
        )
        db.executemany(
            "INSERT OR IGNORE INTO way_node VALUES (?,?)",
            ((w, n) for w, (_, refs) in ways.items() for n in refs),
        )
        db.commit()
        baseline = sqlite3.connect(Path(folder) / "baseline.sqlite")
        baseline.execute("CREATE TABLE road(id INTEGER PRIMARY KEY, geometry TEXT NOT NULL)")

        def publish(s, updates, direct, crash=False):
            seq = db.execute("SELECT seq FROM version").fetchone()[0]
            if s <= seq:
                return "duplicate"
            if s != seq + 1:
                return "out-of-order"
            try:
                with db:
                    for w in sorted(direct):
                        db.execute("DELETE FROM way_node WHERE way=?", (w,))
                        if w in ways:
                            db.executemany(
                                "INSERT OR IGNORE INTO way_node VALUES (?,?)",
                                ((w, n) for n in ways[w][1]),
                            )
                    for key, new in updates.items():
                        if new is None:
                            db.execute("DELETE FROM road WHERE id=?", (key,))
                        else:
                            db.execute("INSERT OR REPLACE INTO road VALUES (?,?)", (key, new))
                        db.execute("INSERT INTO history VALUES (?,?,?)", (key, s, new))
                    db.execute("UPDATE version SET seq=?", (s,))
                    if reader.execute("SELECT seq FROM version").fetchone()[0] != seq:
                        raise ValueError("Reader saw an uncommitted version")
                    if crash:
                        raise Interrupted
            except Interrupted:
                return "rolled back"
            return "committed"

        for seq, delta in sorted(edits.items()):
            affected = set()
            direct = set()
            changed_nodes = set()
            if telemetry is not None:
                step_start = time.perf_counter_ns()
            for r in delta:
                kind = r["kind"]
                if kind == "header":
                    continue
                key = int(r["id"])
                if kind == "node":
                    before = nodes.get(key)
                    apply_raw(r, nodes, ways)
                    if before != nodes.get(key):
                        changed_nodes.add(key)
                        affected.update(
                            v[0]
                            for v in db.execute("SELECT way FROM way_node WHERE node=?", (key,))
                        )
                else:
                    old = ways.get(key)
                    if old:
                        for n in old[1]:
                            rev[n].discard(key)
                    apply_raw(r, nodes, ways)
                    if key in ways:
                        for n in ways[key][1]:
                            rev[n].add(key)
                    affected.add(key)
                    direct.add(key)
            for n in changed_nodes:
                affected.update(rev[n])
            batch = {w: signature(ways.get(w), nodes) for w in sorted(affected)}
            if telemetry is not None:
                telemetry["repair_calculation_ms"].append(
                    (time.perf_counter_ns() - step_start) / 1e6
                )
                step_start = time.perf_counter_ns()
            expected = snapshot(ways, nodes)
            if telemetry is not None:
                with baseline:
                    baseline.execute("DELETE FROM road")
                    baseline.executemany("INSERT INTO road VALUES (?,?)", expected.items())
                telemetry["full_materialize_and_commit_ms"].append(
                    (time.perf_counter_ns() - step_start) / 1e6
                )
            updates = {w: v for w, v in batch.items() if geom.get(w) != v}
            indirect = set(updates) - direct
            if seq == min(edits) or (indirect and not counts["indirect_crash"]):
                previous = dict(reader.execute("SELECT * FROM road"))
                if (
                    publish(seq + 1, updates, direct) != "out-of-order"
                    or publish(seq, updates, direct, True) != "rolled back"
                ):
                    raise ValueError("Failed interruption or gap check")
                db.close()
                if telemetry is not None:
                    restart = time.perf_counter_ns()
                db = sqlite3.connect(path)
                if (
                    db.execute("SELECT seq FROM version").fetchone()[0] != seq - 1
                    or dict(db.execute("SELECT * FROM road")) != previous
                ):
                    raise ValueError("Recovery changed committed state")
                if telemetry is not None:
                    telemetry["reopen_and_verify_ms"].append(
                        (time.perf_counter_ns() - restart) / 1e6
                    )
                counts["crashes"] += 1
                counts["indirect_crash"] += int(bool(indirect))
            reader.execute("BEGIN")
            previous_sequence = reader.execute("SELECT seq FROM version").fetchone()[0]
            if telemetry is not None:
                stamp = time.perf_counter_ns()
            if (
                publish(seq, updates, direct) != "committed"
                or publish(seq, updates, direct) != "duplicate"
            ):
                raise ValueError("Unexpected commit/replay status")
            if telemetry is not None:
                telemetry["indexed_commit_ms"].append((time.perf_counter_ns() - stamp) / 1e6)
            if reader.execute("SELECT seq FROM version").fetchone()[0] != previous_sequence:
                raise ValueError("Pinned reader advanced")
            if dict(reader.execute("SELECT * FROM road")) != geom:
                raise ValueError("Pinned reader lost its historical snapshot")
            reader.commit()
            if dict(reader.execute("SELECT * FROM road")) != expected:
                raise ValueError(f"Full oracle mismatch at {seq}")
            # Each updated geometry is also retrievable at the prior version after the commit.
            for key in updates:
                record = db.execute(
                    "SELECT geometry FROM history WHERE id=? AND seq<=? ORDER BY seq DESC LIMIT 1",
                    (key, seq - 1),
                ).fetchone()
                if (record[0] if record else None) != geom.get(key):
                    raise ValueError("Historical lookup mismatch")
            if telemetry is not None:
                keys = sorted(expected)[:: max(1, len(expected) // 40)]
                for key in keys:
                    for name, conn in [
                        ("full_indexed_lookup_us", baseline),
                        ("incremental_indexed_lookup_us", reader),
                    ]:
                        tick = time.perf_counter_ns()
                        found = conn.execute(
                            "SELECT geometry FROM road WHERE id=?", (key,)
                        ).fetchone()[0]
                        elapsed = (time.perf_counter_ns() - tick) / 1000
                        if found != expected[key]:
                            raise ValueError("Benchmark lookup mismatch")
                        telemetry[name].append(elapsed)
            counts["full"] += len(expected)
            counts["indexed"] += sum(w in expected or w in geom for w in affected)
            counts["naive_misses"] += len(indirect)
            counts["writes"] += len(updates)
            geom = expected
            per[seq] = dict(
                roads=len(geom),
                indirect_only=len(indirect),
                affected=len(affected),
                changes=len(delta) - 1,
                written_geometries=len(updates),
            )
        # A second process exits mid-transaction without an orderly close.
        child = "import os,sqlite3,sys; conn=sqlite3.connect(sys.argv[1]); conn.execute('BEGIN IMMEDIATE'); conn.execute('UPDATE version SET seq=-1'); os._exit(7)"
        killed = subprocess.run([sys.executable, "-c", child, str(path)], check=False)
        if killed.returncode != 7 or db.execute("SELECT seq FROM version").fetchone()[0] != max(
            edits
        ):
            raise ValueError("Writer-process crash recovery failed")
        if telemetry is not None:
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            telemetry["versioned_storage_KiB"].append(path.stat().st_size / 1024)
            telemetry["single_current_version_storage_KiB"].append(
                (Path(folder) / "baseline.sqlite").stat().st_size / 1024
            )
        baseline.close()
        reader.close()
        db.close()
    example = snapshot(truthways, truthnodes)
    if geom != example:
        raise ValueError("Independent next-month publisher snapshot mismatch")
    return result(
        f"Across {len(edits)} consecutive real map releases, dependency-aware repair matched every full rebuild and the next independent snapshot ({len(geom):,} highway geometries). Updating only revised ways missed {counts['naive_misses']} geometry-version discrepancy.",
        {
            "Checked sequences": len(edits),
            "Final highway geometries": len(geom),
            "Interrupted transaction reopens": counts["crashes"],
        },
        [
            figure(
                "Geometry materializations over all versions",
                "Highway-way evaluations",
                {"Full rebuild": counts["full"], "Dependency closure": counts["indexed"]},
                "Counts use the same highway scope and oracle per version.",
            ),
            figure(
                "Consequences of indexing only edited ways",
                "Incorrect geometry-version pairs",
                {"Direct edits only": counts["naive_misses"], "Reverse dependency closure": 0},
                "A moved node can change its referencing road even without a new way version.",
            ),
            figure(
                "Commit and interruption checks",
                "Completed checks",
                {
                    "Pinned readers": len(edits),
                    "Duplicate replays": len(edits),
                    "Rollback and reopen": counts["crashes"],
                    "Writer process exits": 1,
                },
                "Reader snapshot checks span the commit. The writer-exit trial deliberately leaves a transaction uncommitted.",
            ),
        ],
        {
            "per_sequence": per,
            "initial_road_ways": base,
            "oracle_mismatches": 0,
            "full_recomputes": counts["full"],
            "indexed_recomputes": counts["indexed"],
            "geometry_row_writes": counts["writes"],
            "direct_only_misses": counts["naive_misses"],
            "crash_reopens": counts["crashes"],
            "writer_process_crash_checks": 1,
            "pinned_reader_checks": len(edits),
        },
        "Publish a version after reverse dependencies, updated geometries and the sequence have committed together. Keep an indexed historical lookup and periodically verify the source snapshot.",
    )
