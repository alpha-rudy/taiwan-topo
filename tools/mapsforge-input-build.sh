#!/bin/bash
#
# mapsforge-input-build.sh - Build Mapsforge PBF file with metadata and elevation
#
# Usage: mapsforge-input-build.sh <SED_PBF> <META> <ELEVATION_MIX> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <BUILD_DIR> <OUTPUT>
#
# This script:
# 1. Copies the sed-processed PBF
# 2. Appends metadata
# 3. Appends elevation mix data
# 4. Converts to final format with osmconvert
#

set -e

SED_PBF="$1"
META="$2"
ELEVATION_MIX="$3"
OSMCONVERT_CMD="$4"
OSMCONVERT_BOUNDING="$5"
BUILD_DIR="$6"
OUTPUT="$7"

if [ -z "$SED_PBF" ] || [ -z "$META" ] || [ -z "$ELEVATION_MIX" ] || [ -z "$OSMCONVERT_CMD" ] || [ -z "$BUILD_DIR" ] || [ -z "$OUTPUT" ]; then
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
bash "${TOOLS_DIR}/osmium-append.sh" "$TEMP_FILE" "$META"

# Append elevation mix data
bash "${TOOLS_DIR}/osmium-append.sh" "$TEMP_FILE" "$ELEVATION_MIX"

# Convert to final format with bounding
$OSMCONVERT_CMD \
    --drop-version \
    $OSMCONVERT_BOUNDING \
    "$TEMP_FILE" \
    -o="$OUTPUT"

# Cleanup temporary file
rm -f "$TEMP_FILE"

echo "Mapsforge PBF created: $OUTPUT"
