#!/bin/sh
set -ex
infile="$1"
outfile="$2"

if [ "$infile" = "" -o "$outfile" = "" ]; then
    echo "Usage: $0 <infile> <outfile>"
    exit 1
fi

rm -f "$outfile"

# Generate unique prefix based on input filename to avoid conflicts between regions
prefix=$(basename "$infile" .o5m)

osmfilter \
    --drop-nodes \
    --drop-ways \
    --drop-version \
    --ignore-dependencies \
    --keep-relations='type=route and route=hiking and name= and network=' \
    "$infile" -o="${prefix}_hknetworks.osm"

osmfilter \
    --drop-nodes \
    --drop-ways \
    --drop-version \
    --ignore-dependencies \
    --keep-relations='type=boundary and boundary=national_park and name=' \
    "$infile" -o="${prefix}_national_park.osm"

osmfilter \
    --drop-nodes \
    --drop-ways \
    --drop-version \
    --ignore-dependencies \
    --keep-relations='type=boundary and boundary=protected_area and protect_class=1 and name=' \
    "$infile" -o="${prefix}_strict_protected.osm"

filtered_o5m="${prefix}_filtered.o5m"
filtered_pbf="${prefix}_filtered.osm.pbf"
osmfilter \
    --drop-version \
    --ignore-dependencies \
    --drop-tags='name:zh= ref:zh=' \
    --drop-tags='disused:*=' \
    "$infile" -o="$filtered_o5m"
${OSMCONVERT_CMD} "$filtered_o5m" -o="$filtered_pbf"

script_dir="$(dirname $0)"
python3 "$script_dir/process_osm.py" "$filtered_pbf" "$outfile" "$prefix"

# Cleanup intermediate files
rm -f "${prefix}_hknetworks.osm" "${prefix}_national_park.osm" "${prefix}_strict_protected.osm" "$filtered_o5m" "$filtered_pbf"
