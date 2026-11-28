#!/usr/bin/env python3
"""Clone compiled Garmin .img tiles to a new 4-digit MAPID prefix.

Garmin tile .img files compiled by mkgmap with identical OSM input, style, DEM
config, code-page, and name-tag-list differ across TYP/MAPID variants only in:

1. Outer IMG FAT subfile names (`<old_mapname>.{TRE,RGN,LBL,NET,NOD,DEM}` ->
   `<new_mapname>.*`)
2. TRE header `mapId` (uint32 little-endian at offset 0x74)
3. TRE header 16-byte Garmin `MapValues` hash (offset 0x9A..0xA9, matching
   `uk.me.parabola.imgfmt.app.trergn.MapValues`)

All vector and routing subfiles (`RGN`, `LBL`, `NET`, `NOD`, `DEM`) are
byte-for-byte identical, allowing sibling variants (e.g. `bw` vs `odc`) to
reuse compiled tiles in under a second instead of re-running mkgmap.
"""

from __future__ import annotations

import argparse
import os
import re
import struct
import sys

MAP_ID_CODE_TABLE = (0, 1, 15, 5, 13, 4, 7, 6, 11, 9, 14, 8, 2, 10, 12, 3)
OFFSET_MAP = (6, 7, 5, 11, 3, 10, 13, 12, 1, 15, 4, 14, 8, 0, 2, 9)

FAT_OFFSET = 0x600
FAT_RECORD_SIZE = 512
TRE_MAP_ID_OFFSET = 0x74
TRE_MAP_VALUES_OFFSET = 0x9A
TRE_MAP_VALUES_END = 0xAA


def calc_map_values(map_id: int, header_len: int) -> bytes:
    """Compute the 16-byte TRE MapValues hash (offsets 0x9A..0xA9)."""

    def digit(i: int) -> int:
        return (map_id >> (4 * (7 - i))) & 0x0F

    v = [[0] * 8 for _ in range(4)]
    for i in range(8):
        v[2][i ^ 1] = MAP_ID_CODE_TABLE[digit(i)]
    v[3] = v[2][:]

    v[0][0] = (digit(4) + v[3][0]) & 0xFF
    v[0][1] = (digit(5) + v[3][1]) & 0xFF
    v[0][2] = (digit(6) + v[3][2]) & 0xFF
    v[0][3] = (digit(7) + v[3][3]) & 0xFF
    v[0][4] = v[3][4]
    v[0][5] = v[3][5]
    v[0][6] = v[3][6]
    v[0][7] = (v[3][7] + 1) & 0xFF

    v[1][0] = v[3][0]
    v[1][1] = v[3][1]
    v[1][2] = (v[3][2] + (header_len >> 4)) & 0x0F
    v[1][3] = (v[3][3] + header_len) & 0x0F
    v[1][4] = (v[3][4] + digit(0)) & 0xFF
    v[1][5] = (v[3][5] + digit(1)) & 0xFF
    v[1][6] = (v[3][6] + digit(2)) & 0xFF
    v[1][7] = (v[3][7] + digit(3)) & 0xFF

    n = (digit(1) + digit(3) + digit(5) + digit(7)) & 0x0F
    off = OFFSET_MAP[n]
    for r in range(4):
        for c in range(8):
            v[r][c] = (v[r][c] + off) & 0xFF

    vals = []
    for r in range(4):
        res = 0
        for c in range(8):
            res |= (v[r][c] & 0x0F) << (4 * (7 - c))
        vals.append(res)
    return struct.pack("<4I", *vals)


def clone_tile_img(src_path: str, dst_path: str, old_mapname: str, new_mapname: str) -> None:
    """Clone a single compiled Garmin tile .img with a new 8-digit mapname."""
    if len(old_mapname) != 8 or len(new_mapname) != 8 or not new_mapname.isdigit():
        raise ValueError(f"Expected 8-digit mapnames, got {old_mapname!r} -> {new_mapname!r}")

    with open(src_path, "rb") as f:
        data = bytearray(f.read())

    if not data or data[0] != 0:
        raise ValueError(f"{src_path}: unsupported non-zero IMG XOR byte")

    block_size = 1 << (data[0x61] + data[0x62])
    old_b = old_mapname.encode("ascii")
    new_b = new_mapname.encode("ascii")
    new_id = int(new_mapname)

    min_data = len(data)
    tre_first_block: int | None = None
    pos = FAT_OFFSET
    while pos + FAT_RECORD_SIZE <= min_data:
        rec = data[pos : pos + FAT_RECORD_SIZE]
        if rec[0] == 1:
            name = bytes(rec[1:9])
            ext = bytes(rec[9:12])
            part = struct.unpack_from("<H", rec, 16)[0]
            blocks = [b for b in struct.unpack_from("<240H", rec, 32) if b != 0xFFFF]
            if blocks and ext.strip():
                min_data = min(min_data, blocks[0] * block_size)
            if name == old_b:
                data[pos + 1 : pos + 9] = new_b
                if ext == b"TRE" and part == 0 and blocks:
                    tre_first_block = blocks[0]
        pos += FAT_RECORD_SIZE

    if tre_first_block is None:
        raise ValueError(f"{src_path}: TRE subfile for {old_mapname} not found")

    tre_off = tre_first_block * block_size
    tre_hdr_len = struct.unpack_from("<H", data, tre_off)[0]
    if tre_hdr_len < TRE_MAP_VALUES_END:
        raise ValueError(f"{src_path}: unexpected TRE header length {tre_hdr_len}")

    struct.pack_into("<I", data, tre_off + TRE_MAP_ID_OFFSET, new_id)
    data[tre_off + TRE_MAP_VALUES_OFFSET : tre_off + TRE_MAP_VALUES_END] = calc_map_values(
        new_id, tre_hdr_len
    )

    tmp_path = f"{dst_path}.{os.getpid()}.tmp"
    try:
        with open(tmp_path, "wb") as f:
            f.write(data)
        os.replace(tmp_path, dst_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("src_dir", help="Directory containing compiled source .img tiles")
    parser.add_argument("src_mapid", help="4-digit source MAPID prefix (e.g. 4115)")
    parser.add_argument("dst_dir", help="Destination directory for cloned .img tiles")
    parser.add_argument("dst_mapid", help="4-digit destination MAPID prefix (e.g. 4114)")
    args = parser.parse_args(argv)

    if not re.fullmatch(r"\d{4}", args.src_mapid) or not re.fullmatch(r"\d{4}", args.dst_mapid):
        parser.error("src_mapid and dst_mapid must be 4-digit numbers")

    os.makedirs(args.dst_dir, exist_ok=True)
    tile_re = re.compile(rf"^({re.escape(args.src_mapid)}\d{{4}})\.img$")
    overview_name = f"{args.src_mapid}0000"

    count = 0
    for entry in sorted(os.listdir(args.src_dir)):
        m = tile_re.match(entry)
        if not m:
            continue
        old_mn = m.group(1)
        if old_mn == overview_name:
            continue
        new_mn = args.dst_mapid + old_mn[4:]
        src_path = os.path.join(args.src_dir, entry)
        dst_path = os.path.join(args.dst_dir, f"{new_mn}.img")
        clone_tile_img(src_path, dst_path, old_mn, new_mn)
        count += 1

    if count == 0:
        print(
            f"gmap-clone-tiles: no {args.src_mapid}xxxx.img tiles found in {args.src_dir}",
            file=sys.stderr,
        )
        return 1

    print(
        f"gmap-clone-tiles: cloned {count} tiles ({args.src_mapid} -> {args.dst_mapid})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
