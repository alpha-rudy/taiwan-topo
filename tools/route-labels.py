#!/usr/bin/env python3
"""
Write one label point per hiking-route way, at the centre of its bounding box.

The Mapsforge theme writes a hiking route's ref as a caption (rules 602 and
603 of styles/mapsforge_style/MOI_OSM.xml): once per way, level, at the centre
of the way's bounding box. The PMTiles style draws the same captions from the
route_label point layer, and this script makes those points.

tilemaker cannot place them itself: LayerAsCentroid treats an open way as a
polygon, so a two-node way lands on one of its ends and a curved way lands
inside the curve, and its Lua API gives no access to the way's coordinates.
tilemaker reads this script's GeoJSON as the route_label layer's source
instead (see osm_scripts/pmtiles/config.json and tools/pmtiles-build.sh).

The ways chosen are the ones osm_scripts/pmtiles/process.lua draws as hiking
routes (hknetwork in the hiking networks, or highlight=yes) that also have a
ref and are neither a tunnel nor an area, as the theme's caption rules test.
Each point carries network (when it is a hiking network), highlight (when
yes) and ref, as the style's filters expect. The centre is taken in Web
Mercator, the projection the theme's renderer measures the box in.

Usage:
    python3 tools/route-labels.py <input.pbf> <output.geojson>
"""

import json
import math
import sys

import osmium

HIKING_NETWORKS = {"iwn", "nwn", "rwn", "lwn", "uwn"}


def unset(value):
    """True for a tunnel/area tag that does not make the way one."""
    return value is None or value == "" or value == "no"


def mercator_mid_lat(lat_a, lat_b):
    """The latitude halfway between two latitudes in Web Mercator y."""
    def y(lat):
        return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    mid = (y(lat_a) + y(lat_b)) / 2
    return math.degrees(2 * math.atan(math.exp(mid)) - math.pi / 2)


def label(way):
    """The label feature for a way, or None when the way gets no label."""
    tags = way.tags
    network = tags.get("hknetwork")
    highlight = tags.get("highlight") == "yes"
    in_network = network in HIKING_NETWORKS
    if not (in_network or highlight):
        return None
    ref = tags.get("ref")
    if not ref or not unset(tags.get("tunnel")) or not unset(tags.get("area")):
        return None
    lons, lats = [], []
    for node in way.nodes:
        if node.location.valid():
            lons.append(node.location.lon)
            lats.append(node.location.lat)
    if not lons:
        return None
    lon = (min(lons) + max(lons)) / 2
    lat = mercator_mid_lat(min(lats), max(lats))
    props = {}
    if in_network:
        props["network"] = network
    if highlight:
        props["highlight"] = "yes"
    props["ref"] = ref
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [round(lon, 7), round(lat, 7)]},
        "properties": props,
    }


def main(src, dst):
    features = []
    missing = 0
    fp = (osmium.FileProcessor(src, osmium.osm.NODE | osmium.osm.WAY)
          .with_locations()
          .with_filter(osmium.filter.EntityFilter(osmium.osm.WAY))
          .with_filter(osmium.filter.KeyFilter("ref")))
    for way in fp:
        feature = label(way)
        if feature is None:
            continue
        features.append(feature)
        if any(not n.location.valid() for n in way.nodes):
            missing += 1
    with open(dst, "w", encoding="utf-8") as out:
        json.dump({"type": "FeatureCollection", "features": features}, out,
                  ensure_ascii=False, separators=(",", ":"))
    print(f"route-labels: {len(features)} points"
          + (f" ({missing} ways with nodes missing from the file)" if missing else ""),
          file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
