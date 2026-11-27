#!/bin/sh
set -ex
infile="$1"
outfile="$2"

if [ "$infile" = "" -o "$outfile" = "" ]; then
    echo "Usage: $0 <infile> <outfile>"
    exit 1
fi

rm -f "$outfile"

# NB: name:zh is intentionally KEPT (do not drop it). mapsforge renders Chinese
# via the name:zh tag (preferred-languages=zh,en) and complete_name.py no longer
# overwrites `name` with the Chinese value, so dropping name:zh would leave the
# mapsforge map with only the native `name` (e.g. French/German in the Alps).
# disused:* tags and metadata lookups (hknetworks, national_park,
# strict_protected, summit_board) are handled directly inside process_osm.py.
script_dir="$(dirname "$0")"
python3 "$script_dir/process_osm.py" "$infile" "$outfile"
