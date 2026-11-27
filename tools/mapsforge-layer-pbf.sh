#!/bin/bash
#
# mapsforge-layer-pbf.sh - Build single-layer Mapsforge input PBF for mftool merge
#
# Usage:
#   mapsforge-layer-pbf.sh mix <ELEVATION_MIX> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <OUTPUT> [FRAME]
#   mapsforge-layer-pbf.sh osm <SED_PBF> <META> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <OUTPUT> [FRAME]
#
# Splitting the static elevation/landsea/frame layer ('mix') from the dynamic
# OSM+meta layer ('osm') allows caching the compiled elevation .map across builds
# and combining both layers with `mftool merge` in a few seconds.
#

set -euo pipefail

MODE="${1:-}"
shift || true

# ID block layout (must stay in sync with tools/osmium-append.sh)
BLOCK_SIZE=10000000000
MIX_BASE=110000000000
META_BASE=140000000000
FRAME_BASE=160000000000

TOOLS_DIR="$(dirname "$0")"
WORK_DIR=""

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
    if [ -n "$WORK_DIR" ]; then
        rm -rf "$WORK_DIR"
    fi
}

largest_ids() {
    local info n w r
    info=$(osmium fileinfo -e "$1")
    n=$(printf '%s\n' "$info" | sed -n 's/.*Largest node ID: \([0-9]*\).*/\1/p')
    w=$(printf '%s\n' "$info" | sed -n 's/.*Largest way ID: \([0-9]*\).*/\1/p')
    r=$(printf '%s\n' "$info" | sed -n 's/.*Largest relation ID: \([0-9]*\).*/\1/p')
    echo "${n:-0} ${w:-0} ${r:-0}"
}

check_target_block_free() {
    local target="$1" ns="$2" base="$3"
    local limit=$((base + BLOCK_SIZE))
    local t_n t_w t_r id
    read -r t_n t_w t_r <<<"$(largest_ids "$target")"
    for id in "$t_n" "$t_w" "$t_r"; do
        if [ "$id" -ge "$base" ] && [ "$id" -lt "$limit" ]; then
            echo "error: ${target} already holds ids in the '${ns}' block [${base}, ${limit})" >&2
            return 1
        fi
    done
    if [ "$t_n" -ge "$limit" ] || [ "$t_w" -ge "$limit" ] || [ "$t_r" -ge "$limit" ]; then
        local probe
        probe="$(osmium getid --no-progress -f osm "$target" "n$base" "w$base" "r$base" 2>/dev/null || true)"
        if printf '%s' "$probe" | grep -qE "<(node|way|relation) id=\"${base}\""; then
            echo "error: ${target} already holds ids in the '${ns}' block [${base}, ${limit})" >&2
            return 1
        fi
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

case "$MODE" in
    mix)
        ELEVATION_MIX="${1:-}"
        OSMCONVERT_CMD="${2:-}"
        OSMCONVERT_BOUNDING="${3:-}"
        OUTPUT="${4:-}"
        FRAME="${5:-}"
        if [ -z "$ELEVATION_MIX" ] || [ -z "$OSMCONVERT_CMD" ] || [ -z "$OUTPUT" ]; then
            echo "Usage: $0 mix <ELEVATION_MIX> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <OUTPUT> [FRAME]" >&2
            exit 1
        fi

        WORK_DIR="${OUTPUT}.work.$$"
        mkdir -p "$(dirname "$OUTPUT")" "$WORK_DIR"
        rm -f "$OUTPUT"
        trap cleanup EXIT

        echo "renumber ${ELEVATION_MIX} into 'mix' block: ${MIX_BASE}"
        osmium renumber -s "${MIX_BASE},${MIX_BASE},${MIX_BASE}" "$ELEVATION_MIX" -Oo "$WORK_DIR/mix_ren.pbf"
        check_renumbered_within_block "$WORK_DIR/mix_ren.pbf" mix "$MIX_BASE" &
        p_guard=$!

        if [ -n "$FRAME" ]; then
            IFS=, read -r F_LEFT F_BOTTOM F_RIGHT F_TOP <<<"$FRAME"
            osmium tags-filter -O -o "$WORK_DIR/mix_nosea.pbf" "$WORK_DIR/mix_ren.pbf" w/natural=nosea &
            p_nosea=$!
            osmium tags-filter -i -O -o "$WORK_DIR/mix_no_sea.pbf" "$WORK_DIR/mix_ren.pbf" w/natural=sea
            # shellcheck disable=SC2086
            $OSMCONVERT_CMD $OSMCONVERT_BOUNDING "$WORK_DIR/mix_no_sea.pbf" --out-o5m -o="$WORK_DIR/mix_clip.o5m"
            wait "$p_nosea"
            wait "$p_guard"

            MERGE_INPUTS=("$WORK_DIR/mix_clip.o5m")
            MIX_NOSEA_WAYS="$(osmium fileinfo -e -g data.count.ways "$WORK_DIR/mix_nosea.pbf")"
            LAND_GRID=""
            if [ "$MIX_NOSEA_WAYS" -gt 0 ]; then
                MERGE_INPUTS+=("$WORK_DIR/mix_nosea.pbf")
            else
                LAND_GRID="--land-grid 0.1"
            fi

            # shellcheck disable=SC2086
            python3 "${TOOLS_DIR}/frame-landsea.py" "$F_LEFT" "$F_BOTTOM" "$F_RIGHT" "$F_TOP" \
                "$WORK_DIR/frame.osm" $LAND_GRID
            echo "renumber ${WORK_DIR}/frame.osm into 'frame' block: ${FRAME_BASE}"
            osmium renumber -s "${FRAME_BASE},${FRAME_BASE},${FRAME_BASE}" "$WORK_DIR/frame.osm" -Oo "$WORK_DIR/frame_ren.pbf"
            check_renumbered_within_block "$WORK_DIR/frame_ren.pbf" frame "$FRAME_BASE"
            MERGE_INPUTS+=("$WORK_DIR/frame_ren.pbf")

            osmium merge -O -f pbf,add_metadata=false -o "$OUTPUT" "${MERGE_INPUTS[@]}"
        else
            # shellcheck disable=SC2086
            $OSMCONVERT_CMD $OSMCONVERT_BOUNDING "$WORK_DIR/mix_ren.pbf" --out-o5m -o="$WORK_DIR/mix_clip.o5m"
            wait "$p_guard"
            osmium cat -O -f pbf,add_metadata=false -o "$OUTPUT" "$WORK_DIR/mix_clip.o5m"
        fi
        ;;

    osm)
        SED_PBF="${1:-}"
        META="${2:-}"
        OSMCONVERT_CMD="${3:-}"
        OSMCONVERT_BOUNDING="${4:-}"
        OUTPUT="${5:-}"
        FRAME="${6:-}"
        if [ -z "$SED_PBF" ] || [ -z "$META" ] || [ -z "$OSMCONVERT_CMD" ] || [ -z "$OUTPUT" ]; then
            echo "Usage: $0 osm <SED_PBF> <META> <OSMCONVERT_CMD> <OSMCONVERT_BOUNDING> <OUTPUT> [FRAME]" >&2
            exit 1
        fi

        WORK_DIR="${OUTPUT}.work.$$"
        mkdir -p "$(dirname "$OUTPUT")" "$WORK_DIR"
        rm -f "$OUTPUT"
        trap cleanup EXIT

        # SED_PBF (produced from $(REGION_EXTRACT)) is already clipped by
        # OSMCONVERT_BOUNDING with version metadata dropped. Run Guard 1,
        # meta renumber+clip, and (when FRAME is set) land/sea probe in parallel.
        check_target_block_free "$SED_PBF" meta "$META_BASE" &
        p_guard=$!

        (
            echo "renumber ${META} into 'meta' block: ${META_BASE}"
            osmium renumber -s "${META_BASE},${META_BASE},${META_BASE}" "$META" -Oo "$WORK_DIR/meta_ren.pbf"
            check_renumbered_within_block "$WORK_DIR/meta_ren.pbf" meta "$META_BASE"
            # shellcheck disable=SC2086
            $OSMCONVERT_CMD $OSMCONVERT_BOUNDING "$WORK_DIR/meta_ren.pbf" --out-o5m -o="$WORK_DIR/meta_clip.o5m"
            osmium cat -O -f pbf,add_metadata=false -o "$WORK_DIR/meta_clip.osm.pbf" "$WORK_DIR/meta_clip.o5m"
        ) &
        p_meta=$!

        p_sedls=""
        if [ -n "$FRAME" ]; then
            osmium tags-filter -O -o "$WORK_DIR/sed_landsea.pbf" "$SED_PBF" w/natural=sea w/natural=nosea &
            p_sedls=$!
        fi

        wait "$p_guard"
        wait "$p_meta"
        if [ -n "$p_sedls" ]; then
            wait "$p_sedls"
        fi

        SED_LS_WAYS=0
        if [ -n "$FRAME" ]; then
            SED_LS_WAYS="$(osmium fileinfo -e -g data.count.ways "$WORK_DIR/sed_landsea.pbf")"
        fi

        if [ "$SED_LS_WAYS" -eq 0 ] && [[ "$SED_PBF" == *.pbf ]]; then
            # Fast path: zero-recompression PBF blob insertion of meta node(s)
            set +e
            python3 "${TOOLS_DIR}/pbf-insert-nodes.py" "$SED_PBF" "$WORK_DIR/meta_clip.osm.pbf" "$OUTPUT"
            rc=$?
            set -e
            if [ "$rc" -eq 0 ]; then
                exit 0
            elif [ "$rc" -ne 2 ]; then
                exit "$rc"
            fi
            # rc=2: fall back to osmium merge
            osmium merge -O -f pbf,add_metadata=false -o "$OUTPUT" "$SED_PBF" "$WORK_DIR/meta_clip.osm.pbf"
        elif [ "$SED_LS_WAYS" -eq 0 ]; then
            osmium merge -O -f pbf,add_metadata=false -o "$OUTPUT" "$SED_PBF" "$WORK_DIR/meta_clip.osm.pbf"
        else
            # Rare path: SED_PBF itself contains natural=sea or natural=nosea
            EXTRA_INPUTS=()
            osmium tags-filter -O -o "$WORK_DIR/sed_nosea.pbf" "$WORK_DIR/sed_landsea.pbf" w/natural=nosea
            SED_NOSEA_WAYS="$(osmium fileinfo -e -g data.count.ways "$WORK_DIR/sed_nosea.pbf")"
            if [ "$SED_NOSEA_WAYS" -gt 0 ]; then
                EXTRA_INPUTS+=("$WORK_DIR/sed_nosea.pbf")
            fi
            osmium tags-filter -i -O -o "$WORK_DIR/sed_no_sea.pbf" "$SED_PBF" w/natural=sea
            osmium merge -O -f pbf,add_metadata=false -o "$OUTPUT" "$WORK_DIR/sed_no_sea.pbf" "$WORK_DIR/meta_clip.osm.pbf" "${EXTRA_INPUTS[@]}"
        fi
        ;;

    *)
        echo "Usage: $0 <mix|osm> ..." >&2
        exit 1
        ;;
esac
