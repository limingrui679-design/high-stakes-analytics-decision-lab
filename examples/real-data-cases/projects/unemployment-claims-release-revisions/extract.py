"""Use state tables from original dated Department of Labor releases."""

import re
from datetime import datetime, timedelta

JURISDICTIONS = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "District of Columbia",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Puerto Rico",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virgin Islands",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
]
CANONICAL = {name.lower().replace(" ", ""): name for name in JURISDICTIONS}


def extract_release(path):
    from pypdf import PdfReader

    issued = datetime.strptime(path.stem.removeprefix("dol-"), "%m%d%y").date()
    pdf = PdfReader(path)
    for i in [4, 5, 3, 6, 7, 8]:
        if i >= len(pdf.pages):
            continue
        text = pdf.pages[i].extract_text(extraction_mode="layout")
        if (
            "Alabama" in text
            and "Initial Claims" in text
            and "Advance" in text
            and "Prior W" in text
        ):
            break
    else:
        raise ValueError(f"Missing state advance table in {path.name}")
    m = re.search(
        r"Initial Claims (?:Filed )?(?:During|For) Week End(?:ed|ing)\s+([A-Za-z]+)\s+(\d{1,2})",
        text,
        re.I,
    )
    if not m:
        raise ValueError((path.name, text[:400]))
    month = datetime.strptime(m[1][:3], "%b").month
    end = issued.replace(month=month, day=int(m[2]))
    if end > issued:
        end = end.replace(year=end.year - 1)
    if not 1 <= (issued - end).days <= 10:
        raise ValueError((path.name, end))
    rows = {}
    for line in text.splitlines():
        hit = re.match(
            r"^\s*([A-Za-z][A-Za-z. ]*?)\s*[\*]*\s{2,}(-?[\d,]+)\s+(-?[\d,]+)\s+(-?[\d,]+)(?:\s|$)",
            line,
        )
        if hit and not hit[1].upper().startswith(("TOTAL", "U.S.", "US TOTAL", "NATIONAL")):
            key = re.sub("[^a-z]", "", hit[1].lower())
            name = CANONICAL.get(key)
            if name is None or name in rows:
                raise ValueError((path.name, hit[1]))
            a, b, c = [int(hit[i].replace(",", "")) for i in [2, 3, 4]]
            if a - b != c:
                raise ValueError((path.name, name, a, b, c))
            rows[name] = (a, b)
    if len(rows) != 53:
        raise ValueError(f"{path.name}: {len(rows)} states/territories")
    return end, issued, rows


def rows(src):
    names = src.names("dol-*.pdf")
    paths = [src.get(n) for n in names]
    # Parsing is read-only. Keep the replay independent of worker completion order.
    records = sorted(map(extract_release, paths))
    indexed = {d: (issued, r) for d, issued, r in records}
    for week, first, table in records:
        nxt = indexed.get(week + timedelta(days=7))
        if not nxt:
            continue
        second, revised = nxt
        if set(table) != set(revised):
            raise ValueError((first, second, set(table) - set(revised), set(revised) - set(table)))
        for name, (x, _) in sorted(table.items()):
            yield f"{week}/{name}", week.isoformat(), name, first, second, x, revised[name][1]
