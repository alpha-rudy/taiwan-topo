#!/bin/bash
#
# osmium-append.sh - Append an OSM file into a target, renumbering the added
# objects into a reserved, permanently OSM-free ID block.
#
# Usage: osmium-append.sh [-o <output>] <target> <add> [namespace]
#        osmium-append.sh [-o <output>] <target> <add1> <ns1> [<add2> <ns2> ...]
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
#     6    160e9   frame       mapsforge sea frame (tools/mapsforge-input-build.sh)
#    7-8   170e9   (reserved for future sources)
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
    echo "Usage: $0 [-o <output>] <target> <add> [namespace]" >&2
    echo "       $0 [-o <output>] <target> <add1> <ns1> [<add2> <ns2> ...]" >&2
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
        frame)     echo 6 ;;
        fallback)  echo 9 ;;
        *)         echo "" ;;
    esac
}

output=""
if [ "${1:-}" = "-o" ]; then
    [ "$#" -ge 4 ] || usage
    output="$2"
    shift 2
fi

if [ "$#" -lt 2 ]; then
    usage
fi

target="$1"
output="${output:-$target}"
shift

adds=()
namespaces=()
if [ "$#" -eq 1 ]; then
    adds+=("$1")
    namespaces+=("fallback")
elif [ $(($# % 2)) -eq 0 ]; then
    while [ "$#" -gt 0 ]; do
        adds+=("$1")
        namespaces+=("$2")
        shift 2
    done
else
    usage
fi

[ -f "$target" ] || { echo "error: target file not found: $target" >&2; exit 1; }

bases=()
limits=()
seen_ns=" "
for i in "${!adds[@]}"; do
    add="${adds[$i]}"
    ns="${namespaces[$i]}"
    [ -f "$add" ] || { echo "error: add file not found: $add" >&2; exit 1; }
    block="$(block_for "$ns")"
    if [ -z "$block" ]; then
        echo "error: unknown ID namespace '$ns' (see the ID LAYOUT table in $0)" >&2
        exit 1
    fi
    if [[ "$seen_ns" == *" $ns "* ]]; then
        echo "error: duplicate ID namespace '$ns' in a single append call" >&2
        exit 1
    fi
    seen_ns="${seen_ns}${ns} "
    base=$((SYNTHETIC_BASE + block * BLOCK_SIZE))
    bases+=("$base")
    limits+=($((base + BLOCK_SIZE)))
done

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

# Guard 1: every requested block must still be free in the target. Scan the
# target once for largest IDs and (only if needed) once with osmium getid.
read -r t_n t_w t_r <<<"$(largest_ids "$target")"
probe_ids=()
probe_indices=()
for i in "${!adds[@]}"; do
    b="${bases[$i]}"
    l="${limits[$i]}"
    for id in "$t_n" "$t_w" "$t_r"; do
        if [ "$id" -ge "$b" ] && [ "$id" -lt "$l" ]; then
            echo "error: ${target} already holds ids in the '${namespaces[$i]}' block [${b}, ${l}); refusing to append ${adds[$i]}" >&2
            exit 1
        fi
    done
    # Every largest id sits outside the block - but if one sits ABOVE it, the block
    # itself may still be populated (a target that inherited several blocks, e.g.
    # the mapsforge input already carries adshelter+gianttree before 'mix' is
    # appended). osmium renumber always starts a block at exactly <base>, so
    # probing that single id settles the question exactly.
    if [ "$t_n" -ge "$l" ] || [ "$t_w" -ge "$l" ] || [ "$t_r" -ge "$l" ]; then
        probe_ids+=("n$b" "w$b" "r$b")
        probe_indices+=("$i")
    fi
done

if [ "${#probe_ids[@]}" -gt 0 ]; then
    # getid exits 1 when ANY requested id is missing, which is the normal case
    # here (most sources contribute only nodes), so ignore its status and look
    # at what it actually printed.
    probe="$(osmium getid --no-progress -f osm "$target" "${probe_ids[@]}" 2>/dev/null || true)"
    for i in "${probe_indices[@]}"; do
        b="${bases[$i]}"
        l="${limits[$i]}"
        if printf '%s' "$probe" | grep -qE "<(node|way|relation) id=\"${b}\""; then
            echo "error: ${target} already holds ids in the '${namespaces[$i]}' block [${b}, ${l}); refusing to append ${adds[$i]}" >&2
            exit 1
        fi
    done
fi

ext="${output##*.}"
tmp_dir="$(dirname "$output")"
mgr_file="${tmp_dir}/.append_$$_mgr.pbf"
ren_files=()

cleanup() {
    rm -f "$mgr_file" "${ren_files[@]}"
}
trap cleanup EXIT

for i in "${!adds[@]}"; do
    add="${adds[$i]}"
    ns="${namespaces[$i]}"
    base="${bases[$i]}"
    limit="${limits[$i]}"
    ren_file="${tmp_dir}/.append_$$_ren_${i}.pbf"
    ren_files+=("$ren_file")

    echo "renumber ${add} into '${ns}' block: ${base}"
    osmium renumber \
        -s "${base},${base},${base}" \
        "$add" \
        -Oo "$ren_file"

    # Guard 2: the renumbered payload must stay inside its block.
    read -r a_node a_way a_rel <<<"$(largest_ids "$ren_file")"
    for id in "$a_node" "$a_way" "$a_rel"; do
        if [ "$id" -ge "$limit" ]; then
            echo "error: ${add} overflows the '${ns}' block [${base}, ${limit}); largest id ${id}" >&2
            exit 1
        fi
    done
done

echo "merge: ${target} ${adds[*]}"
osmium merge \
    "$target" \
    "${ren_files[@]}" \
    -Oo "$mgr_file"

if [ "$ext" == "pbf" ]; then
    mv "$mgr_file" "$output"
else
    "${OSMCONVERT_CMD:-osmconvert}" "$mgr_file" -o="$output"
fi
