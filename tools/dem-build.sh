#!/bin/bash
# dem-build.sh - Build terrain-RGB PMTiles from a HGT elevation zip.
#
# Pipeline: HGT zip → gdalbuildvrt → rio-rgbify (terrain-RGB MBTiles) → go-pmtiles convert
#
# The output PMTiles uses Mapbox terrain-RGB encoding (R,G,B channels encode
# elevation) and is readable by MapLibre GL JS raster-dem sources.
#
# Usage: dem-build.sh <hgt_zip> <output_pmtiles> <gopmtiles_cmd> [min_z] [max_z]
#
# Parameters:
#   hgt_zip         - ZIP file containing *.hgt elevation tiles
#   output_pmtiles  - Output .pmtiles file (directory will be created)
#   gopmtiles_cmd   - Path to go-pmtiles binary (or "pmtiles" if on PATH)
#   min_z           - Minimum output zoom (default: 6)
#   max_z           - Maximum output zoom (default: 13)
#
# Dependencies (must be on PATH or pre-installed):
#   gdalbuildvrt    - from gdal-bin (Ubuntu: apt-get install gdal-bin)
#   rio rgbify      - from rio-rgbify (pip3 install rio-rgbify)
#   go-pmtiles      - from <gopmtiles_cmd> parameter

set -eo pipefail

HGT_ZIP="$1"
OUTPUT_PMTILES="$2"
GOPMTILES_CMD="$3"
MIN_Z="${4:-6}"
MAX_Z="${5:-13}"

if [ -z "$HGT_ZIP" ] || [ -z "$OUTPUT_PMTILES" ] || [ -z "$GOPMTILES_CMD" ]; then
    echo "Usage: $0 <hgt_zip> <output_pmtiles> <gopmtiles_cmd> [min_z] [max_z]" >&2
    exit 1
fi

if [ ! -f "$HGT_ZIP" ]; then
    echo "ERROR: HGT zip not found: $HGT_ZIP" >&2; exit 1
fi
if [ ! -x "$GOPMTILES_CMD" ] && ! command -v "$GOPMTILES_CMD" >/dev/null 2>&1; then
    echo "ERROR: go-pmtiles not found: $GOPMTILES_CMD" >&2; exit 1
fi

WORK_DIR="$(dirname "$OUTPUT_PMTILES")"
STEM="$(basename "$OUTPUT_PMTILES" .pmtiles)"
VRT="$WORK_DIR/$STEM.vrt"
MBTILES="$WORK_DIR/$STEM.mbtiles"
TMP_HGT="$WORK_DIR/.${STEM}_hgt_tmp"

mkdir -p "$WORK_DIR"

cleanup() {
    rm -rf "$TMP_HGT"
    rm -f "$MBTILES"
}
trap cleanup EXIT

echo "DEM: unzipping HGT tiles..."
rm -rf "$TMP_HGT"
mkdir -p "$TMP_HGT"
unzip -j "$HGT_ZIP" '*.hgt' -d "$TMP_HGT"

echo "DEM: building GDAL VRT mosaic..."
gdalbuildvrt "$VRT" "$TMP_HGT"/*.hgt

# rio is rasterio's CLI. A pip rasterio installs a `rio` executable, but the
# Debian python3-rasterio package (used in the Docker image) does not. Its
# rasterio.rio.main module has no __main__ block, so `python3 -m rasterio.rio.main`
# is a silent no-op; call main_group() explicitly instead. rio-rgbify registers
# its `rgbify` subcommand into that group either way.
if command -v rio >/dev/null 2>&1; then
    RIO_CMD=(rio)
elif python3 -c 'from rasterio.rio.main import main_group' >/dev/null 2>&1; then
    RIO_CMD=(python3 -c 'from rasterio.rio.main import main_group; main_group()')
else
    echo "ERROR: rio CLI not found (need rasterio + rio-rgbify)." >&2; exit 1
fi

echo "DEM: running rio-rgbify (z${MIN_Z}-${MAX_Z}, terrain-RGB PNG)..."
# rio-rgbify writes every output tile as an in-memory dataset with no
# geotransform, so rasterio emits one NotGeoreferencedWarning per tile
# (thousands of lines). Filter by message text, not category: a category
# filter (ignore::rasterio.errors.NotGeoreferencedWarning) is parsed at
# interpreter startup and fails to import rasterio then ("invalid -W option"),
# so it silently does nothing. A message regex needs no import and just works.
PYTHONWARNINGS="ignore:Dataset has no geotransform" \
"${RIO_CMD[@]}" rgbify \
    --min-z "$MIN_Z" \
    --max-z "$MAX_Z" \
    "$VRT" "$MBTILES"

echo "DEM: converting MBTiles → PMTiles..."
rm -f "$OUTPUT_PMTILES"
"$GOPMTILES_CMD" convert "$MBTILES" "$OUTPUT_PMTILES"

test -s "$OUTPUT_PMTILES" || { echo "ERROR: output PMTiles is empty: $OUTPUT_PMTILES" >&2; exit 1; }
echo "DEM: done — $OUTPUT_PMTILES ($(du -sh "$OUTPUT_PMTILES" | cut -f1))"
