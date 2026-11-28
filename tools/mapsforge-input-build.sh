#!/bin/bash
#
# mapsforge-input-build.sh - Build Mapsforge PBF file with metadata and elevation
#
# Usage: mapsforge-input-build.sh <SED_PBF> <META> <ELEVATION_MIX> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <BUILD_DIR> <OUTPUT> [FRAME]
#
# This script:
# 1. Verifies reserved ID blocks are free in SED_PBF (same layout as osmium-append.sh)
# 2. Renumbers metadata / elevation mix (and frame) into their disjoint ID blocks
# 3. Clips each independent source in parallel with osmconvert (--out-o5m)
# 4. Merges all clipped sources (plus unclipped nosea land polygons and sea frame
#    when FRAME is set) in a single osmium merge with add_metadata=false
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

set -euo pipefail

SED_PBF="${1:-}"
META="${2:-}"
ELEVATION_MIX="${3:-}"
OSMCONVERT_CMD="${4:-}"
OSMCONVERT_BOUNDING="${5:-}"
BUILD_DIR="${6:-}"
OUTPUT="${7:-}"
FRAME="${8:-}"

if [ -z "$SED_PBF" ] || [ -z "$META" ] || [ -z "$OSMCONVERT_CMD" ] || [ -z "$BUILD_DIR" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 <SED_PBF> <META> <ELEVATION_MIX> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <BUILD_DIR> <OUTPUT> [FRAME]" >&2
    exit 1
fi

# ID block layout (must stay in sync with tools/osmium-append.sh)
BLOCK_SIZE=10000000000
MIX_BASE=110000000000
META_BASE=140000000000
FRAME_BASE=160000000000

TOOLS_DIR="$(dirname "$0")"
WORK_DIR="${OUTPUT}.work.$$"

# Ensure build directory exists
mkdir -p "$BUILD_DIR" "$WORK_DIR"

# Remove any existing output
rm -f "$OUTPUT"

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

check_target_blocks_free() {
    local target="$1"
    shift
    local t_n t_w t_r
    read -r t_n t_w t_r <<<"$(largest_ids "$target")"

    local probe_ids=()
    local probe_meta=()
    local entry ns base limit id
    for entry in "$@"; do
        IFS=: read -r ns base <<<"$entry"
        limit=$((base + BLOCK_SIZE))
        for id in "$t_n" "$t_w" "$t_r"; do
            if [ "$id" -ge "$base" ] && [ "$id" -lt "$limit" ]; then
                echo "error: ${target} already holds ids in the '${ns}' block [${base}, ${limit})" >&2
                return 1
            fi
        done
        if [ "$t_n" -ge "$limit" ] || [ "$t_w" -ge "$limit" ] || [ "$t_r" -ge "$limit" ]; then
            probe_ids+=("n$base" "w$base" "r$base")
            probe_meta+=("$ns:$base:$limit")
        fi
    done

    if [ "${#probe_ids[@]}" -gt 0 ]; then
        local probe
        probe="$(osmium getid --no-progress -f osm "$target" "${probe_ids[@]}" 2>/dev/null || true)"
        for entry in "${probe_meta[@]}"; do
            IFS=: read -r ns base limit <<<"$entry"
            if printf '%s' "$probe" | grep -qE "<(node|way|relation) id=\"${base}\""; then
                echo "error: ${target} already holds ids in the '${ns}' block [${base}, ${limit})" >&2
                return 1
            fi
        done
    fi
}

check_renumbered_within_block() {
    local file="$1" ns="$2" base="$3"
    local limit=$((base + BLOCK_SIZE))
    local a_n a_w a_r id
    read -r a_n a_w a_r <<<"$(largest_ids "$file")"
    for id in "$a_n" "$a_w" "$a_r"; do
        if [ "$id" -ge "$limit" ]; then
            echo "error: ${file} overflows the '${ns}' block [${base}, ${limit}); largest id ${id}" >&2
            return 1
        fi
    done
}

# Build list of reserved blocks to guard on SED_PBF
GUARD_BLOCKS=("meta:${META_BASE}")
if [ -n "$ELEVATION_MIX" ]; then
    GUARD_BLOCKS+=("mix:${MIX_BASE}")
fi
if [ -n "$FRAME" ]; then
    GUARD_BLOCKS+=("frame:${FRAME_BASE}")
fi

# Phase 1: run independent guards, renumbering, and clipping in parallel.
# Each source lives in its own disjoint ID block, so clipping them independently
# and merging once at the end produces the exact same output as merging first.
check_target_blocks_free "$SED_PBF" "${GUARD_BLOCKS[@]}" &
p_guard=$!

# Clip SED_PBF directly to uncompressed o5m (avoids single-threaded PBF recompression)
# shellcheck disable=SC2086
$OSMCONVERT_CMD $OSMCONVERT_BOUNDING "$SED_PBF" --out-o5m -o="$WORK_DIR/sed_clip.o5m" &
p_sedclip=$!

# Renumber, guard, and clip META
(
    echo "renumber ${META} into 'meta' block: ${META_BASE}"
    osmium renumber -s "${META_BASE},${META_BASE},${META_BASE}" "$META" -Oo "$WORK_DIR/meta_ren.pbf"
    check_renumbered_within_block "$WORK_DIR/meta_ren.pbf" meta "$META_BASE"
    # shellcheck disable=SC2086
    $OSMCONVERT_CMD $OSMCONVERT_BOUNDING "$WORK_DIR/meta_ren.pbf" --out-o5m -o="$WORK_DIR/meta_clip.o5m"
) &
p_meta=$!

p_sedls=""
if [ -n "$FRAME" ]; then
    osmium tags-filter -O -o "$WORK_DIR/sed_landsea.pbf" "$SED_PBF" w/natural=sea w/natural=nosea &
    p_sedls=$!
fi

p_mix=""
if [ -n "$ELEVATION_MIX" ]; then
    (
        echo "renumber ${ELEVATION_MIX} into 'mix' block: ${MIX_BASE}"
        osmium renumber -s "${MIX_BASE},${MIX_BASE},${MIX_BASE}" "$ELEVATION_MIX" -Oo "$WORK_DIR/mix_ren.pbf"
        check_renumbered_within_block "$WORK_DIR/mix_ren.pbf" mix "$MIX_BASE" &
        p_mixguard=$!

        if [ -n "$FRAME" ]; then
            osmium tags-filter -O -o "$WORK_DIR/mix_nosea.pbf" "$WORK_DIR/mix_ren.pbf" w/natural=nosea &
            p_mixnosea=$!
            osmium tags-filter -i -O -o "$WORK_DIR/mix_nosea_dropped.pbf" "$WORK_DIR/mix_ren.pbf" w/natural=sea
            # shellcheck disable=SC2086
            $OSMCONVERT_CMD $OSMCONVERT_BOUNDING "$WORK_DIR/mix_nosea_dropped.pbf" --out-o5m -o="$WORK_DIR/mix_clip.o5m"
            wait "$p_mixnosea"
        else
            # shellcheck disable=SC2086
            $OSMCONVERT_CMD $OSMCONVERT_BOUNDING "$WORK_DIR/mix_ren.pbf" --out-o5m -o="$WORK_DIR/mix_clip.o5m"
        fi
        wait "$p_mixguard"
    ) &
    p_mix=$!
fi

wait "$p_guard"
wait "$p_sedclip"
wait "$p_meta"
if [ -n "$p_sedls" ]; then
    wait "$p_sedls"
fi
if [ -n "$p_mix" ]; then
    wait "$p_mix"
fi

SED_CLIP="$WORK_DIR/sed_clip.o5m"
MERGE_INPUTS=()

if [ -n "$FRAME" ]; then
    IFS=, read -r F_LEFT F_BOTTOM F_RIGHT F_TOP <<<"$FRAME"
    NOSEA_WAYS=0

    # Handle the rare case where SED_PBF itself contains natural=sea or natural=nosea
    SED_LS_WAYS="$(osmium fileinfo -e -g data.count.ways "$WORK_DIR/sed_landsea.pbf")"
    if [ "$SED_LS_WAYS" -gt 0 ]; then
        osmium tags-filter -O -o "$WORK_DIR/sed_nosea.pbf" "$WORK_DIR/sed_landsea.pbf" w/natural=nosea
        SED_NOSEA_WAYS="$(osmium fileinfo -e -g data.count.ways "$WORK_DIR/sed_nosea.pbf")"
        if [ "$SED_NOSEA_WAYS" -gt 0 ]; then
            NOSEA_WAYS=$((NOSEA_WAYS + SED_NOSEA_WAYS))
            MERGE_INPUTS+=("$WORK_DIR/sed_nosea.pbf")
        fi
        osmium tags-filter -i -O -o "$WORK_DIR/sed_clip_nosea.pbf" "$SED_CLIP" w/natural=sea
        SED_CLIP="$WORK_DIR/sed_clip_nosea.pbf"
    fi

    if [ -n "$ELEVATION_MIX" ]; then
        MIX_NOSEA_WAYS="$(osmium fileinfo -e -g data.count.ways "$WORK_DIR/mix_nosea.pbf")"
        if [ "$MIX_NOSEA_WAYS" -gt 0 ]; then
            NOSEA_WAYS=$((NOSEA_WAYS + MIX_NOSEA_WAYS))
            MERGE_INPUTS+=("$WORK_DIR/mix_nosea.pbf")
        fi
    fi

    LAND_GRID=""
    if [ "$NOSEA_WAYS" -eq 0 ]; then
        LAND_GRID="--land-grid 0.1"
    fi

    # shellcheck disable=SC2086
    python3 "${TOOLS_DIR}/frame-landsea.py" "$F_LEFT" "$F_BOTTOM" "$F_RIGHT" "$F_TOP" \
        "$WORK_DIR/frame.osm" $LAND_GRID
    echo "renumber ${WORK_DIR}/frame.osm into 'frame' block: ${FRAME_BASE}"
    osmium renumber -s "${FRAME_BASE},${FRAME_BASE},${FRAME_BASE}" "$WORK_DIR/frame.osm" -Oo "$WORK_DIR/frame_ren.pbf"
    check_renumbered_within_block "$WORK_DIR/frame_ren.pbf" frame "$FRAME_BASE"
    MERGE_INPUTS+=("$WORK_DIR/frame_ren.pbf")
fi

MERGE_INPUTS=("$SED_CLIP" "$WORK_DIR/meta_clip.o5m" "${MERGE_INPUTS[@]}")
if [ -n "$ELEVATION_MIX" ]; then
    MERGE_INPUTS+=("$WORK_DIR/mix_clip.o5m")
fi

# Single multi-threaded merge directly into metadata-free PBF (equivalent to
# osmconvert --drop-version, without a second single-threaded PBF round-trip).
osmium merge -O -f pbf,add_metadata=false -o "$OUTPUT" "${MERGE_INPUTS[@]}"

echo "Mapsforge PBF created: $OUTPUT"
