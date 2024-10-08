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

osmfilter \
    --drop-nodes \
    --drop-ways \
    --drop-version \
    --ignore-dependencies \
    --keep-relations='type=boundary and boundary=national_park and name=' \
    "$infile" -o=national_park.osm

osmfilter \
    --drop-nodes \
    --drop-ways \
    --drop-version \
    --ignore-dependencies \
    --keep-relations='type=boundary and boundary=protected_area and protect_class=1 and name=' \
    "$infile" -o=strict_protected.osm

temp_pbf=temp.osm.pbf
osmfilter \
    --drop-version \
    --ignore-dependencies \
    --drop-tags='name:zh= ref:zh=' \
    --drop-tags='disused:*=' \
    "$infile" --out-o5m | ${OSMCONVERT_CMD} - -o="$temp_pbf"

script_dir="$(dirname $0)"
python3 "$script_dir/process_osm.py" "$temp_pbf" "$outfile"
