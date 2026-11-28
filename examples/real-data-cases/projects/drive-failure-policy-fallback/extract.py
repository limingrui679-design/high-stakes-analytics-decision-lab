"""Compress consecutive identical SMART states while retaining every observed drive-day."""

import zipfile
from datetime import date
from hashlib import blake2b
from pathlib import Path

import pandas as pd

FLAGS = ["smart_5_raw", "smart_187_raw", "smart_197_raw", "smart_198_raw"]


def rows(src):
    active = {}
    keys = {}

    def packed(serial, record):
        start, end, model, signal, failed = record
        anon = keys.setdefault(
            serial, blake2b(serial.encode(), digest_size=7, person=b"DriveCase").hexdigest()
        )
        return f"{anon}/{start}", anon, start, end, model, *signal, failed

    for period in src.names("data_Q*_2016.zip"):
        with zipfile.ZipFile(src.get(period)) as archive:
            for entry in sorted(
                x for x in archive.namelist() if x.endswith(".csv") and Path(x).name[:4] == "2016"
            ):
                day = Path(entry).stem
                with archive.open(entry) as f:
                    df = pd.read_csv(
                        f, usecols=lambda c: c in {"serial_number", "model", "failure", *FLAGS}
                    )
                for c in FLAGS:
                    if c not in df:
                        df[c] = -1
                    # Ordered values: missing, zero, one, two to nine, ten or more.
                    v = df[c].fillna(-1)
                    df[c] = ((v >= 0).astype("int8") + (v >= 1) + (v >= 2) + (v >= 10) - 1).astype(
                        "int8"
                    )
                if df.serial_number.duplicated().any():
                    raise ValueError(f"Duplicate serial on {day}")
                seen = set()
                for serial, model, failure, *signal in df[
                    ["serial_number", "model", "failure", *FLAGS]
                ].itertuples(index=False, name=None):
                    seen.add(serial)
                    old = active.get(serial)
                    s = tuple(signal)
                    if (
                        old
                        and old[2] == model
                        and old[3] == s
                        and old[4] == 0
                        and (date.fromisoformat(day) - date.fromisoformat(old[1])).days == 1
                    ):
                        active[serial] = (old[0], day, model, s, int(failure))
                    else:
                        if old:
                            yield packed(serial, old)
                        active[serial] = (day, day, model, s, int(failure))
                for serial in sorted(active.keys() - seen):
                    yield packed(serial, active.pop(serial))
    for serial in sorted(active):
        yield packed(serial, active[serial])
