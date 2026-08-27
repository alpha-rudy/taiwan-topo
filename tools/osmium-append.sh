#!/bin/bash
#
# osmium-append.sh - Append an OSM file into a target, renumbering the added
# objects into a reserved, permanently OSM-free ID block.
#
# Usage: osmium-append.sh <target> <add> [namespace]
#
# Env:
#   OSMCONVERT_CMD - path to osmconvert binary (falls back to `osmconvert`
#                    on PATH) used to convert the merged result back to
#                    the target's format when target is not already .pbf
#
#
# ID LAYOUT
# =========
# This script used to renumber the added file to "largest id present in the
# target + a small gap". That is unsafe: OSM extracts routinely contain orphan
# ways whose nodes were clipped away, and those dangling refs point ABOVE the
# largest id actually present. Appended data landed straight on top of them and
# resurrected foreign objects with local geometry (e.g. a French reservoir drawn
# across Taiwan from air-defense-shelter and contour nodes).
#
# Instead every non-OSM source gets a fixed block that real OSM ids cannot reach.
#
#   OSM space      [0, 100e9)         never assigned here
#   synthetic base  100_000_000_000
#   block size       10_000_000_000
#
#   block  base    namespace   source
#   -----  ------  ----------  ---------------------------------------------
#     0    100e9   contour     $(ELEVATION) contour lines
#     1    110e9   mix         $(ELEVATION_MIX) marker file / $(LANDSEA_FILE)
#     2    120e9   adshelter   precompiled/NPA_Taiwan_ADShelter-ren.pbf
#     3    130e9   gianttree   precompiled/TFRI_Taiwan_GiantTree-ren.osm
#     4    140e9   meta        meta/meta.osm version stamp
#     5    150e9   gpx         GPX overlay / waypoint appends
#    6-8   160e9   (reserved for future sources)
#     9    190e9   fallback    used when no namespace is given
#
# The same layout applies to node, way and relation ids; way and relation counts
# are orders of magnitude below the block size, so no block can overflow into the
# next one.
#
# Headroom: OSM node ids are ~14.2e9 (Aug 2026) growing ~1.4e9/year, so the 100e9
# floor is ~60 years out. 100e9 < 2^37 and the top of the space (200e9) < 2^38, so
# tools that pack ids into 40 or 48 bits keep working - verified against splitter,
# mkgmap and the osmosis mapfile-writer on the same tile with and without the
# renumbering: identical object counts, no warnings, byte-identical .img and a
# 2-byte delta on the .map. OSM ids reach none of the shipped formats (neither
# Garmin .img nor mapsforge .map store them), so the wide ids cost nothing there.
#
set -euo pipefail

SYNTHETIC_BASE=100000000000
BLOCK_SIZE=10000000000

usage() {
    echo "Usage: $0 <target> <add> [namespace]" >&2
    exit 1
}

# namespace -> block index
block_for() {
    case "$1" in
        contour)   echo 0 ;;
        mix)       echo 1 ;;
        adshelter) echo 2 ;;
        gianttree) echo 3 ;;
        meta)      echo 4 ;;
        gpx)       echo 5 ;;
        fallback)  echo 9 ;;
        *)         echo "" ;;
    esac
}

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    usage
fi

target="$1"
add="$2"
namespace="${3:-fallback}"

[ -f "$target" ] || { echo "error: target file not found: $target" >&2; exit 1; }
[ -f "$add" ] || { echo "error: add file not found: $add" >&2; exit 1; }

block="$(block_for "$namespace")"
if [ -z "$block" ]; then
    echo "error: unknown ID namespace '$namespace' (see the ID LAYOUT table in $0)" >&2
    exit 1
fi

base=$((SYNTHETIC_BASE + block * BLOCK_SIZE))
limit=$((base + BLOCK_SIZE))

# Largest id of each type currently in a file, as "node way relation".
largest_ids() {
    local info
    info=$(osmium fileinfo -e "$1")
    local n w r
    n=$(printf '%s\n' "$info" | sed -n 's/.*Largest node ID: \([0-9]*\).*/\1/p')
    w=$(printf '%s\n' "$info" | sed -n 's/.*Largest way ID: \([0-9]*\).*/\1/p')
    r=$(printf '%s\n' "$info" | sed -n 's/.*Largest relation ID: \([0-9]*\).*/\1/p')
    echo "${n:-0} ${w:-0} ${r:-0}"
}

# Is any id of <file> inside the block [<base>, <limit>)?
block_occupied() {
    local f="$1" b="$2" l="$3"
    local n w r id
    read -r n w r <<<"$(largest_ids "$f")"

    for id in "$n" "$w" "$r"; do
        if [ "$id" -ge "$b" ] && [ "$id" -lt "$l" ]; then
            return 0
        fi
    done

    # Every largest id sits outside the block - but if one sits ABOVE it, the block
    # itself may still be populated (a target that inherited several blocks, e.g.
    # the mapsforge input already carries adshelter+gianttree before 'mix' is
    # appended). osmium renumber always starts a block at exactly <base>, so
    # probing that single id settles the question exactly.
    if [ "$n" -ge "$l" ] || [ "$w" -ge "$l" ] || [ "$r" -ge "$l" ]; then
        # getid exits 1 when ANY requested id is missing, which is the normal case
        # here (most sources contribute only nodes), so ignore its status and look
        # at what it actually printed - at most three objects.
        local probe
        probe="$(osmium getid --no-progress -f osm "$f" "n$b" "w$b" "r$b" 2>/dev/null || true)"
        if printf '%s' "$probe" | grep -qE '<(node|way|relation) id='; then
            return 0
        fi
    fi

    return 1
}

# Guard 1: the block must still be free in the target. A hit means this namespace
# was already appended to this target, and renumbering again would overwrite it.
if block_occupied "$target" "$base" "$limit"; then
    echo "error: ${target} already holds ids in the '${namespace}' block [${base}, ${limit}); refusing to append ${add}" >&2
    exit 1
fi

ext="${target##*.}"
tmp_dir="$(dirname "$target")"
ren_file="${tmp_dir}/.append_$$_ren.pbf"
mgr_file="${tmp_dir}/.append_$$_mgr.pbf"

cleanup() {
    rm -f "$ren_file" "$mgr_file"
}
trap cleanup EXIT

echo "renumber ${add} into '${namespace}' block: ${base}"
osmium renumber \
    -s "${base},${base},${base}" \
    "$add" \
    -Oo "$ren_file"

# Guard 2: the renumbered payload must stay inside its block.
read -r a_node a_way a_rel <<<"$(largest_ids "$ren_file")"
for id in "$a_node" "$a_way" "$a_rel"; do
    if [ "$id" -ge "$limit" ]; then
        echo "error: ${add} overflows the '${namespace}' block [${base}, ${limit}); largest id ${id}" >&2
        exit 1
    fi
done

echo "merge: ${target} ${add}"
osmium merge \
    "$target" \
    "$ren_file" \
    -Oo "$mgr_file"

if [ "$ext" == "pbf" ]; then
    mv "$mgr_file" "$target"
else
    "${OSMCONVERT_CMD:-osmconvert}" "$mgr_file" -o="$target"
fi
