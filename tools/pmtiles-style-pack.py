#!/usr/bin/env python3
"""Fill the PMTiles style zip's folder: the styles, their Latin glyphs, the version.

Writes each style into OUT_DIR with metadata "taiwan-topo:version" set to
VERSION, copies the glyph ranges RANGES (comma-separated, e.g. 0-255) of every
fontstack the styles name from GLYPHS_DIR into OUT_DIR/glyphs/<fontstack>/,
and writes VERSION to OUT_DIR/version.txt. An offline app draws CJK text with
the phone's own font, so only the Latin ranges travel with the styles; a
fontstack or range missing from GLYPHS_DIR stops the run.

Every region draws with these styles, so nothing in them is per region: the
DEM's content version is in each archive's metadata (tools/pmtiles-build.sh).

Usage: pmtiles-style-pack.py OUT_DIR VERSION GLYPHS_DIR RANGES STYLE.json...
"""
import json
import os
import shutil
import sys


def main(argv):
    if len(argv) < 5 or not argv[1]:
        sys.exit(__doc__)
    out_dir, version, glyphs_dir, ranges = argv[:4]
    styles = argv[4:]
    fonts = set()
    for path in styles:
        with open(path) as f:
            style = json.load(f)
        style.setdefault("metadata", {})["taiwan-topo:version"] = version
        for layer in style["layers"]:
            stack = layer.get("layout", {}).get("text-font")
            if stack:
                fonts.add(",".join(stack))
        with open(os.path.join(out_dir, os.path.basename(path)), "w") as f:
            json.dump(style, f, ensure_ascii=False)
    missing = []
    for font in sorted(fonts):
        os.makedirs(os.path.join(out_dir, "glyphs", font), exist_ok=True)
        for r in ranges.split(","):
            src = os.path.join(glyphs_dir, font, r + ".pbf")
            if not os.path.isfile(src) or os.path.getsize(src) == 0:
                missing.append(src)
                continue
            shutil.copy(src, os.path.join(out_dir, "glyphs", font))
    if missing:
        sys.exit("missing glyphs: " + ", ".join(missing))
    with open(os.path.join(out_dir, "version.txt"), "w") as f:
        f.write(version + "\n")
    print("pmtiles style pack: %d styles, fontstacks %s, version %s"
          % (len(styles), sorted(fonts), version), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
