#!/bin/sh
set -ex
infile="$1"
outfile="$2"

if [ "$infile" = "" -o "$outfile" = "" ]; then
    echo "Usage: $0 <infile> <outfile>"
    exit 1
fi

rm -f "$outfile"

osmfilter \
    --drop-nodes \
    --drop-ways \
    --drop-version \
    --ignore-dependencies \
    --keep-relations='type=route and route=hiking and name= and network=' \
    "$infile" -o=hknetworks.osm

temp_pbf=temp.osm.pbf
osmfilter \
    --drop-version \
    --ignore-dependencies \
    --drop-tags='name:zh= ref:zh=' \
    "$infile" --out-o5m | osmconvert - -o="$temp_pbf"

script_dir="$(dirname $0)"
python3 "$script_dir/process_osm.py" "$temp_pbf" "$outfile"
