#!/bin/bash
#
# nsis-build.sh - Generate NSIS Windows installer for Garmin maps
#
# Usage: nsis-build.sh <MAP_DIR> <MAPID> <NAME_WORD> <VERSION> <MAPID_LO_HEX> <MAPID_HI_HEX> <ROOT_DIR> <OUTPUT_EXE>
#
# This script generates copy/delete tile lists, processes the NSIS template,
# and runs makensis to create a Windows installer executable.
#

set -e

MAP_DIR="$1"
MAPID="$2"
NAME_WORD="$3"
VERSION="$4"
MAPID_LO_HEX="$5"
MAPID_HI_HEX="$6"
ROOT_DIR="$7"
OUTPUT_EXE="$8"

if [ -z "$MAP_DIR" ] || [ -z "$MAPID" ] || [ -z "$NAME_WORD" ] || [ -z "$VERSION" ] || [ -z "$ROOT_DIR" ] || [ -z "$OUTPUT_EXE" ]; then
    echo "Usage: $0 <MAP_DIR> <MAPID> <NAME_WORD> <VERSION> <MAPID_LO_HEX> <MAPID_HI_HEX> <ROOT_DIR> <OUTPUT_EXE>"
    exit 1
fi

# Platform-specific sed command
if [ "$(uname)" = 'Darwin' ]; then
    SED_CMD='gsed'
else
    SED_CMD='sed'
fi

cd "$MAP_DIR"

# Generate copy_tiles.txt - NSIS commands to copy tile files
rm -f copy_tiles.txt
for i in ${MAPID}*.img; do
    [ -f "$i" ] || continue
    echo "  File \"${i}\"  "
done > copy_tiles.txt

# Generate delete_tiles.txt - NSIS commands to delete tile files on uninstall
rm -f delete_tiles.txt
for i in ${MAPID}*.img; do
    [ -f "$i" ] || continue
    echo "  Delete \"\$INSTDIR\\${i}\"  "
done > delete_tiles.txt

# Process NSIS template with variable substitutions
cat "${ROOT_DIR}/mkgmaps/makensis.cfg" | $SED_CMD \
    -e "s|__root_dir__|${ROOT_DIR}|g" \
    -e "s|__name_word__|${NAME_WORD}|g" \
    -e "s|__version__|${VERSION}|g" \
    -e "s|__mapid_lo_hex__|${MAPID_LO_HEX}|g" \
    -e "s|__mapid_hi_hex__|${MAPID_HI_HEX}|g" \
    -e "s|__mapid__|${MAPID}|g" > "${NAME_WORD}.nsi"

# Insert tile copy/delete commands into NSIS script
$SED_CMD "/__copy_tiles__/ r copy_tiles.txt" -i "${NAME_WORD}.nsi"
$SED_CMD "/__delete_tiles__/ r delete_tiles.txt" -i "${NAME_WORD}.nsi"

# Create ZIP archive of install files
# (Skipped in favor of direct NSIS compression)
# rm -f "${NAME_WORD}_InstallFiles.zip"
# find . -maxdepth 1 \( -name "${MAPID}*.img" -o -name "${MAPID}.TYP" -o -name "${NAME_WORD}.img" -o -name "${NAME_WORD}_mdr.img" -o -name "${NAME_WORD}.tdb" -o -name "${NAME_WORD}.mdx" \) -type f -print0 | xargs -0 zip -j -6 "${NAME_WORD}_InstallFiles.zip"


# Generate readme from template
cat "${ROOT_DIR}/docs/nsis-readme.txt" | $SED_CMD \
    -e "s|__version__|${VERSION}|g" > readme.txt

# Copy installer graphics
cp "${ROOT_DIR}/nsis/Install.bmp" "${ROOT_DIR}/nsis/Deinstall.bmp" .

# Run NSIS compiler
makensis "${NAME_WORD}.nsi"

# Cleanup temporary ZIP
# rm -f "${NAME_WORD}_InstallFiles.zip"

# Move output to final location
mv "Install_${NAME_WORD}.exe" "$OUTPUT_EXE"

echo "NSIS installer created: $OUTPUT_EXE"
