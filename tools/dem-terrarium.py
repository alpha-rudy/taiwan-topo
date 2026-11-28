#!/usr/bin/env python3
"""Re-encode a Mapbox terrain-RGB MBTiles (rio rgbify -b -10000 -i 0.1) in
place as Terrarium-encoded lossless WebP, the format style.json declares for
its raster-dem source ("encoding": "terrarium").

Terrarium stores whole metres in R and G (elevation + 32768 = R * 256 + G)
and the fraction in B. rio rgbify resamples bilinearly into the HGT's own
integer type (int16), so every value it writes is a whole metre: B is always
0, and the tiles compress to well under half the Mapbox PNGs with the same elevations.
A tile whose elevations are not whole metres is an error, not rounded away.

rio rgbify writes no bounds, so go-pmtiles would give the archive a whole-world
header. Write the source mosaic's extent as bounds (and its middle as center)
so the PMTiles header says where the elevations are.

Usage: dem-terrarium.py <tiles.mbtiles> <source.vrt>
"""
import io
import multiprocessing
import os
import sqlite3
import sys

import numpy as np
import rasterio
from PIL import Image


def _reencode_tile(row):
    z, x, y, data = row
    rgb = np.asarray(Image.open(io.BytesIO(data)).convert("RGB")).astype(np.int64)
    tenths = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]   # (h + 10000) * 10
    if np.any(tenths % 10):
        raise ValueError(f"tile {z}/{x}/{y} has elevations that are not whole metres")
    v = tenths // 10 - 10000 + 32768
    out = np.stack([v >> 8, v & 255, np.zeros_like(v)], -1).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(out, "RGB").save(buf, "WEBP", lossless=True, quality=100, method=6)
    return buf.getvalue(), z, x, y


def main():
    db = sqlite3.connect(sys.argv[1])
    rows = db.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles").fetchall()
    workers = max(1, int(os.environ.get("DEM_WORKERS") or os.cpu_count() or 1))
    workers = min(workers, len(rows)) if rows else 1
    try:
        if workers > 1:
            with multiprocessing.Pool(processes=workers) as pool:
                for tile_data, z, x, y in pool.imap(_reencode_tile, rows, chunksize=4):
                    db.execute(
                        "UPDATE tiles SET tile_data = ? WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
                        (tile_data, z, x, y),
                    )
        else:
            for row in rows:
                tile_data, z, x, y = _reencode_tile(row)
                db.execute(
                    "UPDATE tiles SET tile_data = ? WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
                    (tile_data, z, x, y),
                )
    except ValueError as err:
        db.close()
        sys.exit(str(err))
    db.execute("UPDATE metadata SET value = 'webp' WHERE name = 'format'")
    with rasterio.open(sys.argv[2]) as src:
        if src.crs is None or not src.crs.is_geographic:
            sys.exit(f"{sys.argv[2]} is not in geographic coordinates")
        w, s, e, n = src.bounds
    min_z = db.execute("SELECT MIN(zoom_level) FROM tiles").fetchone()[0]
    db.execute("DELETE FROM metadata WHERE name IN ('bounds', 'center')")
    db.executemany("INSERT INTO metadata (name, value) VALUES (?, ?)", [
        ("bounds", f"{w:.6f},{s:.6f},{e:.6f},{n:.6f}"),
        ("center", f"{(w + e) / 2:.6f},{(s + n) / 2:.6f},{min_z}"),
    ])
    db.commit()
    db.execute("VACUUM")
    db.close()
    print(f"DEM: {len(rows)} tiles re-encoded as Terrarium WebP")


if __name__ == "__main__":
    main()
