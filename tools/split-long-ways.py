#!/usr/bin/env python3
"""
Split closed ways longer than tilemaker's limit into chained pieces.

tilemaker (v3) refuses any way with more than 2,000 nodes ("Way had more than
2,000 nodes"), the OSM API's own limit. The natural=nosea land polygons of the
land/sea scheme (see tools/generate_landsea.py) are not OSM data and are kept
whole, so a coastline ring can run to many thousands of nodes.

Each closed way above the limit is replaced by pieces of at most MAX_NODES
nodes that share their end nodes, so together they trace the same ring:
  - a tagged way becomes an untagged chain plus a new type=multipolygon
    relation carrying the way's tags, with every piece as an outer member;
  - every existing relation that names the way as a member names the pieces
    instead, in order and with the same role.
Open ways are left alone: they cannot become an area, and splitting a line
would repeat its label on every piece. tilemaker then fails on them loudly.

The input must be sorted (osmium sort): pieces take the ids just above the
largest way id and are written before the first relation, new relations take
the ids above the largest relation id and come last, so the output is still
sorted and tilemaker can read it without another sort.

Usage:
    python3 tools/split-long-ways.py <sorted_input.pbf> <output.pbf>
"""

import sys

import osmium

MAX_NODES = 2000


def pieces(refs):
    """Consecutive slices of refs, each at most MAX_NODES long, each starting on
    the node where the previous one ended."""
    out = []
    start = 0
    while start < len(refs) - 1:
        end = min(start + MAX_NODES, len(refs))
        out.append(refs[start:end])
        start = end - 1
    return out


def main(src, dst):
    replaced = {}      # way id -> [piece way ids]
    new_areas = []     # (tags, [piece way ids])
    pending = []       # (piece id, refs), written before the first relation
    max_way = 0
    max_rel = 0
    flushed = False
    writer = osmium.SimpleWriter(dst, overwrite=True)

    def flush_pieces():
        for wid, refs in pending:
            writer.add_way(osmium.osm.mutable.Way(id=wid, nodes=refs))
        pending.clear()

    try:
        for obj in osmium.FileProcessor(src):
            if obj.is_node():
                writer.add_node(obj)
            elif obj.is_way():
                if obj.id <= max_way:
                    sys.exit("input is not sorted (way %d after %d); run osmium sort first"
                             % (obj.id, max_way))
                max_way = obj.id
                refs = [n.ref for n in obj.nodes]
                if len(refs) <= MAX_NODES or refs[0] != refs[-1]:
                    writer.add_way(obj)
                    continue
                # Ids are assigned once every way is seen; remember the slices.
                replaced[obj.id] = pieces(refs)
                tags = {t.k: t.v for t in obj.tags}
                if tags:
                    new_areas.append((obj.id, tags))
            else:
                if not flushed:
                    assign_ids(replaced, pending, max_way)
                    flush_pieces()
                    flushed = True
                max_rel = max(max_rel, obj.id)
                if not any(m.type == "w" and m.ref in replaced for m in obj.members):
                    writer.add_relation(obj)
                    continue
                members = []
                for m in obj.members:
                    if m.type == "w" and m.ref in replaced:
                        members.extend(("w", wid, m.role) for wid in replaced[m.ref])
                    else:
                        members.append((m.type, m.ref, m.role))
                writer.add_relation(obj.replace(members=members))
        if not flushed:
            assign_ids(replaced, pending, max_way)
            flush_pieces()
        for i, (way_id, tags) in enumerate(new_areas, start=1):
            tags = dict(tags, type="multipolygon")
            members = [("w", wid, "outer") for wid in replaced[way_id]]
            writer.add_relation(osmium.osm.mutable.Relation(
                id=max_rel + i, members=members, tags=tags))
    finally:
        writer.close()
    print("split %d closed ways longer than %d nodes into %d pieces"
          % (len(replaced), MAX_NODES, sum(len(v) for v in replaced.values())))


def assign_ids(replaced, pending, max_way):
    """Turn each replaced way's slices into piece ids above max_way, in way order,
    and queue the pieces for writing."""
    next_id = max_way + 1
    for way_id in sorted(replaced):
        ids = []
        for refs in replaced[way_id]:
            pending.append((next_id, refs))
            ids.append(next_id)
            next_id += 1
        replaced[way_id] = ids


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
