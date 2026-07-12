#!/usr/bin/env python3
"""
Generate a mapsforge land/sea overlay PBF for a bounding box.

Coastal regions built WITHOUT contours (no ele_*_mix.pbf) still need sea
polygons in the mapsforge input: the kcwu elevation-mix files carry them for
normal regions (one natural=sea rectangle covering the bbox plus natural=nosea
land polygons, all layer=-5 — the OpenAndroMaps land/sea scheme, rendered via
the land_sea entries in osm_scripts/tag-mapping.xml). This tool produces the
same scheme directly from the OSM natural=coastline ways in the region
extract, using the OSM coastline convention: land on the LEFT, water on the
RIGHT of the way direction.

Usage:
    python3 tools/generate_landsea.py \
        --input build-<region>/latest-<Region>-sed.osm.pbf \
        --output build-<region>/landsea_<region>.osm.pbf \
        --left 29.99 --bottom 59.69 --right 30.62 --top 60.15

Exits with an error if the input contains no coastline inside the bbox —
landlocked regions must not enable LANDSEA.
"""

import argparse
import sys

import osmium
from shapely.geometry import LineString, Point, box
from shapely.ops import polygonize, unary_union

SIDE_EPS = 1e-6      # ~10 cm offset used to probe which side of a coastline a face is on
ON_BOUNDARY_EPS = 1e-9


class CoastlineReader(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def way(self, w):
        if w.tags.get('natural') != 'coastline':
            return
        try:
            coords = [(n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        if len(coords) >= 2:
            self.lines.append(coords)


def clip_coastlines(lines, bbox_poly):
    """Clip coastline ways to the bbox, preserving vertex order (direction)."""
    pieces = []
    for coords in lines:
        geom = LineString(coords).intersection(bbox_poly)
        if geom.is_empty:
            continue
        geoms = getattr(geom, 'geoms', [geom])
        for g in geoms:
            if g.geom_type == 'LineString' and len(g.coords) >= 2:
                pieces.append(g)
    return pieces


def face_signature(face):
    """All rings of a face, for boundary-membership tests."""
    return [face.exterior] + list(face.interiors)


def classify_face(face, pieces):
    """Return 'sea' or 'land' for a polygonized face, or None if undecided.

    A face is SEA when it lies on the right-hand side of a coastline piece on
    its boundary (OSM convention: water on the right).
    """
    rings = face_signature(face)
    for piece in pieces:
        coords = list(piece.coords)
        for i in range(len(coords) - 1):
            (x0, y0), (x1, y1) = coords[i], coords[i + 1]
            mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            mid = Point(mx, my)
            if not any(ring.distance(mid) < ON_BOUNDARY_EPS for ring in rings):
                continue
            dx, dy = x1 - x0, y1 - y0
            length = (dx * dx + dy * dy) ** 0.5
            if length == 0:
                continue
            # right-hand normal of the direction vector
            rx, ry = dy / length, -dx / length
            right_probe = Point(mx + SIDE_EPS * rx, my + SIDE_EPS * ry)
            left_probe = Point(mx - SIDE_EPS * rx, my - SIDE_EPS * ry)
            if face.contains(right_probe):
                return 'sea'
            if face.contains(left_probe):
                return 'land'
    return None


class PbfBuilder:
    """Accumulates dedup'd nodes and tagged ways/relations, writes a PBF."""

    def __init__(self):
        self.node_ids = {}
        self.nodes = []       # (id, lon, lat)
        self.ways = []        # (id, [node ids], {tags})
        self.relations = []   # (id, [(type, ref, role)], {tags})
        self._next_way = 1
        self._next_rel = 1

    def node_for(self, lon, lat):
        key = (round(lon, 7), round(lat, 7))
        nid = self.node_ids.get(key)
        if nid is None:
            nid = len(self.nodes) + 1
            self.node_ids[key] = nid
            self.nodes.append((nid, key[0], key[1]))
        return nid

    def add_ring(self, coords, tags):
        refs = [self.node_for(x, y) for x, y in coords]
        if refs[0] != refs[-1]:
            refs.append(refs[0])
        wid = self._next_way
        self._next_way += 1
        self.ways.append((wid, refs, tags))
        return wid

    def add_multipolygon(self, outer_id, inner_ids, tags):
        rid = self._next_rel
        self._next_rel += 1
        members = [('w', outer_id, 'outer')] + [('w', i, 'inner') for i in inner_ids]
        rel_tags = dict(tags)
        rel_tags['type'] = 'multipolygon'
        self.relations.append((rid, members, rel_tags))

    def write(self, path):
        writer = osmium.SimpleWriter(path)
        try:
            for nid, lon, lat in self.nodes:
                writer.add_node(osmium.osm.mutable.Node(id=nid, location=(lon, lat)))
            for wid, refs, tags in self.ways:
                writer.add_way(osmium.osm.mutable.Way(id=wid, nodes=refs, tags=tags))
            for rid, members, tags in self.relations:
                writer.add_relation(osmium.osm.mutable.Relation(id=rid, members=members, tags=tags))
        finally:
            writer.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--input', required=True, help='OSM extract (pbf) containing natural=coastline ways')
    ap.add_argument('--output', required=True, help='Output .osm.pbf with the land/sea scheme')
    ap.add_argument('--left', type=float, required=True)
    ap.add_argument('--bottom', type=float, required=True)
    ap.add_argument('--right', type=float, required=True)
    ap.add_argument('--top', type=float, required=True)
    args = ap.parse_args()

    bbox_poly = box(args.left, args.bottom, args.right, args.top)

    reader = CoastlineReader()
    reader.apply_file(args.input, locations=True, idx='flex_mem')
    print(f"coastline ways in extract: {len(reader.lines)}")

    pieces = clip_coastlines(reader.lines, bbox_poly)
    print(f"coastline pieces inside bbox: {len(pieces)}")
    if not pieces:
        print("ERROR: no natural=coastline inside the bounding box.", file=sys.stderr)
        print("This region looks landlocked - do not enable LANDSEA for it.", file=sys.stderr)
        return 1

    # Partition the bbox into faces along the coastline, then classify each
    # face by which side of the coastline it lies on.
    faces = list(polygonize(unary_union([bbox_poly.exterior] + pieces)))
    land, sea, undecided = [], 0, 0
    for face in faces:
        cls = classify_face(face, pieces)
        if cls == 'land':
            land.append(face)
        elif cls == 'sea':
            sea += 1
        else:
            undecided += 1
            land.append(face)  # safer to over-draw land than to flood it
    print(f"faces: {len(faces)} (land {len(land)}, sea {sea}, undecided->land {undecided})")
    if sea == 0:
        print("WARNING: no sea face found; output will render as all land.", file=sys.stderr)

    builder = PbfBuilder()
    tags_sea = {'natural': 'sea', 'area': 'yes', 'layer': '-5'}
    tags_land = {'natural': 'nosea', 'layer': '-5'}
    builder.add_ring(list(bbox_poly.exterior.coords), tags_sea)
    for face in land:
        outer_id = builder.add_ring(list(face.exterior.coords), tags_land)
        if face.interiors:
            inner_ids = [builder.add_ring(list(r.coords), {}) for r in face.interiors]
            builder.add_multipolygon(outer_id, inner_ids, tags_land)

    builder.write(args.output)
    land_area = sum(f.area for f in land)
    print(f"land coverage: {land_area / bbox_poly.area * 100:.1f}% of bbox")
    print(f"wrote {args.output}: {len(builder.nodes)} nodes, {len(builder.ways)} ways, "
          f"{len(builder.relations)} relations")
    return 0


if __name__ == '__main__':
    sys.exit(main())
