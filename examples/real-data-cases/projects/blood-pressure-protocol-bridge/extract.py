"""Paired adult measurements in the NHANES blood-pressure methodology study."""

import pandas as pd


def rows(src):
    pieces = [
        pd.read_sas(src.get(n + ".XPT")).set_index("SEQN") for n in ("BPX_J", "BPXO_J", "DEMO_J")
    ]
    df = pieces[0].join(pieces[1], how="inner").join(pieces[2], how="inner").sort_index()
    for person, r in df.iterrows():
        manual = [r[f"BPXSY{i}"] for i in range(1, 4) if pd.notna(r[f"BPXSY{i}"])]
        auto = [r[f"BPXOSY{i}"] for i in range(1, 4) if pd.notna(r[f"BPXOSY{i}"])]
        if (
            r.RIDAGEYR >= 18
            and len(manual) >= 2
            and len(auto) >= 2
            and r.WTMEC2YR > 0
            and pd.notna(r.BPAOMNTS)
        ):
            yield (
                int(person),
                int(r.RIDAGEYR),
                int(r.SDMVSTRA),
                int(r.SDMVPSU),
                round(r.WTMEC2YR, 6),
                int(r.BPAOMNTS),
                len(manual),
                len(auto),
                round(sum(manual) / len(manual), 6),
                round(sum(auto) / len(auto), 6),
            )
