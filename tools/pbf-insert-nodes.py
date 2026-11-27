#!/usr/bin/env python3
"""Insert an OSMData PBF containing only high-ID nodes into a sorted PBF without recompression.

Exits with code 0 on success, or code 2 when the fast blob-insertion preconditions
are not met (caller should fall back to `osmium merge`).
"""

import os
import shutil
import sys

from pbf_utils import (
    copy_range,
    decompress_blob,
    read_varint,
    scan_pbf_blocks,
    skip_field,
)

FALLBACK_EXIT = 2


def _read_blob(f, blob_start, blob_size):
    f.seek(blob_start)
    return decompress_blob(f.read(blob_size))


def _zigzag_decode(v):
    return (v >> 1) ^ -(v & 1)


def _inspect_primitive_block(raw):
    """Return (has_nodes, has_non_nodes, min_node_id, max_node_id)."""
    has_nodes = False
    has_non_nodes = False
    min_nid = None
    max_nid = None

    pos = 0
    n = len(raw)
    while pos < n:
        tag, pos = read_varint(raw, pos)
        field_no = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 2 and field_no == 2:  # PrimitiveGroup
            g_len, pos = read_varint(raw, pos)
            g_end = pos + g_len
            while pos < g_end:
                gtag, pos = read_varint(raw, pos)
                gfield = gtag >> 3
                gwire = gtag & 0x07
                if gfield == 1 and gwire == 2:  # Node
                    has_nodes = True
                    nlen, pos = read_varint(raw, pos)
                    nend = pos + nlen
                    while pos < nend:
                        ntag, pos = read_varint(raw, pos)
                        nf = ntag >> 3
                        nw = ntag & 0x07
                        if nf == 1 and nw == 0:
                            nid, pos = read_varint(raw, pos)
                            if min_nid is None or nid < min_nid:
                                min_nid = nid
                            if max_nid is None or nid > max_nid:
                                max_nid = nid
                        else:
                            pos = skip_field(raw, pos, nw)
                elif gfield == 2 and gwire == 2:  # DenseNodes
                    has_nodes = True
                    dlen, pos = read_varint(raw, pos)
                    dend = pos + dlen
                    while pos < dend:
                        dtag, pos = read_varint(raw, pos)
                        df = dtag >> 3
                        dw = dtag & 0x07
                        if df == 1 and dw == 2:  # packed sint64 id
                            ilen, pos = read_varint(raw, pos)
                            iend = pos + ilen
                            cur_id = 0
                            while pos < iend:
                                delta, pos = read_varint(raw, pos)
                                cur_id += _zigzag_decode(delta)
                                if min_nid is None or cur_id < min_nid:
                                    min_nid = cur_id
                                if max_nid is None or cur_id > max_nid:
                                    max_nid = cur_id
                        else:
                            pos = skip_field(raw, pos, dw)
                elif gfield in (3, 4, 5):  # Ways, Relations, Changesets
                    has_non_nodes = True
                    pos = skip_field(raw, pos, gwire)
                else:
                    pos = skip_field(raw, pos, gwire)
        else:
            pos = skip_field(raw, pos, wire_type)
    return has_nodes, has_non_nodes, min_nid, max_nid


def main():
    if len(sys.argv) != 4:
        sys.stderr.write(f"Usage: {sys.argv[0]} <base.osm.pbf> <extra_nodes.osm.pbf> <out.osm.pbf>\n")
        sys.exit(1)

    base_path, extra_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    extra_blocks = [b for b in scan_pbf_blocks(extra_path) if b[0] == "OSMData"]
    if not extra_blocks:
        # Nothing to insert (e.g. meta node clipped outside bbox)
        shutil.copyfile(base_path, out_path)
        return

    extra_min_nid = None
    with open(extra_path, "rb") as ef:
        for _, _, blob_start, blob_size, _ in extra_blocks:
            raw = _read_blob(ef, blob_start, blob_size)
            has_nodes, has_non_nodes, mn, _ = _inspect_primitive_block(raw)
            if has_non_nodes or not has_nodes or mn is None:
                sys.exit(FALLBACK_EXIT)
            if extra_min_nid is None or mn < extra_min_nid:
                extra_min_nid = mn

    base_blocks = scan_pbf_blocks(base_path)
    data_blocks = [b for b in base_blocks if b[0] == "OSMData"]
    if not data_blocks:
        sys.exit(FALLBACK_EXIT)

    # Binary search for the first OSMData block that contains non-nodes (ways/relations).
    # In a sorted PBF, blocks are [node-only...][maybe mixed][non-node-only...].
    with open(base_path, "rb") as bf:
        cache = {}

        def inspect_idx(idx):
            if idx not in cache:
                _, _, bs, bsz, _ = data_blocks[idx]
                cache[idx] = _inspect_primitive_block(_read_blob(bf, bs, bsz))
            return cache[idx]

        lo, hi = 0, len(data_blocks)
        while lo < hi:
            mid = (lo + hi) // 2
            _, has_non_nodes, _, _ = inspect_idx(mid)
            if has_non_nodes:
                hi = mid
            else:
                lo = mid + 1

        # Verify boundary block is clean (not mixed nodes + ways) and node IDs stay sorted
        if lo < len(data_blocks):
            has_nodes, _, _, _ = inspect_idx(lo)
            if has_nodes:
                sys.exit(FALLBACK_EXIT)

        if lo > 0:
            prev_nodes, prev_non_nodes, _, prev_max_nid = inspect_idx(lo - 1)
            if prev_non_nodes or not prev_nodes:
                sys.exit(FALLBACK_EXIT)
            if prev_max_nid is not None and extra_min_nid is not None and prev_max_nid >= extra_min_nid:
                sys.exit(FALLBACK_EXIT)

        insert_offset = (
            data_blocks[lo][1]
            if lo < len(data_blocks)
            else data_blocks[-1][1] + data_blocks[-1][4]
        )
        base_size = os.path.getsize(base_path)

        tmp_out = f"{out_path}.tmp.{os.getpid()}"
        try:
            with open(tmp_out, "wb") as dst_f:
                copy_range(bf, dst_f, 0, insert_offset)
                with open(extra_path, "rb") as ef:
                    for _, block_start, _, _, total_len in extra_blocks:
                        copy_range(ef, dst_f, block_start, total_len)
                copy_range(bf, dst_f, insert_offset, base_size - insert_offset)
            os.replace(tmp_out, out_path)
        except Exception:
            if os.path.exists(tmp_out):
                os.unlink(tmp_out)
            raise


if __name__ == "__main__":
    main()
