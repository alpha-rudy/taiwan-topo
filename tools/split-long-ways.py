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

import os
import shutil
import sys
import tempfile

import osmium

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pbf_utils

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


def _process_stream(src, dst):
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
                    sys.exit(
                        f"input is not sorted (way {obj.id} after {max_way}); run osmium sort first"
                    )
                max_way = obj.id
                if len(obj.nodes) <= MAX_NODES or obj.nodes[0].ref != obj.nodes[-1].ref:
                    writer.add_way(obj)
                    continue
                refs = [n.ref for n in obj.nodes]
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
    print(
        f"split {len(replaced)} closed ways longer than {MAX_NODES} nodes into "
        f"{sum(len(v) for v in replaced.values())} pieces"
    )


def main(src, dst):
    # Fast path for sorted PBF inputs: raw-copy the contiguous node-only block
    # prefix without decompressing/recompressing millions of nodes, and only
    # decode ways/relations from the first way/relation block onward.
    if src.endswith(".pbf") and dst.endswith(".pbf"):
        blocks = pbf_utils.scan_pbf_blocks(src)
        header_blocks = [b for b in blocks if b[0] == "OSMHeader"]
        data_blocks = [b for b in blocks if b[0] == "OSMData"]
        if header_blocks and data_blocks:
            with open(src, "rb") as src_f:
                first_wr = pbf_utils.find_first_block_with_types(src_f, data_blocks, {"w", "r"})
            if first_wr > 0:
                dst_dir = os.path.dirname(os.path.abspath(dst))
                os.makedirs(dst_dir, exist_ok=True)
                tmp_dir = tempfile.mkdtemp(prefix=".split_ways_", dir=dst_dir)
                tmp_out = os.path.join(tmp_dir, "out.osm.pbf")
                try:
                    tail_in = os.path.join(tmp_dir, "tail_in.osm.pbf")
                    tail_out = os.path.join(tmp_dir, "tail_out.osm.pbf")
                    with open(src, "rb") as src_f:
                        pbf_utils.write_pbf_block_slice(
                            src_f, header_blocks[0], data_blocks, first_wr, len(data_blocks), tail_in
                        )
                    _process_stream(tail_in, tail_out)

                    tail_blocks = [b for b in pbf_utils.scan_pbf_blocks(tail_out) if b[0] == "OSMData"]
                    with open(tmp_out, "wb") as dst_f, open(src, "rb") as src_f:
                        _, h_start, _, _, h_len = header_blocks[0]
                        pbf_utils.copy_range(src_f, dst_f, h_start, h_len)
                        node_start = data_blocks[0][1]
                        node_end = data_blocks[first_wr - 1][1] + data_blocks[first_wr - 1][4]
                        pbf_utils.copy_range(src_f, dst_f, node_start, node_end - node_start)
                        if tail_blocks:
                            with open(tail_out, "rb") as tf:
                                t_start = tail_blocks[0][1]
                                t_end = tail_blocks[-1][1] + tail_blocks[-1][4]
                                pbf_utils.copy_range(tf, dst_f, t_start, t_end - t_start)
                    os.replace(tmp_out, dst)
                    return
                finally:
                    shutil.rmtree(tmp_dir, ignore_errors=True)

    _process_stream(src, dst)


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
