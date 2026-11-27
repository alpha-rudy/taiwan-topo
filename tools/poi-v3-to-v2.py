#!/usr/bin/env python3
"""Lossless converter from a Mapsforge POI v3 SQLite database to POI v2.

Mapsforge POI v2 and v3 share the exact same category tree and POI rows,
differing only in:
  - `poi_index`: v3 uses a plain `(id, lat, lon)` table with B-tree indexes;
    v2 uses a SQLite R*Tree virtual table `(id, minLat, maxLat, minLon, maxLon)`.
  - `poi_data`: v3 adds a `normalized_name=...` line for diacritic-insensitive
    search, which v2 readers/converters do not expect.
  - `metadata`: `version` is `2` instead of `3`.

Usage:
    python3 tools/poi-v3-to-v2.py <input_v3.poi> <output_v2.poi>
"""

import os
import sqlite3
import sys


def _strip_normalized_name(data: str) -> str:
    if "normalized_name=" not in data:
        return data
    return "\r".join(
        line for line in data.split("\r") if not line.startswith("normalized_name=")
    )


def convert(src_path: str, dst_path: str) -> None:
    dst_dir = os.path.dirname(os.path.abspath(dst_path))
    os.makedirs(dst_dir, exist_ok=True)
    tmp_path = os.path.join(dst_dir, f".{os.path.basename(dst_path)}.{os.getpid()}.tmp")
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)

    src = sqlite3.connect(f"file:{src_path}?mode=ro", uri=True)
    dst = sqlite3.connect(tmp_path)
    try:
        dst.execute("PRAGMA synchronous = OFF")
        dst.execute("PRAGMA journal_mode = MEMORY")
        dst.executescript(
            """
            CREATE TABLE poi_categories (id INTEGER, name TEXT, parent INTEGER, PRIMARY KEY (id));
            CREATE TABLE poi_data (id INTEGER, data TEXT, PRIMARY KEY (id));
            CREATE TABLE poi_category_map (id INTEGER, category INTEGER, PRIMARY KEY (id, category));
            CREATE TABLE metadata (name TEXT, value TEXT);
            CREATE VIRTUAL TABLE poi_index USING rtree(id, minLat, maxLat, minLon, maxLon);
            """
        )

        dst.executemany(
            "INSERT INTO poi_categories VALUES (?, ?, ?)",
            src.execute("SELECT id, name, parent FROM poi_categories"),
        )
        dst.executemany(
            "INSERT INTO poi_category_map VALUES (?, ?)",
            src.execute("SELECT id, category FROM poi_category_map"),
        )
        dst.executemany(
            "INSERT INTO poi_index (id, minLat, maxLat, minLon, maxLon) VALUES (?, ?, ?, ?, ?)",
            ((pid, lat, lat, lon, lon) for pid, lat, lon in src.execute("SELECT id, lat, lon FROM poi_index")),
        )
        dst.executemany(
            "INSERT INTO poi_data VALUES (?, ?)",
            ((pid, _strip_normalized_name(data)) for pid, data in src.execute("SELECT id, data FROM poi_data")),
        )

        meta_rows = []
        for name, value in src.execute("SELECT name, value FROM metadata"):
            if name == "version":
                meta_rows.append(("version", "2"))
            elif name == "writer":
                meta_rows.append(("writer", f"{value} (converted to v2)"))
            else:
                meta_rows.append((name, value))
        dst.executemany("INSERT INTO metadata VALUES (?, ?)", meta_rows)

        dst.commit()
        dst.execute("PRAGMA journal_mode = DELETE")
        dst.execute("PRAGMA synchronous = FULL")
        count = dst.execute("SELECT count(*) FROM poi_data").fetchone()[0]
        dst.close()
        src.close()
        os.replace(tmp_path, dst_path)
        print(f"poi-v3-to-v2: converted {count} POIs -> {dst_path}")
    except Exception:
        dst.close()
        src.close()
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    convert(sys.argv[1], sys.argv[2])
