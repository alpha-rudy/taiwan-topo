#!/usr/bin/env python3
"""pmtiles-zoom-shift.py - Publish a PMTiles style half a zoom level early.

style.json and paper.json are written in theme zooms minus one: MapLibre's
512 px tiles show at zoom Z what Mapsforge's 256 px tiles show at Z + 1. A map
of the same theme drawn as 256 px raster tiles (the Mapsforge renderer's
tiles in MapLibre or Leaflet) does not switch at whole zooms, though: MapLibre
picks a raster tile zoom by rounding, so from Z - 0.5 on it already shows the
next zoom's tiles, scaled down. Next to such a map the vector style shows each
theme zoom half a level late: between Z.5 and Z+1 it lacks the peaks, trail
names and distance marks the raster map has.

This moves every zoom in a style by the same amount: each layer's minzoom and
maxzoom, the stops of zoom-driven interpolate and step expressions, and zoom
comparisons in filters, whether against a number or against the zoom a
feature carries (["get", "minzoom"]). The source styles keep their theme-minus-one zooms,
so they still derive from the theme as they are (make paper_style checks it).
The tiles carry each feature one zoom before its first style zoom
(osm_scripts/pmtiles/process.lua TILE_LEAD), so the earlier zooms have their
data: the map draws zoom Z with the tiles of floor(Z).

Usage: pmtiles-zoom-shift.py <shift> <input style.json> <output style.json>
"""

import json
import sys

COMPARE = {"==", "!=", "<", "<=", ">", ">="}


def is_zoom(x):
    return x == ["zoom"]


def shift_expr(e, d):
    """The expression e with every zoom it is driven by moved by -d."""
    if isinstance(e, dict):
        if "stops" in e:  # a legacy function: not written by this repo's tools
            raise ValueError("legacy zoom function: %s" % json.dumps(e)[:80])
        return {k: shift_expr(v, d) for k, v in e.items()}
    if not isinstance(e, list) or not e:
        return e
    op = e[0]
    if op == "interpolate" and len(e) > 3 and is_zoom(e[2]):
        out = [op, e[1], e[2]]
        for i in range(3, len(e), 2):
            out += [e[i] - d, shift_expr(e[i + 1], d)]
        return out
    if op == "step" and len(e) > 2 and is_zoom(e[1]):
        out = [op, e[1], shift_expr(e[2], d)]
        for i in range(3, len(e), 2):
            out += [e[i] - d, shift_expr(e[i + 1], d)]
        return out
    if op in COMPARE and len(e) == 3 and (is_zoom(e[1]) or is_zoom(e[2])):
        # against a number, or against a feature's own zoom (["get", "minzoom"])
        a, b = (shift_expr(x, d) for x in e[1:])
        moved = lambda x: x - d if isinstance(x, (int, float)) else ["-", x, d] if d else x
        return [op, a, moved(b)] if is_zoom(a) else [op, moved(a), b]
    if any(is_zoom(x) for x in e[1:]):
        # a zoom read some other way: this tool would leave it behind
        raise ValueError("unhandled zoom expression: %s" % json.dumps(e)[:80])
    return [shift_expr(x, d) for x in e]


def shift_style(style, d):
    for lay in style["layers"]:
        if lay.get("minzoom", 0) > 0:
            lay["minzoom"] = max(lay["minzoom"] - d, 0)
        if "maxzoom" in lay:
            lay["maxzoom"] = lay["maxzoom"] - d
        for part in ("filter", "paint", "layout"):
            if part in lay:
                lay[part] = shift_expr(lay[part], d)
    return style


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    with open(sys.argv[2], encoding="utf-8") as f:
        style = json.load(f)
    shift_style(style, float(sys.argv[1]))
    with open(sys.argv[3], "w", encoding="utf-8") as f:
        json.dump(style, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
