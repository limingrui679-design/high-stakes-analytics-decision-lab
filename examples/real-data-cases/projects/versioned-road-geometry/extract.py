import gzip
import xml.etree.ElementTree as ET

import osmium


def pbf_entries(path):
    # All nodes, including support nodes of ways crossing the region boundary.
    for item in osmium.FileProcessor(str(path)):
        if item.is_node():
            yield "node", item.id, item.version, item.location.x, item.location.y, "", ""
        elif item.is_way():
            yield (
                "way",
                item.id,
                item.version,
                "",
                "",
                int("highway" in item.tags),
                " ".join(str(n.ref) for n in item.nodes),
            )


def rows(src):
    start = 4897
    end = 4926
    for stage, seq, name in [
        ("base", start, "monaco-260901.osm.pbf"),
        ("oracle", end, "monaco-261001.osm.pbf"),
    ]:
        source = src.get(name)
        reader = osmium.io.Reader(str(source))
        published = reader.header().get("osmosis_replication_sequence_number")
        reader.close()
        if str(seq) != published:
            raise ValueError((name, published))
        for kind, id, version, x, y, road, refs in pbf_entries(source):
            yield f"{stage}/{kind}/{id}", stage, seq, kind, id, version, "put", x, y, road, refs
    for seq in range(start + 1, end + 1):
        root = ET.fromstring(gzip.decompress(src.get(f"monaco-{seq}.osc.gz").read_bytes()))
        # Empty regional updates are still sequence boundaries.
        yield f"delta/{seq}/header", "delta", seq, "header", 0, 0, "commit", "", "", "", ""
        i = 0
        for action in root:
            for e in action:
                if e.tag not in ["node", "way"]:
                    continue
                i += 1
                id = int(e.attrib["id"])
                v = int(e.attrib["version"])
                op = "delete" if action.tag == "delete" else "put"
                coords = [
                    round(float(e.get(k)) * 1e7)
                    if k in e.attrib and op == "put" and e.tag == "node"
                    else ""
                    for k in ["lon", "lat"]
                ]
                road = (
                    int(any(t.get("k") == "highway" for t in e.findall("tag")))
                    if e.tag == "way" and op == "put"
                    else ""
                )
                refs = (
                    " ".join(t.get("ref") for t in e.findall("nd"))
                    if e.tag == "way" and op == "put"
                    else ""
                )
                yield f"delta/{seq}/{i}", "delta", seq, e.tag, id, v, op, *coords, road, refs
