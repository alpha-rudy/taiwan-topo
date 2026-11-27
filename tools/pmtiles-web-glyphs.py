#!/usr/bin/env python3
"""Add the glyph ranges a web page needs to the unpacked PMTiles style folder.

Copies each range listed in RANGES_FILE (one "start-end" per line, "#" starts
a comment) of every fontstack already in OUT_GLYPHS_DIR (the ones the styles
name, put there by pmtiles-style-pack.py) from GLYPHS_DIR. Only the folder
install publishes gets them; the style zip keeps its Latin ranges, since an
app draws the rest with the phone's own font. A range missing from GLYPHS_DIR
stops the run: a page that cannot read one range fails the whole tile.

Usage: pmtiles-web-glyphs.py OUT_GLYPHS_DIR GLYPHS_DIR RANGES_FILE
"""
import os
import shutil
import sys


def main(argv):
    if len(argv) != 3:
        sys.exit(__doc__)
    out_dir, glyphs_dir, ranges_file = argv
    with open(ranges_file) as f:
        ranges = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    if not ranges:
        sys.exit("no ranges in " + ranges_file)
    fonts = sorted(d for d in os.listdir(out_dir) if os.path.isdir(os.path.join(out_dir, d)))
    if not fonts:
        sys.exit("no fontstacks in " + out_dir)
    missing = []
    copied = 0
    for font in fonts:
        for r in ranges:
            src = os.path.join(glyphs_dir, font, r + ".pbf")
            if not os.path.isfile(src) or os.path.getsize(src) == 0:
                missing.append(src)
                continue
            shutil.copy(src, os.path.join(out_dir, font))
            copied += 1
    if missing:
        sys.exit("missing glyphs: " + ", ".join(missing))
    print("pmtiles web glyphs: %d ranges x fontstacks %s (%d files)"
          % (len(ranges), fonts, copied), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
