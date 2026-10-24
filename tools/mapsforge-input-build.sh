#!/bin/bash
#
# mapsforge-input-build.sh - Build Mapsforge PBF file with metadata and elevation
#
# Usage: mapsforge-input-build.sh <SED_PBF> <META> <ELEVATION_MIX> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <BUILD_DIR> <OUTPUT> [FRAME]
#
# This script:
# 1. Copies the sed-processed PBF
# 2. Appends metadata
# 3. Appends elevation mix data
# 4. Converts to final format with osmconvert
#
# FRAME (left,bottom,right,top) is the map frame. Every map gets a natural=sea
# rectangle that is exactly the frame (tools/frame-landsea.py), and the
# land-sea layer is exempt from the OSMCONVERT_BOUNDING clip:
#  - any natural=sea in the input (mix / landsea file) is replaced by the frame
#  - natural=nosea land polygons are all kept, whole and unclipped (the
#    mapsforge writer / tilemaker bbox clips them to the frame)
#  - without any nosea in the input (no mix / landsea file, e.g. moscow) the
#    frame is covered by 0.1 deg nosea tiles, so the map renders as land
# A polygon clip (POLY_FILE) would otherwise drop the sea rectangle, whose
# corners all lie outside the polygon, and the land outside the polygon.
#

set -e

SED_PBF="$1"
META="$2"
ELEVATION_MIX="$3"
OSMCONVERT_CMD="$4"
OSMCONVERT_BOUNDING="$5"
BUILD_DIR="$6"
OUTPUT="$7"
FRAME="$8"

if [ -z "$SED_PBF" ] || [ -z "$META" ] || [ -z "$OSMCONVERT_CMD" ] || [ -z "$BUILD_DIR" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 <SED_PBF> <META> <ELEVATION_MIX> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <BUILD_DIR> <OUTPUT>"
    exit 1
fi

TOOLS_DIR="$(dirname "$0")"
TEMP_FILE="${OUTPUT}.pbf"

# Ensure build directory exists
mkdir -p "$BUILD_DIR"

# Remove any existing output
rm -f "$OUTPUT"

# Copy source file
cp "$SED_PBF" "$TEMP_FILE"

# Append metadata
OSMCONVERT_CMD="$OSMCONVERT_CMD" bash "${TOOLS_DIR}/osmium-append.sh" "$TEMP_FILE" "$META" meta

# Append elevation mix data (skipped when no contour data is configured)
if [ -n "$ELEVATION_MIX" ]; then
    OSMCONVERT_CMD="$OSMCONVERT_CMD" bash "${TOOLS_DIR}/osmium-append.sh" "$TEMP_FILE" "$ELEVATION_MIX" mix
fi

NOSEA_FILE="${OUTPUT}.nosea.pbf"
CLIP_FILE="${OUTPUT}.clip.pbf"
REST_FILE="${OUTPUT}.rest.pbf"
FRAME_FILE="${OUTPUT}.frame.osm"
cleanup() {
    rm -f "$TEMP_FILE" "$NOSEA_FILE" \
        "$CLIP_FILE" "$REST_FILE" "$FRAME_FILE"
}
trap cleanup EXIT

if [ -n "$FRAME" ]; then
    IFS=, read -r F_LEFT F_BOTTOM F_RIGHT F_TOP <<<"$FRAME"

    # all land polygons, kept whole and unclipped: a polygon can cover the
    # frame without any of its nodes inside it (a 1 deg land tile around a
    # small poly region), so a node-based clip would drop it. The mapsforge
    # writer / tilemaker bbox (the frame) clips them.
    osmium tags-filter -O -o "$NOSEA_FILE" "$TEMP_FILE" w/natural=nosea
    LAND_GRID=""
    if [ "$(osmium fileinfo -e -g data.count.ways "$NOSEA_FILE")" -eq 0 ]; then
        rm -f "$NOSEA_FILE"
        LAND_GRID="--land-grid 0.1"
    fi

    # everything else is clipped as usual; any sea area in the input is dropped
    # (the frame replaces it)
    $OSMCONVERT_CMD $OSMCONVERT_BOUNDING "$TEMP_FILE" -o="$CLIP_FILE"
    osmium tags-filter -i -O -o "$REST_FILE" "$CLIP_FILE" w/natural=sea
    if [ -f "$NOSEA_FILE" ]; then
        osmium merge -O -o "$CLIP_FILE" "$REST_FILE" "$NOSEA_FILE"
    else
        mv "$REST_FILE" "$CLIP_FILE"
    fi

    python3 "${TOOLS_DIR}/frame-landsea.py" "$F_LEFT" "$F_BOTTOM" "$F_RIGHT" "$F_TOP" \
        "$FRAME_FILE" $LAND_GRID
    OSMCONVERT_CMD="$OSMCONVERT_CMD" bash "${TOOLS_DIR}/osmium-append.sh" "$CLIP_FILE" "$FRAME_FILE" frame

    $OSMCONVERT_CMD --drop-version "$CLIP_FILE" -o="$OUTPUT"
else
    # Convert to final format with bounding
    $OSMCONVERT_CMD \
        --drop-version \
        $OSMCONVERT_BOUNDING \
        "$TEMP_FILE" \
        -o="$OUTPUT"
fi

echo "Mapsforge PBF created: $OUTPUT"
