#!/bin/bash
#
# gmap-input-build.sh - Build Garmin map input file with elevation data
#
# Usage: gmap-input-build.sh <REGION_EXTRACT_NAME> <ELEVATION> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <BUILD_DIR> <OUTPUT>
#
# This script:
# 1. Verifies the reserved contour ID block is free in the region extract
# 2. Renumbers elevation data into the disjoint contour ID block (100e9)
# 3. Clips extract and elevation in parallel with osmconvert (--drop-version --out-o5m)
# 4. Merges directly into the final .o5m output without intermediate PBF recompression
#

set -euo pipefail

REGION_EXTRACT_NAME="${1:-}"
ELEVATION="${2:-}"
OSMCONVERT_CMD="${3:-}"
OSMCONVERT_BOUNDING="${4:-}"
BUILD_DIR="${5:-}"
OUTPUT="${6:-}"

if [ -z "$REGION_EXTRACT_NAME" ] || [ -z "$OSMCONVERT_CMD" ] || [ -z "$BUILD_DIR" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 <REGION_EXTRACT_NAME> <ELEVATION> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <BUILD_DIR> <OUTPUT>" >&2
    exit 1
fi

# ID block layout (must stay in sync with tools/osmium-append.sh)
CONTOUR_BASE=100000000000
BLOCK_SIZE=10000000000
CONTOUR_LIMIT=$((CONTOUR_BASE + BLOCK_SIZE))

if [ -f "${REGION_EXTRACT_NAME}.osm.pbf" ]; then
    SRC_FILE="${REGION_EXTRACT_NAME}.osm.pbf"
else
    SRC_FILE="${REGION_EXTRACT_NAME}.o5m"
fi

# Ensure build directory exists
mkdir -p "$BUILD_DIR"
rm -f "$OUTPUT"

# Fast path when no contour data is configured: clip directly into OUTPUT.
if [ -z "$ELEVATION" ]; then
    # shellcheck disable=SC2086
    $OSMCONVERT_CMD --drop-version $OSMCONVERT_BOUNDING "$SRC_FILE" -o="$OUTPUT"
    echo "Garmin map input created: $OUTPUT"
    exit 0
fi

WORK_DIR="${OUTPUT}.work.$$"
mkdir -p "$WORK_DIR"
kill_tree() {
    local pid="$1" children child
    children="$(pgrep -P "$pid" 2>/dev/null || true)"
    kill "$pid" 2>/dev/null || true
    for child in $children; do
        kill_tree "$child"
    done
}

cleanup() {
    local pid
    for pid in $(jobs -p 2>/dev/null || true); do
        kill_tree "$pid"
    done
    wait 2>/dev/null || true
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT

largest_ids() {
    local info n w r
    info=$(osmium fileinfo -e "$1")
    n=$(printf '%s\n' "$info" | sed -n 's/.*Largest node ID: \([0-9]*\).*/\1/p')
    w=$(printf '%s\n' "$info" | sed -n 's/.*Largest way ID: \([0-9]*\).*/\1/p')
    r=$(printf '%s\n' "$info" | sed -n 's/.*Largest relation ID: \([0-9]*\).*/\1/p')
    echo "${n:-0} ${w:-0} ${r:-0}"
}

check_contour_block_free() {
    local target="$1"
    local t_n t_w t_r id
    read -r t_n t_w t_r <<<"$(largest_ids "$target")"
    for id in "$t_n" "$t_w" "$t_r"; do
        if [ "$id" -ge "$CONTOUR_BASE" ] && [ "$id" -lt "$CONTOUR_LIMIT" ]; then
            echo "error: ${target} already holds ids in the 'contour' block [${CONTOUR_BASE}, ${CONTOUR_LIMIT})" >&2
            return 1
        fi
    done
    if [ "$t_n" -ge "$CONTOUR_LIMIT" ] || [ "$t_w" -ge "$CONTOUR_LIMIT" ] || [ "$t_r" -ge "$CONTOUR_LIMIT" ]; then
        local probe
        probe="$(osmium getid --no-progress -f osm "$target" "n${CONTOUR_BASE}" "w${CONTOUR_BASE}" "r${CONTOUR_BASE}" 2>/dev/null || true)"
        if printf '%s' "$probe" | grep -qE "<(node|way|relation) id=\"${CONTOUR_BASE}\""; then
            echo "error: ${target} already holds ids in the 'contour' block [${CONTOUR_BASE}, ${CONTOUR_LIMIT})" >&2
            return 1
        fi
    fi
}

# Phase 1: guard check, source clip, and elevation renumber+clip in parallel.
check_contour_block_free "$SRC_FILE" &
p_guard=$!

# shellcheck disable=SC2086
$OSMCONVERT_CMD --drop-version $OSMCONVERT_BOUNDING "$SRC_FILE" --out-o5m -o="$WORK_DIR/src_clip.o5m" &
p_src=$!

(
    echo "renumber ${ELEVATION} into 'contour' block: ${CONTOUR_BASE}"
    osmium renumber -s "${CONTOUR_BASE},${CONTOUR_BASE},${CONTOUR_BASE}" "$ELEVATION" -Oo "$WORK_DIR/ele_ren.pbf"
    read -r a_n a_w a_r <<<"$(largest_ids "$WORK_DIR/ele_ren.pbf")"
    for id in "$a_n" "$a_w" "$a_r"; do
        if [ "$id" -ge "$CONTOUR_LIMIT" ]; then
            echo "error: ${ELEVATION} overflows the 'contour' block [${CONTOUR_BASE}, ${CONTOUR_LIMIT}); largest id ${id}" >&2
            exit 1
        fi
    done
    # shellcheck disable=SC2086
    $OSMCONVERT_CMD --drop-version $OSMCONVERT_BOUNDING "$WORK_DIR/ele_ren.pbf" --out-o5m -o="$WORK_DIR/ele_clip.o5m"
) &
p_ele=$!

wait "$p_guard"
wait "$p_src"
wait "$p_ele"

# Phase 2: merge both clipped .o5m files directly into final .o5m output
# without any intermediate PBF compression/decompression round-trip.
$OSMCONVERT_CMD "$WORK_DIR/src_clip.o5m" "$WORK_DIR/ele_clip.o5m" --out-o5m -o="$OUTPUT"

echo "Garmin map input created: $OUTPUT"
