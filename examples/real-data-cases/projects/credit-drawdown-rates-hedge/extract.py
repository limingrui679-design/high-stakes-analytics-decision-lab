"""Derive aligned weekly NAV total returns from issuer NAV and ex-date distributions."""

import csv
from collections import defaultdict
from datetime import datetime, timedelta
from math import prod

from lxml import etree


def workbook(path):
    # SpreadsheetML contains malformed unescaped ampersands in legal prose.
    # Parse only the two named, well-formed data tables, preserving all numeric bytes.
    body = path.read_bytes()
    sheets = {}
    for name in ["Historical", "Distributions"]:
        key = b'<ss:Worksheet ss:Name="' + name.encode() + b'">'
        block = body.split(key, 1)[1].split(b"</ss:Worksheet>", 1)[0]
        parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
        xml = etree.fromstring(
            b'<ss:Worksheet xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">'
            + block
            + b"</ss:Worksheet>",
            parser=parser,
        )
        sheets[name] = [
            [cell.findtext("{*}Data", default="") for cell in r.findall("{*}Cell")]
            for r in xml.findall(".//{*}Row")
        ]

    def day(s):
        return datetime.strptime(s, "%b %d, %Y").date()

    nav = {
        day(r[0]): float(r[1])
        for r in sheets["Historical"][1:]
        if len(r) >= 2 and r[1] not in ("", "--")
    }
    distributions = defaultdict(float)
    for r in sheets["Distributions"][1:]:
        if len(r) >= 4 and r[1] not in ("", "--"):
            distributions[day(r[1])] += float(r[3])
    dates = sorted(nav)
    return {
        t: (nav[t] + distributions.get(t, 0)) / nav[p] - 1
        for p, t in zip(dates, dates[1:], strict=False)
    }


def rows(src):
    def monthly(file, datecol, series):
        with src.get(file).open() as f:
            return {r[datecol][:7]: float(r[series]) for r in csv.DictReader(f) if r[series]}

    spread = monthly("fed-gz.csv", "date", "gz_spread")
    treasury = monthly("fed-gs10.csv", "observation_date", "GS10")

    def monthly_change(at, lookup):
        previous = (at.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        current = at.strftime("%Y-%m")
        return (
            round(100 * (lookup[current] - lookup[previous]), 5)
            if current in lookup and previous in lookup
            else ""
        )

    funds = ["LQD", "IEF", "SHY", "TLT"]
    daily = {k: workbook(src.get("ishares-" + k + ".xls")) for k in funds}
    shared = set.intersection(*(set(s) for s in daily.values()))
    grouped = defaultdict(list)
    for t in sorted(shared):
        if 2004 <= t.year <= 2025:
            grouped[t + timedelta(days=4 - t.weekday())].append(t)
    for end, ds in sorted(grouped.items()):
        if any(abs(daily[k][t]) > 0.3 for k in funds for t in ds):
            raise ValueError(f"Inspect possible share split or distribution adjustment at {end}")
        yield (
            end,
            len(ds),
            *(round(prod(1 + daily[k][t] for t in ds) - 1, 10) for k in funds),
            monthly_change(end, spread),
            monthly_change(end, treasury),
        )
