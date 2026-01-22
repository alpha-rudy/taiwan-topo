#!/bin/bash
# mapsforge-build.sh - Build mapsforge map using osmosis mapfile-writer
#
# This script consolidates the common osmosis mapfile-writer pattern used by
# gpx, with_gpx, gpx-2, and mapsforge targets.
#
# Usage: mapsforge-build.sh <input_pbf> <output_map> <osmosis_cmd> <osmosis_bounding> \
#                     <threads> <languages> <tag_conf> <comment> [extra_opts]
#
# Parameters:
#   input_pbf        - Input PBF file
#   output_map       - Output .map file
#   osmosis_cmd      - Path to osmosis command
#   osmosis_bounding - Osmosis bounding box options (can be empty)
#   threads          - Number of mapwriter threads
#   languages        - Preferred languages (e.g., "zh,en")
#   tag_conf         - Tag configuration XML file
#   comment          - Map comment string
#   extra_opts       - Extra mapfile-writer options (optional, e.g., "simplification-factor=2.5")

set -e

INPUT_PBF="$1"
OUTPUT_MAP="$2"
OSMOSIS_CMD="$3"
OSMOSIS_BOUNDING="$4"
THREADS="$5"
LANGUAGES="$6"
TAG_CONF="$7"
COMMENT="$8"
EXTRA_OPTS="$9"

if [ -z "$INPUT_PBF" ] || [ -z "$OUTPUT_MAP" ] || [ -z "$OSMOSIS_CMD" ]; then
    echo "Usage: $0 <input_pbf> <output_map> <osmosis_cmd> <osmosis_bounding> <threads> <languages> <tag_conf> <comment> [extra_opts]" >&2
    exit 1
fi

# Build extra options string
EXTRA_ARGS=""
if [ -n "$EXTRA_OPTS" ]; then
    EXTRA_ARGS="$EXTRA_OPTS"
fi

sh "$OSMOSIS_CMD" \
    --read-pbf "$INPUT_PBF" \
    $OSMOSIS_BOUNDING \
    --buffer \
    --mapfile-writer \
        type=ram \
        threads="$THREADS" \
        preferred-languages="$LANGUAGES" \
        tag-conf-file="$TAG_CONF" \
        polygon-clipping=true way-clipping=true label-position=true \
        zoom-interval-conf=6,0,6,10,7,11,14,12,21 \
        map-start-zoom=12 \
        $EXTRA_ARGS \
        comment="$COMMENT" \
        file="$OUTPUT_MAP"
