#!/usr/bin/env python3
"""Merge same-attribute Polygon features into MultiPolygons in PMTiles v3.

Replaces tilemaker's ``combine_polygons_below`` (which runs Boost.Geometry
boolean polygon union and stalls for several minutes on dense urban tiles)
with an O(N) MVT ring concatenation pass over the target zoom range.

Only tiles within ``[minzoom, maxzoom]`` that actually contain more than one
Polygon feature in the target layer are rewritten; every other tile (e.g.
z4-z11, z14, and non-urban z12-z13 tiles) is copied verbatim without
decompression or recompression. The output is written as a clustered,
deduplicated PMTiles v3 archive that passes ``pmtiles verify``.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import struct
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

_PMTILES_HEADER_SIZE = 127
_PMTILES_ROOT_MAX = 16384 - _PMTILES_HEADER_SIZE
_PMTILES_HEADER_STRUCT = struct.Struct("<QQQQQQQQQQQBBBBBBiiiiBii")
_COMP_NONE = 1
_COMP_GZIP = 2
_MVT_GEOM_POLYGON = 3


@dataclass
class _DirEntry:
    tile_id: int
    offset: int
    length: int
    run_length: int


def _zoom_base(z: int) -> int:
    """First Hilbert tile ID at zoom level z."""
    return ((1 << (2 * z)) - 1) // 3


def _read_varint(buf: bytes | memoryview, pos: int) -> tuple[int, int]:
    val = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, pos
        shift += 7


def _encode_varint(val: int, out: bytearray) -> None:
    while True:
        b = val & 0x7F
        val >>= 7
        if val:
            out.append(b | 0x80)
        else:
            out.append(b)
            return


def _zigzag_dec(u: int) -> int:
    return (u >> 1) ^ -(u & 1)


def _zigzag_enc(s: int) -> int:
    # MVT sint32 zigzag encoding (matches protobuf WireFormat::ZigZagEncode32)
    return ((s << 1) ^ (s >> 31)) & 0xFFFFFFFF


def _decompress_internal(data: bytes, comp: int) -> bytes:
    if comp == _COMP_NONE:
        return data
    if comp == _COMP_GZIP:
        return gzip.decompress(data)
    raise ValueError(f"Unsupported PMTiles internal compression: {comp}")


def _compress_internal(data: bytes, comp: int) -> bytes:
    if comp == _COMP_NONE:
        return data
    if comp == _COMP_GZIP:
        return gzip.compress(data, compresslevel=6)
    raise ValueError(f"Unsupported PMTiles internal compression: {comp}")


def _decode_directory(raw: bytes) -> list[_DirEntry]:
    pos = 0
    num_entries, pos = _read_varint(raw, pos)
    if num_entries == 0:
        return []

    tile_ids = [0] * num_entries
    last_id = 0
    for i in range(num_entries):
        delta, pos = _read_varint(raw, pos)
        last_id += delta
        tile_ids[i] = last_id

    run_lengths = [0] * num_entries
    for i in range(num_entries):
        run_lengths[i], pos = _read_varint(raw, pos)

    lengths = [0] * num_entries
    for i in range(num_entries):
        lengths[i], pos = _read_varint(raw, pos)

    offsets = [0] * num_entries
    for i in range(num_entries):
        tmp, pos = _read_varint(raw, pos)
        if i > 0 and tmp == 0:
            offsets[i] = offsets[i - 1] + lengths[i - 1]
        else:
            offsets[i] = tmp - 1

    return [
        _DirEntry(tile_ids[i], offsets[i], lengths[i], run_lengths[i])
        for i in range(num_entries)
    ]


def _encode_directory(entries: list[_DirEntry]) -> bytes:
    out = bytearray()
    _encode_varint(len(entries), out)
    last_id = 0
    for e in entries:
        _encode_varint(e.tile_id - last_id, out)
        last_id = e.tile_id
    for e in entries:
        _encode_varint(e.run_length, out)
    for e in entries:
        _encode_varint(e.length, out)
    for i, e in enumerate(entries):
        if i > 0 and e.offset == entries[i - 1].offset + entries[i - 1].length:
            _encode_varint(0, out)
        else:
            _encode_varint(e.offset + 1, out)
    return bytes(out)


def _read_all_tile_entries(
    fp_bytes: memoryview | bytes,
    root_off: int,
    root_len: int,
    leaf_off: int,
    internal_comp: int,
) -> list[_DirEntry]:
    root_raw = _decompress_internal(bytes(fp_bytes[root_off : root_off + root_len]), internal_comp)
    root_entries = _decode_directory(root_raw)
    all_entries: list[_DirEntry] = []
    for e in root_entries:
        if e.run_length == 0:
            leaf_slice = bytes(fp_bytes[leaf_off + e.offset : leaf_off + e.offset + e.length])
            leaf_raw = _decompress_internal(leaf_slice, internal_comp)
            all_entries.extend(_decode_directory(leaf_raw))
        else:
            all_entries.append(e)
    return all_entries


def _build_directories(
    entries: list[_DirEntry],
    meta_len: int,
    internal_comp: int,
) -> tuple[bytes, bytes]:
    """Encode root directory and (if needed) leaf directories within the 16 KiB header budget."""
    max_root = _PMTILES_ROOT_MAX - meta_len
    if max_root <= 0:
        raise ValueError(f"PMTiles metadata ({meta_len} bytes) exceeds 16 KiB header budget")

    direct_root = _compress_internal(_encode_directory(entries), internal_comp)
    if len(direct_root) <= max_root:
        return direct_root, b""

    leaf_size = max(4096, len(entries) // 3500)
    while True:
        leaf_blobs: list[bytes] = []
        root_entries: list[_DirEntry] = []
        leaf_cursor = 0
        for i in range(0, len(entries), leaf_size):
            chunk = entries[i : i + leaf_size]
            blob = _compress_internal(_encode_directory(chunk), internal_comp)
            root_entries.append(
                _DirEntry(
                    tile_id=chunk[0].tile_id,
                    offset=leaf_cursor,
                    length=len(blob),
                    run_length=0,
                )
            )
            leaf_blobs.append(blob)
            leaf_cursor += len(blob)

        root_blob = _compress_internal(_encode_directory(root_entries), internal_comp)
        if len(root_blob) <= max_root:
            return root_blob, b"".join(leaf_blobs)
        leaf_size = int(leaf_size * 1.2) + 1


def _split_entry_at_range(
    e: _DirEntry, range_start: int, range_end: int
) -> list[tuple[_DirEntry, bool]]:
    """Split a run-length entry if it crosses [range_start, range_end)."""
    s = e.tile_id
    t = e.tile_id + e.run_length
    if t <= range_start or s >= range_end:
        return [(e, False)]
    parts: list[tuple[_DirEntry, bool]] = []
    if s < range_start:
        parts.append((_DirEntry(s, e.offset, e.length, range_start - s), False))
    in_s = max(s, range_start)
    in_t = min(t, range_end)
    parts.append((_DirEntry(in_s, e.offset, e.length, in_t - in_s), True))
    if t > range_end:
        parts.append((_DirEntry(range_end, e.offset, e.length, t - range_end), False))
    return parts


def _scan_polygon_geom(geom: bytes) -> tuple[int, int, int, int, int]:
    """Return (first_x, first_y, after_first_xy_pos, end_x, end_y) for an MVT polygon geometry.

    In MVT 2.1, every coordinate after the initial MoveTo is delta-encoded
    relative to the previous vertex, and ClosePath does not move the cursor.
    Concatenating polygon features into one MultiPolygon therefore only
    requires rewriting the first MoveTo's (dx, dy) delta.
    """
    pos = 0
    n = len(geom)
    cx = 0
    cy = 0
    first_x = 0
    first_y = 0
    after_first_xy = -1

    while pos < n:
        cmd_int, pos = _read_varint(geom, pos)
        cmd = cmd_int & 7
        cnt = cmd_int >> 3
        if cmd in (1, 2):
            for idx in range(cnt):
                ux, pos = _read_varint(geom, pos)
                uy, pos = _read_varint(geom, pos)
                cx += _zigzag_dec(ux)
                cy += _zigzag_dec(uy)
                if after_first_xy == -1 and cmd == 1 and idx == 0:
                    first_x = cx
                    first_y = cy
                    after_first_xy = pos
        elif cmd == 7:
            continue
        else:
            raise ValueError(f"Unexpected MVT geometry command: {cmd}")

    return first_x, first_y, after_first_xy, cx, cy


def _concat_polygon_geoms(geoms: list[bytes]) -> bytes:
    """Concatenate multiple MVT Polygon geometry streams into one MultiPolygon stream."""
    out = bytearray()
    cur_x = 0
    cur_y = 0
    first = True

    for geom in geoms:
        if not geom:
            continue
        first_x, first_y, after_first_xy, end_x, end_y = _scan_polygon_geom(geom)
        if after_first_xy == -1:
            continue
        if first:
            out.extend(geom)
            cur_x = end_x
            cur_y = end_y
            first = False
        else:
            # Copy the initial MoveTo command header varint verbatim, patch ONLY the first (dx, dy),
            # then copy the rest of the geometry byte-for-byte.
            cmd_int, _ = _read_varint(geom, 0)
            _encode_varint(cmd_int, out)
            _encode_varint(_zigzag_enc(first_x - cur_x), out)
            _encode_varint(_zigzag_enc(first_y - cur_y), out)
            out.extend(geom[after_first_xy:])
            cur_x = end_x
            cur_y = end_y

    return bytes(out)


def _decode_packed_uints(buf: bytes) -> tuple[int, ...]:
    vals: list[int] = []
    pos = 0
    n = len(buf)
    while pos < n:
        v, pos = _read_varint(buf, pos)
        vals.append(v)
    return tuple(vals)


def _encode_packed_uints(vals: tuple[int, ...]) -> bytes:
    out = bytearray()
    for v in vals:
        _encode_varint(v, out)
    return bytes(out)


def _merge_layer_polygons(layer_bytes: bytes, target_layer: str) -> bytes | None:
    """Merge same-tag Polygon features in ``target_layer``.

    Returns rebuilt layer bytes if >= 2 Polygon features were merged into fewer
    features; otherwise returns ``None`` so the caller leaves the tile untouched.
    """
    pos = 0
    n = len(layer_bytes)
    layer_name = ""
    non_feature_parts: list[bytes] = []
    feature_blobs: list[bytes] = []

    while pos < n:
        start = pos
        tag, pos = _read_varint(layer_bytes, pos)
        field = tag >> 3
        wt = tag & 7
        if wt == 0:
            _, pos = _read_varint(layer_bytes, pos)
            non_feature_parts.append(layer_bytes[start:pos])
        elif wt == 2:
            ln, pos = _read_varint(layer_bytes, pos)
            val = layer_bytes[pos : pos + ln]
            pos += ln
            if field == 1:
                layer_name = val.decode("utf-8")
                non_feature_parts.append(layer_bytes[start:pos])
            elif field == 2:
                feature_blobs.append(val)
            else:
                non_feature_parts.append(layer_bytes[start:pos])
        elif wt == 5:
            pos += 4
            non_feature_parts.append(layer_bytes[start:pos])
        elif wt == 1:
            pos += 8
            non_feature_parts.append(layer_bytes[start:pos])
        else:
            raise ValueError(f"Unsupported protobuf wire type {wt} in MVT layer")

    if layer_name != target_layer or len(feature_blobs) <= 1:
        return None

    groups: dict[tuple[int, ...], list[bytes]] = {}
    passthrough_features: list[bytes] = []
    polygon_count = 0

    for fblob in feature_blobs:
        fp = 0
        fn = len(fblob)
        ftype = 0
        ftags: list[int] = []
        fgeom = b""
        has_id = False
        while fp < fn:
            ftag, fp = _read_varint(fblob, fp)
            ffield = ftag >> 3
            fwt = ftag & 7
            if fwt == 0:
                v, fp = _read_varint(fblob, fp)
                if ffield == 1:
                    has_id = True
                elif ffield == 2:
                    ftags.append(v)
                elif ffield == 3:
                    ftype = v
            elif fwt == 2:
                fln, fp = _read_varint(fblob, fp)
                fval = fblob[fp : fp + fln]
                fp += fln
                if ffield == 2:
                    ftags.extend(_decode_packed_uints(fval))
                elif ffield == 4:
                    fgeom = fval
            elif fwt == 5:
                fp += 4
            elif fwt == 1:
                fp += 8
            else:
                raise ValueError(f"Unsupported protobuf wire type {fwt} in MVT feature")

        if ftype == _MVT_GEOM_POLYGON and not has_id and fgeom:
            polygon_count += 1
            groups.setdefault(tuple(ftags), []).append(fgeom)
        else:
            passthrough_features.append(fblob)

    # Nothing would actually merge (every tag group has at most 1 polygon).
    if polygon_count <= len(groups):
        return None

    rebuilt = bytearray()
    for part in non_feature_parts:
        rebuilt.extend(part)
    for pf in passthrough_features:
        rebuilt.append((2 << 3) | 2)
        _encode_varint(len(pf), rebuilt)
        rebuilt.extend(pf)

    for tag_tuple, geoms in groups.items():
        merged_geom = geoms[0] if len(geoms) == 1 else _concat_polygon_geoms(geoms)
        feat = bytearray()
        if tag_tuple:
            tb = _encode_packed_uints(tag_tuple)
            feat.append((2 << 3) | 2)
            _encode_varint(len(tb), feat)
            feat.extend(tb)
        feat.append((3 << 3) | 0)
        feat.append(_MVT_GEOM_POLYGON)
        feat.append((4 << 3) | 2)
        _encode_varint(len(merged_geom), feat)
        feat.extend(merged_geom)
        rebuilt.append((2 << 3) | 2)
        _encode_varint(len(feat), rebuilt)
        rebuilt.extend(feat)

    return bytes(rebuilt)


def _process_tile_blob(
    args: tuple[bytes, int, str],
) -> bytes | None:
    """Worker: merge target layer polygons in one tile blob. Returns None if unchanged."""
    raw_blob, tile_comp, target_layer = args
    if tile_comp == _COMP_GZIP:
        mvt = gzip.decompress(raw_blob)
    elif tile_comp == _COMP_NONE:
        mvt = raw_blob
    else:
        raise ValueError(f"Unsupported PMTiles tile compression: {tile_comp}")

    # Fast pre-check: skip full protobuf walk if layer name does not appear at all.
    if target_layer.encode("utf-8") not in mvt:
        return None

    pos = 0
    n = len(mvt)
    out = bytearray()
    changed = False

    while pos < n:
        start = pos
        tag, pos = _read_varint(mvt, pos)
        field = tag >> 3
        wt = tag & 7
        if wt == 2:
            ln, pos = _read_varint(mvt, pos)
            sub = mvt[pos : pos + ln]
            pos += ln
            if field == 3:
                merged = _merge_layer_polygons(sub, target_layer)
                if merged is not None:
                    out.append((3 << 3) | 2)
                    _encode_varint(len(merged), out)
                    out.extend(merged)
                    changed = True
                    continue
            out.extend(mvt[start:pos])
        elif wt == 0:
            _, pos = _read_varint(mvt, pos)
            out.extend(mvt[start:pos])
        elif wt == 5:
            pos += 4
            out.extend(mvt[start:pos])
        elif wt == 1:
            pos += 8
            out.extend(mvt[start:pos])
        else:
            raise ValueError(f"Unsupported protobuf wire type {wt} in MVT tile")

    if not changed:
        return None

    if tile_comp == _COMP_GZIP:
        return gzip.compress(bytes(out), compresslevel=6)
    return bytes(out)


def merge_pmtiles(
    input_path: Path,
    output_path: Path,
    layer: str,
    minzoom: int,
    maxzoom: int,
    workers: int,
) -> tuple[int, int]:
    """Rewrite ``input_path`` to ``output_path`` merging Polygon features in ``layer``.

    Returns ``(modified_unique_tiles, total_unique_tiles)``.
    """
    src_bytes = input_path.read_bytes()
    if len(src_bytes) < _PMTILES_HEADER_SIZE or src_bytes[:7] != b"PMTiles" or src_bytes[7] != 3:
        raise ValueError(f"Not a PMTiles v3 archive: {input_path}")

    (
        root_off,
        root_len,
        meta_off,
        meta_len,
        leaf_off,
        _leaf_len,
        data_off,
        _data_len,
        _n_addressed,
        _n_entries,
        _n_contents,
        _clustered,
        internal_comp,
        tile_comp,
        tile_type,
        hdr_min_zoom,
        hdr_max_zoom,
        min_lon_e7,
        min_lat_e7,
        max_lon_e7,
        max_lat_e7,
        center_zoom,
        center_lon_e7,
        center_lat_e7,
    ) = _PMTILES_HEADER_STRUCT.unpack_from(src_bytes, 8)

    meta_blob = src_bytes[meta_off : meta_off + meta_len]
    src_entries = _read_all_tile_entries(src_bytes, root_off, root_len, leaf_off, internal_comp)

    range_start = _zoom_base(minzoom)
    range_end = _zoom_base(maxzoom + 1)

    split_entries: list[tuple[_DirEntry, bool]] = []
    candidate_keys: dict[tuple[int, int], bytes] = {}
    for entry in src_entries:
        for part, in_range in _split_entry_at_range(entry, range_start, range_end):
            split_entries.append((part, in_range))
            if in_range:
                key = (part.offset, part.length)
                if key not in candidate_keys:
                    candidate_keys[key] = src_bytes[
                        data_off + part.offset : data_off + part.offset + part.length
                    ]

    # Process unique candidate tiles in parallel.
    modified_map: dict[tuple[int, int], bytes] = {}
    if candidate_keys:
        keys_list = list(candidate_keys.keys())
        work_items = [(candidate_keys[k], tile_comp, layer) for k in keys_list]
        num_workers = min(max(1, workers), len(work_items))
        if num_workers == 1:
            results = [_process_tile_blob(item) for item in work_items]
        else:
            chunksize = max(1, len(work_items) // (num_workers * 4))
            with ProcessPoolExecutor(max_workers=num_workers) as pool:
                results = list(pool.map(_process_tile_blob, work_items, chunksize=chunksize))
        for k, res in zip(keys_list, results, strict=True):
            if res is not None:
                modified_map[k] = res

    # If nothing changed and we are rewriting in-place, exit immediately.
    if not modified_map and input_path.resolve() == output_path.resolve():
        return 0, len(candidate_keys)

    # Assemble clustered, deduplicated tile data in ascending tile_id order.
    split_entries.sort(key=lambda pair: pair[0].tile_id)
    new_entries: list[_DirEntry] = []
    tile_blobs: list[bytes] = []
    dedup: dict[tuple[str, object], tuple[int, int]] = {}
    data_cursor = 0

    for part, in_range in split_entries:
        orig_key = (part.offset, part.length)
        mod_blob = modified_map.get(orig_key) if in_range else None
        if mod_blob is not None:
            dkey: tuple[str, object] = ("mod", hashlib.sha256(mod_blob).digest())
            blob_to_write: bytes | None = mod_blob
        else:
            dkey = ("orig", orig_key)
            blob_to_write = None

        loc = dedup.get(dkey)
        if loc is None:
            if blob_to_write is None:
                blob_to_write = src_bytes[
                    data_off + part.offset : data_off + part.offset + part.length
                ]
            loc = (data_cursor, len(blob_to_write))
            dedup[dkey] = loc
            tile_blobs.append(blob_to_write)
            data_cursor += len(blob_to_write)

        dst_off, dst_len = loc
        if (
            new_entries
            and new_entries[-1].tile_id + new_entries[-1].run_length == part.tile_id
            and new_entries[-1].offset == dst_off
            and new_entries[-1].length == dst_len
        ):
            new_entries[-1].run_length += part.run_length
        else:
            new_entries.append(_DirEntry(part.tile_id, dst_off, dst_len, part.run_length))

    root_blob, leaf_blob = _build_directories(new_entries, len(meta_blob), internal_comp)
    new_root_off = _PMTILES_HEADER_SIZE
    new_meta_off = new_root_off + len(root_blob)
    new_leaf_off = new_meta_off + len(meta_blob)
    new_data_off = new_leaf_off + len(leaf_blob)

    n_addressed = sum(e.run_length for e in new_entries)
    n_entries = len(new_entries)
    n_contents = len(tile_blobs)

    header = bytearray(b"PMTiles\x03")
    header.extend(
        _PMTILES_HEADER_STRUCT.pack(
            new_root_off,
            len(root_blob),
            new_meta_off,
            len(meta_blob),
            new_leaf_off if leaf_blob else 0,
            len(leaf_blob),
            new_data_off,
            data_cursor,
            n_addressed,
            n_entries,
            n_contents,
            1,  # clustered
            internal_comp,
            tile_comp,
            tile_type,
            hdr_min_zoom,
            hdr_max_zoom,
            min_lon_e7,
            min_lat_e7,
            max_lon_e7,
            max_lat_e7,
            center_zoom,
            center_lon_e7,
            center_lat_e7,
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_name(f".{output_path.name}.tmp.{os.getpid()}")
    try:
        with tmp_path.open("wb") as out_fp:
            out_fp.write(header)
            out_fp.write(root_blob)
            out_fp.write(meta_blob)
            if leaf_blob:
                out_fp.write(leaf_blob)
            for blob in tile_blobs:
                out_fp.write(blob)
        os.replace(tmp_path, output_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise

    return len(modified_map), len(candidate_keys)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge same-attribute Polygon features into MultiPolygons in PMTiles v3."
    )
    parser.add_argument("input", type=Path, help="Input PMTiles v3 archive.")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Output PMTiles v3 archive (defaults to rewriting input in-place).",
    )
    parser.add_argument("--layer", default="building", help="Target MVT layer name (default: building).")
    parser.add_argument("--minzoom", type=int, default=12, help="First zoom level to merge (default: 12).")
    parser.add_argument("--maxzoom", type=int, default=13, help="Last zoom level to merge (default: 13).")
    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count() or 4,
        help="Number of worker processes (default: CPU count).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    out_path: Path = args.output if args.output is not None else args.input
    modified, candidates = merge_pmtiles(
        input_path=args.input,
        output_path=out_path,
        layer=args.layer,
        minzoom=args.minzoom,
        maxzoom=args.maxzoom,
        workers=args.workers,
    )
    print(
        f"pmtiles-merge-buildings: merged {modified}/{candidates} unique z{args.minzoom}-z{args.maxzoom} "
        f"'{args.layer}' tiles"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
