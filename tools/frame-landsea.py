#!/usr/bin/env python3
"""Write the mapsforge sea frame as an OSM XML file.

Usage: frame-landsea.py LEFT BOTTOM RIGHT TOP OUTPUT [--land-grid DEG]

The frame is one natural=sea rectangle covering exactly LEFT,BOTTOM,RIGHT,TOP
(same tags as the taiwan-contour mix files). With --land-grid, the frame is
also covered by natural=nosea tiles of DEG degrees - for regions without any
land polygons (no mix / landsea file), so the map renders as land instead of
sea. Small tiles instead of one big rectangle: large rectangular nosea
polygons cause rendering artifacts in mapsforge (see taiwan-contour
regions/common.mk, inland regions).

Ids start at 1; the caller renumbers them into the 'frame' block
(tools/osmium-append.sh).
"""
import argparse

LANDSEA_TAGS = '<tag k="area" v="yes"/><tag k="layer" v="-5"/>'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('left', type=float)
    ap.add_argument('bottom', type=float)
    ap.add_argument('right', type=float)
    ap.add_argument('top', type=float)
    ap.add_argument('output')
    ap.add_argument('--land-grid', type=float)
    a = ap.parse_args()

    nodes, ways = [], []

    def rect(left, bottom, right, top, natural):
        base = len(nodes) + 1
        for lat, lon in ((bottom, left), (top, left), (top, right), (bottom, right)):
            nodes.append(f'  <node id="{len(nodes) + 1}" lat="{lat}" lon="{lon}"/>')
        refs = ''.join(f'<nd ref="{base + i}"/>' for i in (0, 1, 2, 3, 0))
        ways.append(f'  <way id="{len(ways) + 1}">{refs}'
                    f'{LANDSEA_TAGS}<tag k="natural" v="{natural}"/></way>')

    rect(a.left, a.bottom, a.right, a.top, 'sea')

    if a.land_grid:
        lon = a.left
        while lon < a.right - 1e-9:
            lon_end = min(round(lon + a.land_grid, 10), a.right)
            lat = a.bottom
            while lat < a.top - 1e-9:
                lat_end = min(round(lat + a.land_grid, 10), a.top)
                rect(lon, lat, lon_end, lat_end, 'nosea')
                lat = lat_end
            lon = lon_end

    with open(a.output, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<osm version="0.6" generator="frame-landsea.py">\n')
        f.write('\n'.join(nodes + ways) + '\n</osm>\n')


if __name__ == '__main__':
    main()
