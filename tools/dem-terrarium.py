#!/usr/bin/env python3
"""Re-encode a Mapbox terrain-RGB MBTiles (rio rgbify -b -10000 -i 0.1) in
place as Terrarium-encoded lossless WebP, the format style.json declares for
its raster-dem source ("encoding": "terrarium").

Terrarium stores whole metres in R and G (elevation + 32768 = R * 256 + G)
and the fraction in B. rio rgbify resamples bilinearly into the HGT's own
integer type (int16), so every value it writes is a whole metre: B is always
0, and the tiles compress to well under half the Mapbox PNGs with the same elevations.
A tile whose elevations are not whole metres is an error, not rounded away.

Usage: dem-terrarium.py <tiles.mbtiles>
"""
import io
import sqlite3
import sys

import numpy as np
from PIL import Image


def main():
    db = sqlite3.connect(sys.argv[1])
    rows = db.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles").fetchall()
    for z, x, y, data in rows:
        rgb = np.asarray(Image.open(io.BytesIO(data)).convert("RGB")).astype(np.int64)
        tenths = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]   # (h + 10000) * 10
        if np.any(tenths % 10):
            sys.exit("tile %d/%d/%d has elevations that are not whole metres" % (z, x, y))
        v = tenths // 10 - 10000 + 32768
        out = np.stack([v >> 8, v & 255, np.zeros_like(v)], -1).astype(np.uint8)
        buf = io.BytesIO()
        Image.fromarray(out, "RGB").save(buf, "WEBP", lossless=True, quality=100, method=6)
        db.execute("UPDATE tiles SET tile_data = ? WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
                   (buf.getvalue(), z, x, y))
    db.execute("UPDATE metadata SET value = 'webp' WHERE name = 'format'")
    db.commit()
    db.execute("VACUUM")
    db.close()
    print("DEM: %d tiles re-encoded as Terrarium WebP" % len(rows))


if __name__ == "__main__":
    main()
