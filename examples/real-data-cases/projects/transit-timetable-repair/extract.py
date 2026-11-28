"""Delta-encode real consecutive GTFS schedules for one common calendar service date."""

import csv
import io
import zipfile
from collections import defaultdict

SERVICE_DATE = "20241122"
FILES = [
    "20241021",
    "20241024",
    "20241025",
    "20241027",
    "20241031",
    "20241101",
    "20241107",
    "20241112",
    "20241113",
    "20241115",
]
ROUTES = {
    "Red",
    "Orange",
    "Blue",
    "Green-B",
    "Green-C",
    "Green-D",
    "Green-E",
    "Mattapan",
    "1",
    "39",
    "66",
    "77",
    "SL1",
    "SL3",
}


def seconds(t):
    h, m, s = map(int, t.split(":"))
    return 3600 * h + 60 * m + s


def feed(path):
    with zipfile.ZipFile(path) as z:

        def table(name):
            return csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8-sig"))

        services = {
            r["service_id"]
            for r in table("calendar.txt")
            if r["start_date"] <= SERVICE_DATE <= r["end_date"] and r["friday"] == "1"
        }
        for r in table("calendar_dates.txt"):
            if r["date"] == SERVICE_DATE:
                if r["exception_type"] == "1":
                    services.add(r["service_id"])
                else:
                    services.discard(r["service_id"])
        trips = {
            r["trip_id"]: r["route_id"]
            for r in table("trips.txt")
            if r["service_id"] in services
            and (r["route_id"] in ROUTES or r["route_id"].startswith("Shuttle-"))
        }
        stops = {r["stop_id"]: r["parent_station"] or r["stop_id"] for r in table("stops.txt")}
        times = defaultdict(list)
        for r in table("stop_times.txt"):
            if r["trip_id"] in trips and r["departure_time"] and r["arrival_time"]:
                times[r["trip_id"]].append(
                    (
                        int(r["stop_sequence"]),
                        stops[r["stop_id"]],
                        seconds(r["arrival_time"]),
                        seconds(r["departure_time"]),
                        r["pickup_type"] != "1",
                        r["drop_off_type"] != "1",
                    )
                )
        edges = {}
        for trip, rows in times.items():
            rows.sort()
            for a, b in zip(rows, rows[1:], strict=False):
                if b[2] < a[3]:
                    raise ValueError("A scheduled connection runs backwards")
                edges[(trip, a[0])] = (a[1], b[1], a[3], b[2], int(a[4]), int(b[5]))
        if not services or not edges:
            raise ValueError("Shared date not supported by published calendars")
        return edges


def rows(src):
    prev = {}
    for version in FILES:
        new = feed(src.get("mbta-" + version + ".zip"))
        yield version + "/header", version, "header", "", 0, "", "", 0, 0, 0, 0
        for key in sorted(set(new) | set(prev)):
            if prev.get(key) == new.get(key):
                continue
            op = "drop" if key not in new else "put"
            yield (
                version + "/" + str(key),
                version,
                op,
                key[0],
                key[1],
                *(new.get(key) or prev[key]),
            )
        prev = new
