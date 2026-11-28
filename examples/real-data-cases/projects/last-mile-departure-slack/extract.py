import json
import math
from datetime import datetime


def objects(path):
    """Stream top-level route values; the publisher uses bare NaN for missing times."""
    decoder = json.JSONDecoder()
    with path.open() as source:
        buf = ""
        eof = False
        started = False
        while True:
            if not buf.strip() and not eof:
                part = source.read(1 << 20)
                buf += part
                eof = not part
            buf = buf.lstrip()
            if not started:
                if not buf.startswith("{"):
                    raise ValueError("Expected route object")
                buf = buf[1:]
                started = True
            buf = buf.lstrip()
            if buf.startswith(","):
                buf = buf[1:].lstrip()
            if buf.startswith("}"):
                return
            try:
                key, n = decoder.raw_decode(buf)
                tail = buf[n:].lstrip()
                if not tail.startswith(":"):
                    raise ValueError("Missing separator")
                pos = len(buf) - len(tail) + 1
                while pos < len(buf) and buf[pos].isspace():
                    pos += 1
                value, end = decoder.raw_decode(buf, pos)
            except (ValueError, IndexError):
                if eof:
                    raise
                part = source.read(1 << 20)
                buf += part
                eof = not part
                continue
            yield key, value
            buf = buf[end:]


def rows(src):
    ds = json.loads(src.get("amazon-route_data.json").read_bytes())
    sts = ["DLA7", "DSE5", "DCH4", "DBO3"]
    ids = set()
    for st in sts:
        # Route IDs are publisher UUIDs. Select before inspecting costs or windows.
        keys = sorted(
            k
            for k, v in ds.items()
            if v["station_code"] == st
            and 45 <= len(v["stops"]) <= 145
            and v.get("route_score") == "High"
        )
        ids.update(keys[:6])
    pack = {k: v for k, v in objects(src.get("amazon-package_data.json")) if k in ids}
    order = json.loads(src.get("amazon-actual_sequences.json").read_bytes())
    for k, tt in objects(src.get("amazon-travel_times.json")):
        if k not in ids:
            continue
        route = ds[k]
        nodes = sorted(route["stops"])
        t0 = datetime.fromisoformat(route["date_YYYY_MM_DD"] + "T" + route["departure_time_utc"])
        for node in nodes:
            pkgs = pack[k].get(node, {})
            left = []
            right = []
            service = 0
            bounded = 0
            for v in pkgs.values():
                service += float(v["planned_service_time_seconds"])
                w = v["time_window"]
                if isinstance(w["start_time_utc"], str):
                    left.append(
                        int((datetime.fromisoformat(w["start_time_utc"]) - t0).total_seconds())
                    )
                if isinstance(w["end_time_utc"], str):
                    right.append(
                        int((datetime.fromisoformat(w["end_time_utc"]) - t0).total_seconds())
                    )
                bounded += int(
                    isinstance(w["start_time_utc"], str) or isinstance(w["end_time_utc"], str)
                )
            zone = route["stops"][node]["zone_id"]
            yield (
                k + "/" + node,
                k,
                route["station_code"],
                node,
                int(route["stops"][node]["type"] == "Station"),
                zone if isinstance(zone, str) else "",
                len(pkgs),
                bounded,
                round(service),
                max(left) if left else "",
                min(right) if right else "",
                order[k]["actual"][node],
                ",".join(str(math.ceil(tt[node][v])) for v in nodes),
            )
