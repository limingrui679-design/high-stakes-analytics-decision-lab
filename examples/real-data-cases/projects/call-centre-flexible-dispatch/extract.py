import calendar
import csv
import io
import zipfile
from datetime import datetime


def seconds(s):
    h, m, s = map(int, s.split(":"))
    return h * 3600 + m * 60 + s


def rows(src):
    for name in calendar.month_name[1:]:
        with zipfile.ZipFile(src.get(name + "Txt.ZIP")) as z:
            for member in sorted(z.namelist()):
                if not member.lower().endswith(".txt") or "/" in member:
                    continue
                table = csv.reader(
                    io.TextIOWrapper(z.open(member), encoding="latin1"), delimiter="\t"
                )
                header = next(table)
                for fields in table:
                    # Twelve publisher rows use spaces between priority and service type.
                    if len(fields) == len(header) - 1 and len(fields[3].split()) == 2:
                        fields[3:4] = fields[3].split()
                    row = dict(zip(header, fields, strict=True))
                    date = datetime.strptime(row["date"], "%y%m%d").date()
                    if date.weekday() not in (6, 0, 1, 2, 3):
                        continue
                    entry = seconds(row["q_start"])
                    if entry == 0 and row["outcome"] == "AGENT":
                        entry = seconds(row["ser_start"])
                    wait = int(row["q_time"])
                    service = int(row["ser_time"])
                    if (
                        not 8 * 3600 <= entry < 13 * 3600
                        or row["outcome"] not in ("AGENT", "HANG")
                        or wait < 0
                    ):
                        continue
                    if row["outcome"] == "AGENT" and service <= 0:
                        continue
                    key = f"{date}/{row['vru+line']}/{row['call_id']}"
                    yield (
                        key,
                        date.isoformat(),
                        entry,
                        row["type"].strip(),
                        wait,
                        int(row["outcome"] == "AGENT"),
                        service if service > 0 else "",
                    )
