#!/bin/bash
# pmtiles-build.sh - Build PMTiles vector tiles using tilemaker.
#
# Mirrors tools/mapsforge-build.sh: consumes the already-prepared OSM PBF
# ($(MAPSFORGE_PBF)) and renders it to a single .pmtiles archive using the
# custom topo schema in osm_scripts/pmtiles/.
#
# Two adaptations are needed before tilemaker can read the prepared PBF:
#   1. tilemaker's node store streams data in type+id order, but the prepared
#      PBF is not sorted (elevation/meta blocks are appended), so we sort it
#      first with osmium.
#   2. The PBF contains a few dangling node references (the upstream osmosis
#      step keeps incomplete entities). Rather than rewrite the data, we pass
#      tilemaker --skip-integrity so it tolerates the missing refs.
#   3. The contour and elevation payload carries node ids far above OSM's
#      (around 1.6e11 for a region with contours), past what tilemaker's
#      sorted node store can index: it aborts with "SortedNodeStore: unexpected
#      groupIndex". The sorted PBF is renumbered from 1 with osmium, which
#      keeps the order and every reference; the vector schema carries no ids.
#   4. tilemaker refuses ways of more than 2,000 nodes, and the natural=nosea
#      land polygons of the land/sea scheme are kept whole, so a coastline
#      ring can be far longer. tools/split-long-ways.py turns each such ring
#      into chained pieces under a multipolygon relation.
#
# One layer does not come from process.lua: route_label, the hiking-route
# captions, needs each way's bounding-box centre, which tilemaker's Lua API
# cannot compute. tools/route-labels.py writes those points as GeoJSON and the
# config's "__route_labels__" placeholder is replaced with that file's path.
#
# Usage: pmtiles-build.sh <input_pbf> <output_pmtiles> <tilemaker_cmd> \
#                         <config_json> <process_lua> <version> [bbox] [extra_opts]
#
# Parameters:
#   input_pbf       - Input OSM PBF file (region-clipped, already prepared)
#   output_pmtiles  - Output .pmtiles file
#   tilemaker_cmd   - Path to the tilemaker binary
#   config_json     - tilemaker layer config. Any "__version__" placeholder is
#                     substituted with <version>, "__route_labels__" with the
#                     route label GeoJSON written by tools/route-labels.py.
#   process_lua     - tilemaker profile (process.lua)
#   version         - Build version string (substituted into the config)
#   bbox            - Optional "minlon,minlat,maxlon,maxlat". If empty, it is
#                     derived from the sorted PBF's data extent (the prepared
#                     PBF has no bbox in its header).
#   extra_opts      - Optional extra tilemaker flags (e.g. "--store /path")
#
# The archive's JSON metadata also carries "version": <version>, the same
# string as the map's version stamp and the style zip's version.txt, so an app
# can tell whether an archive and a style come from the same build. tilemaker
# 3.1 writes only name, description, attribution and vector_layers to PMTiles
# metadata (a "version" in the config is dropped), so it is added afterwards
# with go-pmtiles' edit ($GOPMTILES_CMD, default "pmtiles").
#
# Every region draws with one shared style (rudymap_pmtiles_style.zip), so what
# differs per region travels in the archive's own metadata instead:
#   PMTILES_ATTRIBUTION  replaces "attribution", e.g. naming the region's DEM.
#   PMTILES_DEM          the region's DEM archive: "taiwan-topo:dem_version" is the
#                        first 16 hex digits of its SHA-256. The DEM build is
#                        deterministic, so this changes only when the elevations
#                        do; an app can skip downloading the DEM while it stays
#                        the same, and check a downloaded DEM against it.

set -e

INPUT_PBF="$1"
OUTPUT_PMTILES="$2"
TILEMAKER_CMD="$3"
CONFIG_JSON="$4"
PROCESS_LUA="$5"
VERSION="$6"
BBOX="$7"
EXTRA_OPTS="$8"

OSMIUM_CMD="${OSMIUM_CMD:-osmium}"
GOPMTILES_CMD="${GOPMTILES_CMD:-pmtiles}"

if [ -z "$INPUT_PBF" ] || [ -z "$OUTPUT_PMTILES" ] || [ -z "$TILEMAKER_CMD" ] \
   || [ -z "$CONFIG_JSON" ] || [ -z "$PROCESS_LUA" ]; then
    echo "Usage: $0 <input_pbf> <output_pmtiles> <tilemaker_cmd> <config_json> <process_lua> <version> [bbox] [extra_opts]" >&2
    exit 1
fi

if [ ! -x "$TILEMAKER_CMD" ] && ! command -v "$TILEMAKER_CMD" >/dev/null 2>&1; then
    echo "ERROR: tilemaker not found/executable at '$TILEMAKER_CMD'." >&2
    echo "       See tools/tilemaker/README.md for how to install/vendor it." >&2
    exit 1
fi

CONFIG_RUNTIME="$CONFIG_JSON"
SORTED_PBF="${OUTPUT_PMTILES%.pmtiles}.sort.tmp.pbf"
RENUMBERED_PBF="${OUTPUT_PMTILES%.pmtiles}.renum.tmp.pbf"
SPLIT_PBF="${OUTPUT_PMTILES%.pmtiles}.split.tmp.pbf"
ROUTE_LABELS="$(cd "$(dirname "$OUTPUT_PMTILES")" && pwd)/$(basename "${OUTPUT_PMTILES%.pmtiles}").route-labels.tmp.geojson"
METADATA_JSON="${OUTPUT_PMTILES%.pmtiles}.metadata.tmp.json"
cleanup() { rm -f "$SORTED_PBF" "$RENUMBERED_PBF" "$SPLIT_PBF" "$ROUTE_LABELS" "$METADATA_JSON"; [ "$CONFIG_RUNTIME" != "$CONFIG_JSON" ] && rm -f "$CONFIG_RUNTIME"; }
trap cleanup EXIT

# tilemaker reads several config strings (name/version/description) without
# null-checking and segfaults if any is absent. Substitute the build version
# into a temp copy so the placeholder is never left empty, and the route
# label file's absolute path (tilemaker resolves a relative source against its
# working directory).
if grep -q -e '__version__' -e '__route_labels__' "$CONFIG_JSON"; then
    CONFIG_RUNTIME="$(mktemp "${TMPDIR:-/tmp}/pmtiles-config.XXXXXX.json")"
    sed -e "s/__version__/${VERSION:-dev}/g" \
        -e "s|__route_labels__|${ROUTE_LABELS}|g" "$CONFIG_JSON" > "$CONFIG_RUNTIME"
fi

# 1. Sort into tilemaker's expected type+id order.
"$OSMIUM_CMD" sort "$INPUT_PBF" -o "$SORTED_PBF" -O

# 2. Renumber from 1 so tilemaker's node store can index every node.
"$OSMIUM_CMD" renumber "$SORTED_PBF" -o "$RENUMBERED_PBF" -O
rm -f "$SORTED_PBF"

# 3. Split rings longer than tilemaker's 2,000-node limit.
python3 "$(dirname "$0")/split-long-ways.py" "$RENUMBERED_PBF" "$SPLIT_PBF"
rm -f "$RENUMBERED_PBF"

# 3b. Route label points (see the note above).
python3 "$(dirname "$0")/route-labels.py" "$SPLIT_PBF" "$ROUTE_LABELS"

# 4. Derive the bounding box from the data if not supplied (the prepared PBF
#    has no bbox in its header). osmium prints "(minlon,minlat,maxlon,maxlat)";
#    strip the parentheses for tilemaker.
if [ -z "$BBOX" ]; then
    BBOX="$("$OSMIUM_CMD" fileinfo -e -g data.bbox "$SPLIT_PBF" | tr -d '()')"
fi

rm -f "$OUTPUT_PMTILES"

# --skip-integrity: tolerate the dangling node references noted above.
"$TILEMAKER_CMD" \
    --input "$SPLIT_PBF" \
    --output "$OUTPUT_PMTILES" \
    --config "$CONFIG_RUNTIME" \
    --process "$PROCESS_LUA" \
    --bbox "$BBOX" \
    --skip-integrity \
    $EXTRA_OPTS

test -s "$OUTPUT_PMTILES" || { echo "ERROR: tilemaker produced no output ($OUTPUT_PMTILES)" >&2; exit 1; }

# 5. The build version, attribution and DEM version in the archive's metadata
#    (see the notes above).
"$GOPMTILES_CMD" show --metadata "$OUTPUT_PMTILES" > "$METADATA_JSON"
python3 - "$METADATA_JSON" "${VERSION:-dev}" <<'PY'
import hashlib, json, os, sys
path, version = sys.argv[1:3]
with open(path) as f:
    meta = json.load(f)
meta["version"] = version
if os.environ.get("PMTILES_ATTRIBUTION"):
    meta["attribution"] = os.environ["PMTILES_ATTRIBUTION"]
dem = os.environ.get("PMTILES_DEM")
if dem:
    if not os.path.isfile(dem) or os.path.getsize(dem) == 0:
        sys.exit("DEM archive missing or empty: %s" % dem)
    h = hashlib.sha256()
    with open(dem, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    meta["taiwan-topo:dem_version"] = h.hexdigest()[:16]
with open(path, "w") as f:
    json.dump(meta, f, ensure_ascii=False)
PY
"$GOPMTILES_CMD" edit --quiet "$OUTPUT_PMTILES" --metadata="$METADATA_JSON"
