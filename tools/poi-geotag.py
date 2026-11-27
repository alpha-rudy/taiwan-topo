#!/usr/bin/env python3
"""Fast spatial geo-tagger for Mapsforge POI v3 SQLite databases.

Adds `is_in` (from `boundary=administrative`, admin_level 9/8/7) and
`addr:postcode` (from `boundary=postal_code`) tags to POIs inside a Mapsforge
POI v3 database, replacing mapsforge-poi-writer's O(polygons * POIs) SQLite
table-scan GeoTagger with a 2D spatial grid + vectorized ray-casting pass.

Usage:
    python3 tools/poi-geotag.py <input.osm.pbf> <poi_v3.poi>
"""

import multiprocessing
import os
import shutil
import sqlite3
import sys
import tempfile
from collections import defaultdict

import numpy as np
import osmium

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pbf_utils

ADMIN_LEVELS = (9, 8, 7)
GRID_DEG = 0.02

# Globals shared copy-on-write across forked workers
_NEEDED_NODES: set[int] = set()
_LATS: np.ndarray | None = None
_LONS: np.ndarray | None = None
_GRID: dict[tuple[int, int], np.ndarray] = {}


def _scan_node_shard(shard_path: str) -> dict[int, tuple[float, float]]:
    coords: dict[int, tuple[float, float]] = {}
    needed = _NEEDED_NODES
    for n in osmium.FileProcessor(shard_path, osmium.osm.NODE):
        if n.id in needed and n.location.valid():
            coords[n.id] = (n.location.lat, n.location.lon)
    return coords


def _stitch_rings(
    way_ids: list[int],
    way_nodes: dict[int, list[int]],
    node_coords: dict[int, tuple[float, float]],
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Assemble way node chains into closed `(lats, lons)` rings."""
    segments: list[list[int]] = []
    for wid in way_ids:
        nds = way_nodes.get(wid)
        if nds and len(nds) >= 2:
            segments.append(list(nds))

    rings: list[list[int]] = []
    # First separate already-closed ways
    open_segs: list[list[int]] = []
    for seg in segments:
        if seg[0] == seg[-1]:
            if len(seg) >= 4:
                rings.append(seg)
        else:
            open_segs.append(seg)

    # Chain open segments by matching endpoints
    endpoints: dict[int, list[int]] = defaultdict(list)
    used = [False] * len(open_segs)
    for idx, seg in enumerate(open_segs):
        endpoints[seg[0]].append(idx)
        endpoints[seg[-1]].append(idx)

    for start_idx in range(len(open_segs)):
        if used[start_idx]:
            continue
        used[start_idx] = True
        chain = list(open_segs[start_idx])
        while chain[0] != chain[-1]:
            tail = chain[-1]
            matched = -1
            for cand in endpoints.get(tail, ()):
                if not used[cand]:
                    matched = cand
                    break
            if matched < 0:
                break
            used[matched] = True
            seg = open_segs[matched]
            if seg[0] == tail:
                chain.extend(seg[1:])
            else:
                chain.extend(reversed(seg[:-1]))
        if chain[0] == chain[-1] and len(chain) >= 4:
            rings.append(chain)

    result: list[tuple[np.ndarray, np.ndarray]] = []
    for ring in rings:
        pts = [node_coords[nid] for nid in ring if nid in node_coords]
        if len(pts) < 4:
            continue
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        arr = np.asarray(pts, dtype=np.float64)
        result.append((arr[:, 0], arr[:, 1]))
    return result


def _points_in_ring(
    py: np.ndarray, px: np.ndarray, ry: np.ndarray, rx: np.ndarray
) -> np.ndarray:
    """Vectorized Jordan ray-casting test for `(py, px)` inside closed ring `(ry, rx)`."""
    inside = np.zeros(len(px), dtype=bool)
    n = len(rx) - 1
    for i in range(n):
        y1 = ry[i]
        y2 = ry[i + 1]
        x1 = rx[i]
        x2 = rx[i + 1]
        cond = (y1 > py) != (y2 > py)
        if not np.any(cond):
            continue
        idx = np.nonzero(cond)[0]
        x_int = x1 + (py[idx] - y1) * (x2 - x1) / (y2 - y1)
        cross = px[idx] < x_int
        inside[idx[cross]] ^= True
    return inside


def _eval_boundary_batch(
    batch: list[tuple[str, int, str, list[tuple[np.ndarray, np.ndarray]], list[tuple[np.ndarray, np.ndarray]]]],
) -> list[tuple[str, int, str, np.ndarray]]:
    assert _LATS is not None and _LONS is not None
    lats = _LATS
    lons = _LONS
    grid = _GRID
    out: list[tuple[str, int, str, np.ndarray]] = []

    for kind, level, label, outers, inners in batch:
        min_lat = min(float(r[0].min()) for r in outers)
        max_lat = max(float(r[0].max()) for r in outers)
        min_lon = min(float(r[1].min()) for r in outers)
        max_lon = max(float(r[1].max()) for r in outers)

        gy0 = int(np.floor(min_lat / GRID_DEG))
        gy1 = int(np.floor(max_lat / GRID_DEG))
        gx0 = int(np.floor(min_lon / GRID_DEG))
        gx1 = int(np.floor(max_lon / GRID_DEG))

        cand_chunks: list[np.ndarray] = []
        for gy in range(gy0, gy1 + 1):
            for gx in range(gx0, gx1 + 1):
                bucket = grid.get((gy, gx))
                if bucket is not None:
                    cand_chunks.append(bucket)
        if not cand_chunks:
            continue
        cands = cand_chunks[0] if len(cand_chunks) == 1 else np.concatenate(cand_chunks)

        clat = lats[cands]
        clon = lons[cands]
        bbox_mask = (
            (clat >= min_lat) & (clat <= max_lat) & (clon >= min_lon) & (clon <= max_lon)
        )
        if not np.any(bbox_mask):
            continue
        cands = cands[bbox_mask]
        clat = clat[bbox_mask]
        clon = clon[bbox_mask]

        hit = np.zeros(len(cands), dtype=bool)
        for ry, rx in outers:
            o_mask = (
                (clat >= ry.min()) & (clat <= ry.max()) & (clon >= rx.min()) & (clon <= rx.max())
            )
            if np.any(o_mask):
                oi = np.nonzero(o_mask)[0]
                in_r = _points_in_ring(clat[oi], clon[oi], ry, rx)
                hit[oi[in_r]] = True

        if not np.any(hit):
            continue

        if inners:
            hi = np.nonzero(hit)[0]
            hlat = clat[hi]
            hlon = clon[hi]
            for ry, rx in inners:
                i_mask = (
                    (hlat >= ry.min())
                    & (hlat <= ry.max())
                    & (hlon >= rx.min())
                    & (hlon <= rx.max())
                )
                if np.any(i_mask):
                    ii = np.nonzero(i_mask)[0]
                    in_hole = _points_in_ring(hlat[ii], hlon[ii], ry, rx)
                    hit[hi[ii[in_hole]]] = False

        matched = cands[hit]
        if len(matched) > 0:
            out.append((kind, level, label, matched))
    return out


def _extract_boundaries(pbf_path: str, workers: int):
    """Extract admin_level 9/8/7 and postal_code boundary polygons from an OSM file."""
    header_blocks: list[tuple[str, int, int, int, int]] = []
    data_blocks: list[tuple[str, int, int, int, int]] = []
    if pbf_path.endswith(".pbf"):
        blocks = pbf_utils.scan_pbf_blocks(pbf_path)
        header_blocks = [b for b in blocks if b[0] == "OSMHeader"]
        data_blocks = [b for b in blocks if b[0] == "OSMData"]
    use_pbf_slices = bool(header_blocks and data_blocks)

    tmp_dir = tempfile.mkdtemp(prefix=".poi_geotag_")
    try:
        first_way = 0
        if use_pbf_slices:
            with open(pbf_path, "rb") as src_f:
                first_way = pbf_utils.find_first_block_with_types(src_f, data_blocks, {"w", "r"})
                first_rel = pbf_utils.find_first_block_with_types(src_f, data_blocks, {"r"})
                rel_pbf = os.path.join(tmp_dir, "rels.osm.pbf")
                way_pbf = os.path.join(tmp_dir, "ways.osm.pbf")
                pbf_utils.write_pbf_block_slice(
                    src_f, header_blocks[0], data_blocks, first_rel, len(data_blocks), rel_pbf
                )
                pbf_utils.write_pbf_block_slice(
                    src_f, header_blocks[0], data_blocks, first_way, len(data_blocks), way_pbf
                )
        else:
            rel_pbf = pbf_path
            way_pbf = pbf_path

        # 1. Read relevant boundary relations
        relations: list[tuple[str, int, str, list[int], list[int]]] = []
        needed_ways: set[int] = set()
        admin_set = {str(lvl) for lvl in ADMIN_LEVELS}
        for r in osmium.FileProcessor(rel_pbf, osmium.osm.RELATION).with_filter(
            osmium.filter.KeyFilter("boundary")
        ):
            btype = r.tags.get("boundary")
            if btype == "administrative":
                al = r.tags.get("admin_level", "").strip()
                name = r.tags.get("name", "").strip()
                if al not in admin_set or not name:
                    continue
                kind = "admin"
                level = int(al)
                label = name
            elif btype == "postal_code":
                pc = (r.tags.get("postal_code") or r.tags.get("addr:postcode") or "").strip()
                if not pc:
                    continue
                kind = "postal"
                level = 0
                label = pc
            else:
                continue

            outers: list[int] = []
            inners: list[int] = []
            for m in r.members:
                if m.type != "w":
                    continue
                if m.role == "inner":
                    inners.append(m.ref)
                else:
                    outers.append(m.ref)
                needed_ways.add(m.ref)
            if outers:
                relations.append((kind, level, label, outers, inners))

        if not relations:
            return []

        # 2. Read only needed ways
        way_nodes: dict[int, list[int]] = {}
        needed_nodes: set[int] = set()
        for w in osmium.FileProcessor(way_pbf, osmium.osm.WAY):
            if w.id in needed_ways:
                nds = [n.ref for n in w.nodes]
                way_nodes[w.id] = nds
                needed_nodes.update(nds)

        # 3. Read coordinates for needed nodes (parallel over node blocks)
        global _NEEDED_NODES
        _NEEDED_NODES = needed_nodes
        node_end = min(len(data_blocks), first_way + 1) if use_pbf_slices else 0
        node_coords: dict[int, tuple[float, float]] = {}

        if use_pbf_slices and workers > 1 and node_end >= workers * 2 and hasattr(os, "fork"):
            num_chunks = min(node_end, workers * 4)
            base, extra = divmod(node_end, num_chunks)
            shard_paths: list[str] = []
            pos = 0
            with open(pbf_path, "rb") as src_f:
                for idx in range(num_chunks):
                    cnt = base + (1 if idx < extra else 0)
                    sp = os.path.join(tmp_dir, f"nodes_{idx:03d}.osm.pbf")
                    pbf_utils.write_pbf_block_slice(
                        src_f, header_blocks[0], data_blocks, pos, pos + cnt, sp
                    )
                    shard_paths.append(sp)
                    pos += cnt
            ctx = multiprocessing.get_context("fork")
            with ctx.Pool(workers) as pool:
                for partial in pool.imap_unordered(_scan_node_shard, shard_paths):
                    node_coords.update(partial)
        else:
            node_coords = _scan_node_shard(pbf_path)

        # 4. Stitch polygon rings
        polygons = []
        for kind, level, label, outer_wids, inner_wids in relations:
            outer_rings = _stitch_rings(outer_wids, way_nodes, node_coords)
            if not outer_rings:
                continue
            inner_rings = _stitch_rings(inner_wids, way_nodes, node_coords) if inner_wids else []
            polygons.append((kind, level, label, outer_rings, inner_rings))
        return polygons
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _apply_geotags(
    db: sqlite3.Connection,
    ids: np.ndarray,
    admin_hits: dict[int, list[tuple[int, str]]],
    postal_hits: dict[int, str],
) -> int:
    affected = sorted(set(admin_hits) | set(postal_hits))
    if not affected:
        return 0

    db.execute("PRAGMA synchronous = OFF")
    db.execute("PRAGMA journal_mode = MEMORY")

    # Fetch existing data for affected POIs in chunks
    updates: list[tuple[str, int]] = []
    batch_size = 50000
    for start in range(0, len(affected), batch_size):
        chunk = affected[start : start + batch_size]
        poi_ids = [int(ids[i]) for i in chunk]
        idx_by_poi_id = {int(ids[i]): i for i in chunk}
        placeholders = ",".join("?" * len(poi_ids))
        rows = db.execute(
            f"SELECT id, data FROM poi_data WHERE id IN ({placeholders})", poi_ids
        ).fetchall()
        for pid, data in rows:
            arr_idx = idx_by_poi_id[pid]
            lines = data.split("\r") if data else []
            tag_idx: dict[str, int] = {}
            for pos, line in enumerate(lines):
                if "=" in line:
                    k = line.split("=", 1)[0]
                    tag_idx[k] = pos

            changed = False
            if arr_idx in admin_hits:
                # Fine-to-coarse order (admin_level 9 -> 8 -> 7), deduplicated
                dedup: list[str] = []
                seen: set[str] = set()
                for _, name in sorted(admin_hits[arr_idx], key=lambda x: (-x[0], x[1])):
                    if name not in seen:
                        seen.add(name)
                        dedup.append(name)
                if "is_in" in tag_idx:
                    existing_val = lines[tag_idx["is_in"]].split("=", 1)[1]
                    existing_parts = [p.strip() for p in existing_val.split(",") if p.strip()]
                    existing_set = set(existing_parts)
                    additions = [n for n in dedup if n not in existing_set]
                    if additions:
                        lines[tag_idx["is_in"]] = "is_in=" + ",".join(additions + existing_parts)
                        changed = True
                else:
                    lines.append("is_in=" + ",".join(dedup))
                    changed = True

            if arr_idx in postal_hits and "addr:postcode" not in tag_idx:
                lines.append("addr:postcode=" + postal_hits[arr_idx])
                changed = True

            if changed:
                updates.append(("\r".join(lines), pid))

    db.executemany("UPDATE poi_data SET data = ? WHERE id = ?", updates)
    db.commit()
    db.execute("PRAGMA journal_mode = DELETE")
    db.execute("PRAGMA synchronous = FULL")
    return len(updates)


def main(pbf_path: str, poi_db_path: str) -> None:
    workers = max(1, int(os.environ.get("POI_WORKERS") or os.cpu_count() or 1))
    polygons = _extract_boundaries(pbf_path, workers)
    if not polygons:
        print("poi-geotag: no administrative/postal boundaries found")
        return

    db = sqlite3.connect(poi_db_path)
    try:
        rows = db.execute("SELECT id, lat, lon FROM poi_index").fetchall()
        if not rows:
            return
        ids = np.fromiter((r[0] for r in rows), dtype=np.int64, count=len(rows))
        lats = np.fromiter((r[1] for r in rows), dtype=np.float64, count=len(rows))
        lons = np.fromiter((r[2] for r in rows), dtype=np.float64, count=len(rows))

        # Build 2D spatial grid index
        gys = np.floor(lats / GRID_DEG).astype(np.int32)
        gxs = np.floor(lons / GRID_DEG).astype(np.int32)
        grid_lists: dict[tuple[int, int], list[int]] = defaultdict(list)
        for idx, (gy, gx) in enumerate(zip(gys.tolist(), gxs.tolist())):
            grid_lists[(gy, gx)].append(idx)
        grid = {k: np.asarray(v, dtype=np.int32) for k, v in grid_lists.items()}

        global _LATS, _LONS, _GRID
        _LATS = lats
        _LONS = lons
        _GRID = grid

        # Distribute polygons in batches across workers
        batch_size = max(1, len(polygons) // (workers * 8))
        batches = [polygons[i : i + batch_size] for i in range(0, len(polygons), batch_size)]

        admin_hits: dict[int, list[tuple[int, str]]] = defaultdict(list)
        postal_hits: dict[int, str] = {}

        if workers > 1 and len(batches) > 1 and hasattr(os, "fork"):
            ctx = multiprocessing.get_context("fork")
            with ctx.Pool(workers) as pool:
                for batch_res in pool.imap_unordered(_eval_boundary_batch, batches):
                    for kind, level, label, matched in batch_res:
                        if kind == "admin":
                            for idx in matched.tolist():
                                admin_hits[idx].append((level, label))
                        else:
                            for idx in matched.tolist():
                                postal_hits.setdefault(idx, label)
        else:
            for batch in batches:
                for kind, level, label, matched in _eval_boundary_batch(batch):
                    if kind == "admin":
                        for idx in matched.tolist():
                            admin_hits[idx].append((level, label))
                    else:
                        for idx in matched.tolist():
                            postal_hits.setdefault(idx, label)

        updated = _apply_geotags(db, ids, admin_hits, postal_hits)
        print(
            f"poi-geotag: {len(polygons)} boundaries matched {updated} / {len(ids)} POIs"
        )
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
