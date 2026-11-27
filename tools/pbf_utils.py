"""Generic OSM PBF block-level utilities and parallel PrimitiveBlock shard runner.

An `.osm.pbf` file is a sequence of self-contained `[len][BlobHeader][Blob]`
records: one `OSMHeader` followed by sorted `OSMData` blocks. Operating at the
raw blob boundary enables:

- Splitting a large PBF into contiguous shards for multi-process worker pools
  with zero protobuf decoding overhead in the parent process.
- Concatenating shard output PBFs along exact `OSMData` blob boundaries with
  zero zlib recompression while preserving sorted entity order.
- Inspecting or splicing raw blobs (e.g. `tools/pbf-insert-nodes.py`).
"""

import multiprocessing
import os
import shutil
import struct
import tempfile
import zlib

DEFAULT_MIN_PARALLEL_BYTES = 4 * 1024 * 1024
DEFAULT_CHUNKS_PER_WORKER = 8


def read_varint(buf, pos):
    """Decode a protobuf unsigned varint starting at `pos`."""
    val = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, pos
        shift += 7


def skip_field(buf, pos, wire_type):
    """Advance `pos` past a protobuf field of `wire_type`."""
    if wire_type == 0:
        _, pos = read_varint(buf, pos)
    elif wire_type == 1:
        pos += 8
    elif wire_type == 2:
        length, pos = read_varint(buf, pos)
        pos += length
    elif wire_type == 5:
        pos += 4
    else:
        raise ValueError(f"Unsupported protobuf wire type {wire_type}")
    return pos


def parse_blob_header(data):
    """Parse `(type, datasize)` from a serialized PBF `BlobHeader` message."""
    pos = 0
    n = len(data)
    btype = ""
    datasize = 0
    while pos < n:
        tag, pos = read_varint(data, pos)
        field_no = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 2 and field_no == 1:
            length, pos = read_varint(data, pos)
            btype = data[pos : pos + length].decode("utf-8")
            pos += length
        elif wire_type == 0 and field_no == 3:
            datasize, pos = read_varint(data, pos)
        else:
            pos = skip_field(data, pos, wire_type)
    return btype, datasize


def scan_pbf_blocks(path):
    """Return list of `(btype, block_start, blob_start, blob_size, total_len)`."""
    blocks = []
    with open(path, "rb") as f:
        while True:
            raw_len = f.read(4)
            if not raw_len:
                break
            if len(raw_len) != 4:
                raise ValueError(f"Truncated PBF header length in {path}")
            hlen = struct.unpack(">I", raw_len)[0]
            hbytes = f.read(hlen)
            btype, dsize = parse_blob_header(hbytes)
            blob_start = f.tell()
            block_start = blob_start - 4 - hlen
            blocks.append((btype, block_start, blob_start, dsize, 4 + hlen + dsize))
            f.seek(dsize, os.SEEK_CUR)
    return blocks


def copy_range(src_f, dst_f, offset, length, buf_size=4 * 1024 * 1024):
    """Copy `length` bytes from `src_f` starting at `offset` into `dst_f`."""
    src_f.seek(offset)
    remaining = length
    while remaining > 0:
        chunk = src_f.read(min(remaining, buf_size))
        if not chunk:
            raise EOFError("Unexpected EOF while copying PBF byte range")
        dst_f.write(chunk)
        remaining -= len(chunk)


def decompress_blob(raw_blob):
    """Extract raw payload bytes from a serialized PBF `Blob` message."""
    pos = 0
    n = len(raw_blob)
    raw = None
    zlib_data = None
    while pos < n:
        tag, pos = read_varint(raw_blob, pos)
        field_no = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 2 and field_no == 1:
            length, pos = read_varint(raw_blob, pos)
            raw = raw_blob[pos : pos + length]
            pos += length
        elif wire_type == 2 and field_no == 3:
            length, pos = read_varint(raw_blob, pos)
            zlib_data = raw_blob[pos : pos + length]
            pos += length
        else:
            pos = skip_field(raw_blob, pos, wire_type)
    if raw is not None:
        return raw
    if zlib_data is not None:
        return zlib.decompress(zlib_data)
    raise ValueError("Unsupported or empty PBF Blob compression")


def primitive_block_entity_types(raw_pblock):
    """Return set of entity types (`'n'`, `'w'`, `'r'`) in a `PrimitiveBlock`."""
    types = set()
    pos = 0
    n = len(raw_pblock)
    while pos < n:
        tag, pos = read_varint(raw_pblock, pos)
        field_no = tag >> 3
        wire_type = tag & 0x07
        if wire_type == 2 and field_no == 2:
            length, pos = read_varint(raw_pblock, pos)
            end = pos + length
            gpos = pos
            while gpos < end:
                gtag, gpos = read_varint(raw_pblock, gpos)
                gfield = gtag >> 3
                gwire = gtag & 0x07
                if gfield in (1, 2):
                    types.add("n")
                elif gfield == 3:
                    types.add("w")
                elif gfield == 4:
                    types.add("r")
                gpos = skip_field(raw_pblock, gpos, gwire)
            pos = end
        else:
            pos = skip_field(raw_pblock, pos, wire_type)
    return types


def read_block_entity_types(src_f, block):
    """Return entity types (`'n'`, `'w'`, `'r'`) contained in an `OSMData` block."""
    _, _, blob_start, blob_size, _ = block
    src_f.seek(blob_start)
    raw_blob = src_f.read(blob_size)
    return primitive_block_entity_types(decompress_blob(raw_blob))


def find_first_block_with_types(src_f, data_blocks, target_types):
    """Binary-search sorted `data_blocks` (n < w < r) for first block matching `target_types`.

    Returns index into `data_blocks`, or `len(data_blocks)` if none match.
    """
    rank = {"n": 0, "w": 1, "r": 2}
    min_target_rank = min(rank[t] for t in target_types)
    lo, hi = 0, len(data_blocks)
    while lo < hi:
        mid = (lo + hi) // 2
        btypes = read_block_entity_types(src_f, data_blocks[mid])
        max_rank = max((rank[t] for t in btypes), default=-1)
        if max_rank >= min_target_rank:
            hi = mid
        else:
            lo = mid + 1
    return lo


def write_pbf_block_slice(src_f, header_block, data_blocks, start_idx, end_idx, outfile):
    """Write `header_block` + `data_blocks[start_idx:end_idx]` raw to `outfile`."""
    with open(outfile, "wb") as dst_f:
        _, h_start, _, _, h_len = header_block
        copy_range(src_f, dst_f, h_start, h_len)
        if start_idx < end_idx:
            seg_start = data_blocks[start_idx][1]
            seg_end = data_blocks[end_idx - 1][1] + data_blocks[end_idx - 1][4]
            copy_range(src_f, dst_f, seg_start, seg_end - seg_start)


def concat_pbf_shards(shard_paths, outfile):
    """Concatenate ordered shard PBF files along exact OSMData blob boundaries."""
    out_dir = os.path.dirname(os.path.abspath(outfile))
    tmp_out = os.path.join(out_dir, f".concat_{os.getpid()}.osm.pbf")
    wrote_header = False
    try:
        with open(tmp_out, "wb") as dst_f:
            for shard_path in shard_paths:
                blocks = scan_pbf_blocks(shard_path)
                header_blocks = [b for b in blocks if b[0] == "OSMHeader"]
                data_blocks = [b for b in blocks if b[0] == "OSMData"]
                with open(shard_path, "rb") as sf:
                    if not wrote_header and header_blocks:
                        _, h_start, _, _, h_len = header_blocks[0]
                        copy_range(sf, dst_f, h_start, h_len)
                        wrote_header = True
                    if data_blocks:
                        seg_start = data_blocks[0][1]
                        seg_end = data_blocks[-1][1] + data_blocks[-1][4]
                        copy_range(sf, dst_f, seg_start, seg_end - seg_start)
        os.replace(tmp_out, outfile)
    except Exception:
        if os.path.exists(tmp_out):
            os.unlink(tmp_out)
        raise


def run_parallel_pbf(
    infile,
    outfile,
    worker_fn,
    workers,
    *,
    extra_args=(),
    initializer=None,
    min_size=DEFAULT_MIN_PARALLEL_BYTES,
    chunks_per_worker=DEFAULT_CHUNKS_PER_WORKER,
    tmp_prefix=".pbf_shard_",
):
    """Run `worker_fn` across contiguous PBF shards in a forked worker pool.

    `worker_fn` receives `(in_shard, out_shard, *extra_args)` and may return
    any picklable per-shard result (e.g. statistics). Each shard is partitioned
    by equal `OSMData` block count (~8,000 objects/block) into
    `workers * chunks_per_worker` chunks for dynamic load balancing.

    Returns `(ran_parallel, results)`. When preconditions are not met (small
    file, non-PBF input/output, `workers <= 1`, no `os.fork`, or too few
    `OSMData` blocks), returns `(False, [])` so the caller can fall back to its
    serial/non-PBF path.
    """
    if (
        workers <= 1
        or not infile.endswith(".pbf")
        or not outfile.endswith(".pbf")
        or not os.path.exists(infile)
        or os.path.getsize(infile) < min_size
        or not hasattr(os, "fork")
    ):
        return False, []

    blocks = scan_pbf_blocks(infile)
    header_blocks = [b for b in blocks if b[0] == "OSMHeader"]
    data_blocks = [b for b in blocks if b[0] == "OSMData"]
    if not header_blocks or len(data_blocks) < workers * 2:
        return False, []

    h_start, h_len = header_blocks[0][1], header_blocks[0][4]
    with open(infile, "rb") as f:
        f.seek(h_start)
        header_bytes = f.read(h_len)

    num_chunks = min(len(data_blocks), workers * chunks_per_worker)
    base_per_chunk, extra = divmod(len(data_blocks), num_chunks)
    shards_ranges = []
    pos = 0
    for c in range(num_chunks):
        size = base_per_chunk + (1 if c < extra else 0)
        shards_ranges.append((pos, pos + size))
        pos += size

    out_dir = os.path.dirname(os.path.abspath(outfile))
    tmp_dir = tempfile.mkdtemp(prefix=tmp_prefix, dir=out_dir)
    try:
        tasks = []
        out_shards = []
        with open(infile, "rb") as src_f:
            for shard_id, (lo, hi) in enumerate(shards_ranges):
                in_shard = os.path.join(tmp_dir, f"in_{shard_id:03d}.osm.pbf")
                out_shard = os.path.join(tmp_dir, f"out_{shard_id:03d}.osm.pbf")
                seg_start = data_blocks[lo][1]
                seg_end = data_blocks[hi - 1][1] + data_blocks[hi - 1][4]
                with open(in_shard, "wb") as dst_f:
                    dst_f.write(header_bytes)
                    copy_range(src_f, dst_f, seg_start, seg_end - seg_start)
                tasks.append((in_shard, out_shard, *extra_args))
                out_shards.append(out_shard)

        ctx = multiprocessing.get_context("fork")
        with ctx.Pool(workers, initializer=initializer) as pool:
            results = list(pool.imap(worker_fn, tasks, chunksize=1))

        concat_pbf_shards(out_shards, outfile)
        return True, results
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
