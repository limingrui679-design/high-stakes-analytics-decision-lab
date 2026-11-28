"""Read Wikimedia's headerless 78-field history dump, suppress all editor identifiers."""

import bz2


def rows(src):
    # Positions follow the 2026-10 public TSV schema (Wikitech, MediaWiki history dumps).
    with bz2.open(src.get("wiki-voyages.tsv.bz2"), "rt", encoding="utf-8") as f:
        for line in f:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 78:
                raise ValueError(f"Unexpected Wikimedia TSV schema: {len(fields)}")
            if fields[2:4] != ["revision", "create"] or fields[31] != "0":
                continue
            day = fields[4][:10]
            if not "2022-01-01" <= day < "2025-01-01" or not fields[60]:
                continue
            if fields[66] == "" or fields[72] not in ("true", "false"):
                continue
            delay = fields[74]
            if fields[72] == "true" and not delay:
                continue
            reverted = int(fields[72] == "true" and 0 <= int(delay) <= 7 * 86400)
            yield (
                fields[60],
                fields[4][:19],
                int(fields[19] == "true"),
                int(fields[66]),
                int(fields[62] == "true"),
                reverted,
            )
