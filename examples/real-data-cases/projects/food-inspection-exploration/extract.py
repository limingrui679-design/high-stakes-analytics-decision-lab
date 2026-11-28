"""Build each quarter's eligible roster from licenses and prior restaurant inspections."""

import csv
import subprocess
import tempfile
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

R_EXPORT = r"""
args <- commandArgs(trailingOnly=TRUE)
x <- readRDS(file.path(args[1],"ins.Rds"))
x <- x[x$Facility_Type_Clean=="Restaurant" & !is.na(x$License) & !is.na(x$Inspection_Date), ]
write.csv(x[,c("License","Inspection_Date","Inspection_ID","Risk","criticalCount","Zip","Latitude")],file.path(args[1],"ins.csv"),row.names=FALSE,na="")
b <- readRDS(file.path(args[1],"lic.Rds"))
b <- b[b$LICENSE_DESCRIPTION=="Retail Food Establishment",]
write.csv(b[,c("LICENSE_NUMBER","DATE_ISSUED","LICENSE_TERM_START_DATE","LICENSE_TERM_EXPIRATION_DATE","LICENSE_STATUS_CHANGE_DATE","LICENSE_STATUS")],file.path(args[1],"lic.csv"),row.names=FALSE,na="")
"""


def rows(src):
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(src.get("chicago_repo.zip")) as z:
        temp = Path(tmp)
        for suffix, name in [
            ("23_food_insp_features.Rds", "ins.Rds"),
            ("11_bus_license.Rds", "lic.Rds"),
        ]:
            (temp / name).write_bytes(z.read(next(k for k in z.namelist() if k.endswith(suffix))))
        subprocess.run(["Rscript", "-e", R_EXPORT, str(temp)], check=True)
        permits = defaultdict(list)
        ins = defaultdict(list)
        with (temp / "lic.csv").open() as f:
            for r in csv.DictReader(f):
                valid = max(r["DATE_ISSUED"], r["LICENSE_TERM_START_DATE"])
                expiry = r["LICENSE_TERM_EXPIRATION_DATE"]
                if r["LICENSE_STATUS"] in ("AAC", "REV") and r["LICENSE_STATUS_CHANGE_DATE"]:
                    expiry = min(expiry, r["LICENSE_STATUS_CHANGE_DATE"])
                if valid and expiry:
                    permits[r["LICENSE_NUMBER"]].append((valid, expiry))
        with (temp / "ins.csv").open() as f:
            for r in csv.DictReader(f):
                if r["criticalCount"] != "":
                    ins[r["License"]].append(
                        (
                            r["Inspection_Date"],
                            int(float(r["Inspection_ID"])),
                            int(float(r["criticalCount"]) > 0),
                            r["Risk"],
                            r["Zip"],
                            r["Latitude"],
                        )
                    )
        for k in ins:
            ins[k].sort()
        for yr in [2012, 2013, 2014]:
            for month in [1, 4, 7, 10]:
                start = date(yr, month, 1)
                end = date(yr + (month == 10), 1 if month == 10 else month + 3, 1)
                s = start.isoformat()
                for license, records in sorted(ins.items()):
                    if not any(a <= s <= b for a, b in permits[license]):
                        continue
                    past = [x for x in records if x[0] < s]
                    if not past:
                        continue
                    then, _, crit, risk, zip_code, lat = past[-1]
                    future = next((x for x in records if s <= x[0] < end.isoformat()), None)
                    # Geographic bands are fixed before scoring, never based on outcome.
                    area = (
                        "Unlocated"
                        if not lat
                        else (
                            "South"
                            if float(lat) < 41.80
                            else "Central"
                            if float(lat) < 41.90
                            else "North"
                        )
                    )
                    yield (
                        s + "/" + license,
                        s,
                        license,
                        area,
                        risk,
                        (start - date.fromisoformat(then)).days,
                        len(past),
                        sum(x[2] for x in past),
                        crit,
                        future[2] if future else "",
                        (date.fromisoformat(future[0]) - start).days if future else "",
                    )
