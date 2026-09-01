#!/bin/bash

# Automatic generation for sea and land OSM files
# Creates sea.osm and nosea (land) OSM files from bounding box coordinates
#
# Based on map-creator.sh by devemux86

# Configuration

[ $OSMOSIS_HOME ] || OSMOSIS_HOME="$PWD/tools/osmosis"
[ $DATA_PATH ] || DATA_PATH="$PWD/downloads/land-polygons"
[ $OUTPUT_PATH ] || OUTPUT_PATH="$PWD/downloads/land-polygons"

[ $DAYS ] || DAYS="30"

# =========== DO NOT CHANGE AFTER THIS LINE. ===========================
# Below here is regular code, part of the file. This is not designed to
# be modified by users.
# ======================================================================

print_usage() {
  echo "Usage: $0 -l LEFT -r RIGHT -b BOTTOM -t TOP [-n NAME] [-o OUTPUT_PATH] [-g GRID_SIZE]"
  echo ""
  echo "Required arguments:"
  echo "  -l LEFT     Left longitude (min longitude)"
  echo "  -r RIGHT    Right longitude (max longitude)"
  echo "  -b BOTTOM   Bottom latitude (min latitude)"
  echo "  -t TOP      Top latitude (max latitude)"
  echo ""
  echo "Optional arguments:"
  echo "  -n NAME     Output file name prefix (default: sealand)"
  echo "  -o OUTPUT   Output directory path (default: $OUTPUT_PATH)"
  echo "  -g GRID     Grid size in degrees for inland fine-grid nosea tiles (e.g. 0.1)"
  echo "              When set, skips land polygon shapefile and covers entire bbox"
  echo "              with small rectangular nosea tiles of the given size."
  echo ""
  echo "Example: $0 -l -74.3 -r -73.7 -b 40.5 -t 40.9 -n newyork"
  echo "Example: $0 -l 41.89 -r 43.81 -b 43.09 -t 43.76 -n elbrus -g 0.1"
  exit 1
}

# Parse command line options

LEFT=""
RIGHT=""
BOTTOM=""
TOP=""
NAME="sealand"
GRID=""

while getopts "l:r:b:t:n:o:g:h" opt; do
  case $opt in
    l) LEFT="$OPTARG" ;;
    r) RIGHT="$OPTARG" ;;
    b) BOTTOM="$OPTARG" ;;
    t) TOP="$OPTARG" ;;
    n) NAME="$OPTARG" ;;
    o) OUTPUT_PATH="$OPTARG" ;;
    g) GRID="$OPTARG" ;;
    h) print_usage ;;
    *) print_usage ;;
  esac
done

# Validate required arguments

if [ -z "$LEFT" ] || [ -z "$RIGHT" ] || [ -z "$BOTTOM" ] || [ -z "$TOP" ]; then
  echo "Error: All bounding box coordinates (LEFT, RIGHT, BOTTOM, TOP) are required."
  echo ""
  print_usage
fi

# Validate coordinate values

validate_coordinate() {
  local value="$1"
  local name="$2"
  if ! [[ "$value" =~ ^-?[0-9]+\.?[0-9]*$ ]]; then
    echo "Error: $name must be a valid number."
    exit 1
  fi
}

validate_coordinate "$LEFT" "LEFT"
validate_coordinate "$RIGHT" "RIGHT"
validate_coordinate "$BOTTOM" "BOTTOM"
validate_coordinate "$TOP" "TOP"

cd "$(dirname "$0")"

WORK_PATH="$DATA_PATH/sealand_tmp_$$"

echo "Creating sea and land OSM files..."
echo "Bounding box: LEFT=$LEFT, RIGHT=$RIGHT, BOTTOM=$BOTTOM, TOP=$TOP"

# Pre-process

rm -rf "$WORK_PATH"
mkdir -p "$WORK_PATH"
mkdir -p "$OUTPUT_PATH"

# ========== Land (nosea) ==========

if [ -n "$GRID" ]; then
  echo "Generating fine-grid nosea tiles (grid=${GRID}°)..."
  python3 - "$LEFT" "$RIGHT" "$BOTTOM" "$TOP" "$GRID" "$WORK_PATH/land000.osm" << 'PYEOF'
import sys
left, right, bottom, top = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
grid = float(sys.argv[5])
output = sys.argv[6]

node_id = 1000000000
way_id  = 2000000000
nodes, ways = [], []

lon = left
while lon < right - 1e-9:
    lon_end = min(lon + grid, right)
    lat = bottom
    while lat < top - 1e-9:
        lat_end = min(lat + grid, top)
        n = [node_id + i for i in range(4)]
        node_id += 4
        coords = [(lat, lon), (lat, lon_end), (lat_end, lon_end), (lat_end, lon)]
        for i, (la, lo) in enumerate(coords):
            nodes.append(f'  <node id="{n[i]}" lat="{la}" lon="{lo}" version="1" timestamp="1970-01-01T00:00:00Z"/>')
        ways.append(f'  <way id="{way_id}" version="1" timestamp="1970-01-01T00:00:00Z">')
        for ref in n + [n[0]]:
            ways.append(f'    <nd ref="{ref}"/>')
        ways.append('    <tag k="area" v="yes"/><tag k="layer" v="-5"/><tag k="natural" v="nosea"/>')
        ways.append('  </way>')
        way_id += 1
        lat = round(lat + grid, 10)
    lon = round(lon + grid, 10)

with open(output, 'w') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6">\n')
    for line in nodes + ways:
        f.write(line + '\n')
    f.write('</osm>\n')
print(f"Generated {way_id - 2000000000} nosea tiles")
PYEOF

else
  echo "Processing land polygons..."

  # Land (nosea) - clip land polygons to bounding box and convert to OSM

  ogr2ogr -overwrite -progress -skipfailures -clipsrc $LEFT $BOTTOM $RIGHT $TOP "$WORK_PATH/land.shp" "$DATA_PATH/land-polygons-split-4326/land_polygons.shp"
  python3 shape2osm.py -l "$WORK_PATH/land" "$WORK_PATH/land.shp"

  # Merge all land OSM files into one nosea file
  if ls $WORK_PATH/land*.osm 1> /dev/null 2>&1; then
    LAND_COUNT=$(ls -1 $WORK_PATH/land*.osm 2>/dev/null | wc -l)
    if [ "$LAND_COUNT" -eq 1 ]; then
      cp $WORK_PATH/land*.osm "$OUTPUT_PATH/$NAME-nosea.osm"
    else
      echo '<?xml version="1.0" encoding="UTF-8"?>' > "$OUTPUT_PATH/$NAME-nosea.osm"
      echo '<osm version="0.6">' >> "$OUTPUT_PATH/$NAME-nosea.osm"
      for f in $WORK_PATH/land*.osm; do
        grep -v '<?xml' "$f" | grep -v '<osm' | grep -v '</osm>' >> "$OUTPUT_PATH/$NAME-nosea.osm"
      done
      echo '</osm>' >> "$OUTPUT_PATH/$NAME-nosea.osm"
    fi
    echo "Created: $OUTPUT_PATH/$NAME-nosea.osm"
  else
    echo "Warning: No land polygons found in the specified bounding box."
    echo '<?xml version="1.0" encoding="UTF-8"?>' > "$OUTPUT_PATH/$NAME-nosea.osm"
    echo '<osm version="0.6">' >> "$OUTPUT_PATH/$NAME-nosea.osm"
    echo '</osm>' >> "$OUTPUT_PATH/$NAME-nosea.osm"
    echo "Created empty: $OUTPUT_PATH/$NAME-nosea.osm"
  fi
fi

# ========== Sea ==========

echo "Processing sea..."

# Sea - create sea OSM from template

cp sea.osm "$WORK_PATH/sea.osm"
sed -i "s/\$BOTTOM/$BOTTOM/g" "$WORK_PATH/sea.osm"
sed -i "s/\$LEFT/$LEFT/g" "$WORK_PATH/sea.osm"
sed -i "s/\$TOP/$TOP/g" "$WORK_PATH/sea.osm"
sed -i "s/\$RIGHT/$RIGHT/g" "$WORK_PATH/sea.osm"

cp "$WORK_PATH/sea.osm" "$OUTPUT_PATH/$NAME-sea.osm"
echo "Created: $OUTPUT_PATH/$NAME-sea.osm"

# ========== Merge Sea and Land ==========

echo "Merging sea and land with osmosis..."

CMD="$OSMOSIS_HOME/bin/osmosis --rx file=$WORK_PATH/sea.osm --s"
for f in $WORK_PATH/land*.osm; do
  CMD="$CMD --rx file=$f --s --m"
done
CMD="$CMD --wx file=$OUTPUT_PATH/$NAME-sealand.osm"
echo $CMD
eval "$CMD" || exit 1

echo "Created: $OUTPUT_PATH/$NAME-sealand.osm"

# ========== Renumber and Convert to PBF ==========

echo "Renumbering sealand and converting to PBF..."

osmium renumber -s 1,1,1 "$OUTPUT_PATH/$NAME-sealand.osm" -o "$OUTPUT_PATH/$NAME-sealand.pbf" --overwrite || exit 1

echo "Created: $OUTPUT_PATH/$NAME-sealand.pbf"

# ========== Post-process ==========

echo "Cleaning up..."
rm -rf "$WORK_PATH"
rm -f "$OUTPUT_PATH/$NAME-sea.osm"
rm -f "$OUTPUT_PATH/$NAME-nosea.osm"
rm -f "$OUTPUT_PATH/$NAME-sealand.osm"

echo ""
echo "Done! Output file:"
echo "  Sealand: $OUTPUT_PATH/$NAME-sealand.pbf"
