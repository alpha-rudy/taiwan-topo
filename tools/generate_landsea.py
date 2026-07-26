#!/usr/bin/env python3
"""
Generate a mapsforge land/sea overlay PBF for a bounding box.

Coastal regions built WITHOUT contours (no ele_*_mix.pbf) still need sea
polygons in the mapsforge input: the kcwu elevation-mix files carry them for
normal regions (one natural=sea rectangle covering the bbox plus natural=nosea
land polygons, all layer=-5 -- the OpenAndroMaps land/sea scheme, rendered via
the land_sea entries in osm_scripts/tag-mapping.xml). This tool reproduces the
same scheme using the same method as the (sibling project) taiwan-contour's
tools/sealand-creator.sh: clip the authoritative OSM land-polygons dataset
(https://osmdata.openstreetmap.de/data/land-polygons.html) to the bbox for
"nosea" land, and lay a single fixed rectangle covering the whole bbox
underneath as "sea" -- the sea is never computed, only the land shape is.

Usage:
    python3 tools/generate_landsea.py \
        --land-polygons download/land-polygons/land-polygons-split-4326/land_polygons.shp \
        --output build-<region>/landsea_<region>.osm.pbf \
        --left 29.99 --bottom 59.69 --right 30.62 --top 60.15
"""

import argparse
import sys

import osmium
from osgeo import ogr


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

    def add_multipolygon(self, outer_ids, inner_ids):
        rid = self._next_rel
        self._next_rel += 1
        members = [('w', i, 'outer') for i in outer_ids] + [('w', i, 'inner') for i in inner_ids]
        self.relations.append((rid, members, {'type': 'multipolygon'}))

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


def add_polygon(builder, polygon, tags):
    """Add one OGR Polygon geometry as a tagged outer way, plus a multipolygon
    relation if it has holes (matching taiwan-contour's shape2osm.py: tags on
    the outer way, holes grouped via a bare type=multipolygon relation)."""
    ring_count = polygon.GetGeometryCount()
    if ring_count == 0:
        return
    exterior = polygon.GetGeometryRef(0)
    outer_id = builder.add_ring(exterior.GetPoints(), tags)
    if ring_count > 1:
        inner_ids = [builder.add_ring(polygon.GetGeometryRef(i).GetPoints(), {})
                     for i in range(1, ring_count)]
        builder.add_multipolygon([outer_id], inner_ids)


def add_clipped_geometry(builder, geom, tags):
    """geom may be Polygon, MultiPolygon, or a GeometryCollection produced by
    Intersection() mixing polygons with degenerate points/lines at the clip
    boundary -- only the polygonal parts are kept."""
    gtype = geom.GetGeometryType()
    flat_type = ogr.GT_Flatten(gtype)
    if flat_type == ogr.wkbPolygon:
        add_polygon(builder, geom, tags)
    elif flat_type in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection):
        for i in range(geom.GetGeometryCount()):
            add_clipped_geometry(builder, geom.GetGeometryRef(i), tags)
    # else: point/line degenerate intersection artifact -- ignore


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--land-polygons', required=True,
                     help='Path to land_polygons.shp from the OSM land-polygons-split-4326 dataset')
    ap.add_argument('--output', required=True, help='Output .osm.pbf with the land/sea scheme')
    ap.add_argument('--left', type=float, required=True)
    ap.add_argument('--bottom', type=float, required=True)
    ap.add_argument('--right', type=float, required=True)
    ap.add_argument('--top', type=float, required=True)
    args = ap.parse_args()

    bbox_coords = [(args.left, args.bottom), (args.left, args.top),
                   (args.right, args.top), (args.right, args.bottom), (args.left, args.bottom)]
    bbox_wkt = "POLYGON((" + ",".join(f"{x} {y}" for x, y in bbox_coords) + "))"
    bbox_geom = ogr.CreateGeometryFromWkt(bbox_wkt)

    ds = ogr.Open(args.land_polygons)
    if ds is None:
        print(f"ERROR: could not open {args.land_polygons}", file=sys.stderr)
        return 1
    layer = ds.GetLayer(0)
    layer.SetSpatialFilterRect(args.left, args.bottom, args.right, args.top)

    builder = PbfBuilder()
    land_tags = {'natural': 'nosea', 'layer': '-5'}
    land_count = 0
    for feature in layer:
        clipped = feature.GetGeometryRef().Intersection(bbox_geom)
        if clipped is None or clipped.IsEmpty():
            continue
        add_clipped_geometry(builder, clipped, land_tags)
        land_count += 1
    print(f"land polygon features clipped into bbox: {land_count}")

    # Sea is always the full bbox rectangle -- land (nosea) polygons draw over
    # it, exactly like the kcwu ele_*_mix.pbf files (verified: one natural=sea
    # rectangle plus many natural=nosea polygons, both layer=-5, no relations
    # unless a land polygon has holes).
    builder.add_ring(bbox_coords, {'natural': 'sea', 'area': 'yes', 'layer': '-5'})

    if land_count == 0:
        print("WARNING: no land polygons found in this bbox -- it may be entirely "
              "open ocean, or LANDSEA may not be needed if this region is inland.",
              file=sys.stderr)

    builder.write(args.output)
    print(f"wrote {args.output}: {len(builder.nodes)} nodes, {len(builder.ways)} ways, "
          f"{len(builder.relations)} relations")
    return 0


if __name__ == '__main__':
    sys.exit(main())
