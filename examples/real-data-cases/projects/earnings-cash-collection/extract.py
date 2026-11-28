import collections
import datetime

import duckdb
from pypdf import PdfReader

CIKS = [
    320193,
    789019,
    50863,
    51143,
    104169,
    27419,
    354950,
    60667,
    18230,
    315189,
    320187,
    21344,
    77476,
    909832,
    80424,
    66740,
    858877,
    97476,
    200406,
    773840,
    40545,
    100885,
    1090727,
    1048911,
]
TAGS = {
    "NetIncomeLoss": "income",
    "NetCashProvidedByUsedInOperatingActivities": "cfo",
    "Assets": "assets",
    "StockholdersEquity": "equity",
    "AccountsReceivableNetCurrent": "receivables",
    "InventoryNet": "inventory",
}


def rows(src):
    raw = src.get("sec-facts.parquet")
    doc = PdfReader(src.get("apple-fy2023-10k.pdf"))
    text = " ".join(doc.pages[40].extract_text().split()).lower()
    if "48% and 23%" not in text or "vendor non-trade receivables" not in text:
        raise ValueError("Audited note anchor changed")
    db = duckdb.connect()
    ciks = [f"CIK{c:010}" for c in CIKS]
    columns = """source_folder, accn, form, filed, "end", start, item, CAST(val_dec AS DOUBLE)"""
    # Parameterize all data paths and values. Scan projected numeric columns
    # with the source's point-in-time accession, form and filing date intact.
    q = f"""SELECT DISTINCT {columns} FROM read_parquet(?) WHERE substr(source_folder,1,13) IN (SELECT unnest(?))
         AND item IN (SELECT unnest(?)) AND form IN ('10-K','10-K/A') AND unit_type='USD' AND val_dec IS NOT NULL ORDER BY 1,4,2,5,7"""
    candidates = collections.defaultdict(lambda: collections.defaultdict(set))
    for issuer, accn, form, filed, end, start, tag, x in db.execute(
        q, [str(raw), ciks, list(TAGS)]
    ).fetchall():
        if not end or not filed or not "2008" <= end[:4] <= "2025":
            continue
        if tag in ("NetIncomeLoss", "NetCashProvidedByUsedInOperatingActivities"):
            if not start:
                continue
            length = (datetime.date.fromisoformat(end) - datetime.date.fromisoformat(start)).days
            if not 320 <= length <= 390:
                continue
        elif start:
            continue
        if not (
            end <= filed
            and (datetime.date.fromisoformat(filed) - datetime.date.fromisoformat(end)).days <= 1200
        ):
            continue
        candidates[issuer, accn, form, filed, end][TAGS[tag]].add(x)
    fields = list(TAGS.values())
    for (issuer, accn, form, filed, end), v in sorted(candidates.items()):
        values = [next(iter(v[k])) / 1e6 if len(v[k]) == 1 else "" for k in fields]
        if v["income"] and v["cfo"]:
            yield f"{issuer}/{accn}/{end}", issuer[:13], accn, form, filed, end, *values
