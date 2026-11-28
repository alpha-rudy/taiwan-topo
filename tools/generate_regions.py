#!/usr/bin/env python3
"""Write rudymap_regions.json: every region, its files and the shared themes and styles.

A web page or an app reads this one list to learn which regions there are,
what each one's files are called and where it lies, instead of deriving names
from the suites or keeping its own copy. Only what any downstream can use is
listed: Mapsforge (map, theme, HGT elevations, POI) and PMTiles (archive, DEM,
the shared style). Locus, Cartograph and Garmin files have installers of their
own and are left out. Versions are not here either: regions are built at
different times, so a downstream reads them from each file (HEAD for size and
modification time, the archive's metadata once it has the file).

A region is listed when its suite file (suites/<id>/<id>.mk) names it with
REGION_NAME_ZH and REGION_NAME_EN. Its Lite map comes from <id>_lite.mk beside
it. Everything else is read from the suite files, so the list follows the
suites and any build can publish the same list (Taiwan's weekly install does).

What a downstream can rely on:
- Every "id" (a region's, a map's, a theme's, a style's, a package's) stays
  the same; a downstream may store them. A package's "map" and "theme", and a
  map's "themes", are ids: of the region's mapsforge.maps and of the top-level
  mapsforge.themes.
- "schema_version" goes up only with a change a reader of the old shape would
  misread (a field renamed, removed or given another meaning). New fields do
  not raise it; a downstream ignores fields it does not know.
- pmtiles.styles names files inside rudymap_pmtiles_style.zip, which are also
  in the unpacked rudymap_pmtiles_style/ folder beside it.
- A file listed may not exist yet: the list follows the suites, and a region
  not rebuilt since a target was added has no such file (a 404) until it is.
- Whether an archive and a style can be drawn together is in the files' own
  metadata ("taiwan-topo:schema"), not here: the balancer sends each file to a
  mirror up to date for that file, so the list and a file may be of different
  weeks. If the list ever carries the code (pmtiles.schema), it only helps
  decide whether to download.

Usage: generate_regions.py [-o OUT.json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SUITES_DIR = ROOT_DIR / "suites"
SCHEMA_VERSION = 1

# The Mapsforge themes every region draws with (the style targets in the
# Makefile write these names whatever the region). Locus's and Cartograph's
# own themes are left out.
THEMES = [
    {"id": "rudy", "file": "MOI_OSM_Taiwan_TOPO_Rudy_style.zip", "hillshading": False},
    {"id": "rudy-hs", "file": "MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip", "hillshading": True, "default": True},
    {"id": "lite", "file": "MOI_OSM_Taiwan_TOPO_Lite_style.zip"},
    {"id": "twmap", "file": "MOI_OSM_twmap_style.zip"},
    {"id": "bn", "file": "MOI_OSM_bn_style.zip", "overlay": True},
    {"id": "dn", "file": "MOI_OSM_dn_style.zip", "overlay": True},
    {"id": "tn", "file": "MOI_OSM_tn_style.zip", "overlay": True},
]
# what each Makefile style variable a suite's GTS_STYLE names packs
GTS_THEMES = {"$(HS_STYLE)": "rudy-hs", "$(LITE_STYLE)": "lite", "$(MAPSFORGE_STYLE)": "rudy"}
MAP_THEMES = {"rudy": ["rudy", "rudy-hs", "twmap", "bn", "dn", "tn"], "lite": ["lite"]}
PMTILES = {
    "style": "rudymap_pmtiles_style.zip",
    "styles": [
        {"id": "rudy", "file": "style.json", "default": True},
        {"id": "paper", "file": "paper.json"},
    ],
}


def suite_vars(path):
    """The variables a suite file sets inside its ifeq block (VAR := value or VAR = value)."""
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0]  # a trailing make comment is not part of the value
        m = re.match(r"^([A-Z][A-Z0-9_]*)\s*:?=\s*(.*?)\s*$", line)
        if m and m.group(1) not in found:
            found[m.group(1)] = m.group(2)
    return found


def expand(value, v, where):
    """value with the suite file's own variables filled in; one left over is an error."""
    out = re.sub(r"\$\((\w+)\)", lambda m: v.get(m.group(1), m.group(0)), value)
    if "$(" in out:
        raise ValueError("%s: cannot expand %r" % (where, value))
    return out


def mapsforge_map(map_id, v, where):
    """The map, its package (gts_all) and its HGT, from one suite file's variables."""
    name = expand(v["NAME_MAPSFORGE"], v, where)
    targets = v.get("TARGETS", "").split()
    # only the file name is listed; the directory ($(ROOT_DIR)/hgt) is the build's
    hgt = Path(v["HGT"]).name if v.get("HGT") else None
    entry = {"id": map_id, "file": name + ".map.zip", "themes": MAP_THEMES[map_id]}
    package = None
    if "gts_all" in targets:
        theme = GTS_THEMES.get(v.get("GTS_STYLE", ""))
        if not theme:
            raise ValueError("%s: GTS_STYLE %r is not a theme the list knows" % (where, v.get("GTS_STYLE")))
        package = {"id": map_id, "file": name + ".zip", "map": map_id, "theme": theme, "dem": hgt}
    return entry, package, hgt, name, targets


def region(suite_dir):
    mk = suite_dir / (suite_dir.name + ".mk")
    v = suite_vars(mk)
    names = [v.get("REGION_NAME_ZH"), v.get("REGION_NAME_EN")]
    if not any(names):
        return None
    if not all(names):
        raise ValueError("%s: REGION_NAME_ZH and REGION_NAME_EN go together" % mk)
    main, main_pkg, main_hgt, name, targets = mapsforge_map("rudy", v, mk)
    main["default"] = True
    maps, packages, dems = [main], [main_pkg], [main_hgt]
    lite_mk = suite_dir / (suite_dir.name + "_lite.mk")
    if lite_mk.exists():
        lite, lite_pkg, lite_hgt, _, _ = mapsforge_map("lite", suite_vars(lite_mk), lite_mk)
        maps.append(lite)
        packages.append(lite_pkg)
        dems.append(lite_hgt)
    packages = [p for p in packages if p]
    dems = [d for d in dict.fromkeys(dems) if d]
    mapsforge = {"maps": maps, "packages": packages, "dem": dems or None,
                 "poi": name + ".poi.zip" if "poi_zip" in targets else None}
    pmtiles = None
    if "pmtiles" in targets:
        pmtiles = {"maps": [{"id": "rudy", "file": name + ".pmtiles", "default": True}],
                   "dem": v["REGION"].lower() + "_dem.pmtiles" if "dem" in targets else None}
    return {
        "id": suite_dir.name,
        "name": {"zh": v["REGION_NAME_ZH"], "en": v["REGION_NAME_EN"]},
        # [west, south, east, north], WGS84
        "bounds": [float(v["LEFT"]), float(v["BOTTOM"]), float(v["RIGHT"]), float(v["TOP"])],
        "mapsforge": mapsforge,
        "pmtiles": pmtiles,
    }


def regions():
    found = [region(d) for d in sorted(SUITES_DIR.iterdir())
             if d.is_dir() and (d / (d.name + ".mk")).exists()]
    return [r for r in found if r]


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("-o", "--output", help="write here instead of standard output")
    args = parser.parse_args(argv)
    doc = {"schema_version": SCHEMA_VERSION, "mapsforge": {"themes": THEMES}, "pmtiles": PMTILES,
           "regions": regions()}
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    print(f"regions: {len(doc['regions'])} listed", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
