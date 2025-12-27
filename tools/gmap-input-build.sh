#!/bin/bash
#
# gmap-input-build.sh - Build Garmin map input file with elevation data
#
# Usage: gmap-input-build.sh <REGION_EXTRACT_NAME> <ELEVATION> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <BUILD_DIR> <OUTPUT>
#
# This script:
# 1. Copies the region extract
# 2. Appends elevation data using osmium
# 3. Converts to final format with osmconvert
#

set -e

REGION_EXTRACT_NAME="$1"
ELEVATION="$2"
OSMCONVERT_CMD="$3"
OSMCONVERT_BOUNDING="$4"
BUILD_DIR="$5"
OUTPUT="$6"

if [ -z "$REGION_EXTRACT_NAME" ] || [ -z "$ELEVATION" ] || [ -z "$OSMCONVERT_CMD" ] || [ -z "$BUILD_DIR" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 <REGION_EXTRACT_NAME> <ELEVATION> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <BUILD_DIR> <OUTPUT>"
    exit 1
fi

TOOLS_DIR="$(dirname "$0")"
TEMP_FILE="${OUTPUT}.o5m"

# Ensure build directory exists
mkdir -p "$BUILD_DIR"

# Remove any existing output
rm -f "$OUTPUT"

# Copy source file
cp "${REGION_EXTRACT_NAME}.o5m" "$TEMP_FILE"

# Append elevation data
bash "${TOOLS_DIR}/osmium-append.sh" "$TEMP_FILE" "$ELEVATION"

# Convert to final format with bounding
$OSMCONVERT_CMD \
    --drop-version \
    $OSMCONVERT_BOUNDING \
    "$TEMP_FILE" \
    -o="$OUTPUT"

# Cleanup temporary file
rm -f "$TEMP_FILE"

echo "Garmin map input created: $OUTPUT"
