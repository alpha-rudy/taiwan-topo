#!/bin/bash
#
# osmium-append.sh - Append an OSM file into a target, renumbering IDs
# past the target's largest node/way/relation IDs to avoid collisions.
#
# Usage: osmium-append.sh <target> <add>
#
# Env:
#   OSMCONVERT_CMD - path to osmconvert binary (falls back to `osmconvert`
#                    on PATH) used to convert the merged result back to
#                    the target's format when target is not already .pbf
#
set -euo pipefail

usage() {
    echo "Usage: $0 <target> <add>" >&2
    exit 1
}

if [ "$#" -ne 2 ]; then
    usage
fi

target="$1"
add="$2"

[ -f "$target" ] || { echo "error: target file not found: $target" >&2; exit 1; }
[ -f "$add" ] || { echo "error: add file not found: $add" >&2; exit 1; }

fileinfo=$(osmium fileinfo -e "$target")

lnid=$(printf '%s\n' "$fileinfo" | sed -n 's/.*Largest node ID: \([0-9]*\).*/\1/p')
lwid=$(printf '%s\n' "$fileinfo" | sed -n 's/.*Largest way ID: \([0-9]*\).*/\1/p')
lrid=$(printf '%s\n' "$fileinfo" | sed -n 's/.*Largest relation ID: \([0-9]*\).*/\1/p')

lnid=${lnid:-0}
lwid=${lwid:-0}
lrid=${lrid:-0}

lnid=$((lnid + 1))
lwid=$((lwid + 1))
lrid=$((lrid + 1))

ext="${target##*.}"
tmp_dir="$(dirname "$target")"
ren_file="${tmp_dir}/.append_$$_ren.pbf"
mgr_file="${tmp_dir}/.append_$$_mgr.pbf"

cleanup() {
    rm -f "$ren_file" "$mgr_file"
}
trap cleanup EXIT

echo "renumber ${add}: ${lnid},${lwid},${lrid}"
osmium renumber \
    -s "${lnid},${lwid},${lrid}" \
    "$add" \
    -Oo "$ren_file"

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
