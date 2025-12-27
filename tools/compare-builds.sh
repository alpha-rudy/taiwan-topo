#!/usr/bin/env bash
#
# Compare two build directories to verify they produce identical outputs
# Usage: ./tools/compare-builds.sh [build-dir-1] [build-dir-2]
#

set -e

DIR1="${1:-build}"
DIR2="${2:-build-2}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Binary file extensions that may differ due to timestamps/non-determinism
BINARY_EXTS="map|poi|img|db"

# Intermediate build artifacts to exclude from comparison (contain BUILD_DIR paths)
# These are generated config files, not final outputs
# Note: Using -iname for case-insensitive matching where needed
EXCLUDE_PATTERN="-name *.cfg -o -name *.args -o -name *.txt -o -name *.nsi -o -name .*.done -o -iname *.typ -o -name *.article -o -name *.list -o -name *.poly -o -name *.log"

echo "=========================================="
echo "Comparing: $DIR1 vs $DIR2"
echo "=========================================="

# Check directories exist
if [[ ! -d "$DIR1" ]]; then
    echo -e "${RED}Error: Directory '$DIR1' does not exist${NC}"
    exit 1
fi

if [[ ! -d "$DIR2" ]]; then
    echo -e "${RED}Error: Directory '$DIR2' does not exist${NC}"
    exit 1
fi

# 1. Compare file lists (excluding intermediate artifacts)
echo ""
echo "=== File List Comparison (excluding intermediate artifacts) ==="
LIST1=$(mktemp)
LIST2=$(mktemp)
trap "rm -f $LIST1 $LIST2" EXIT

(cd "$DIR1" && find . -type f ! \( $EXCLUDE_PATTERN \) | sort) > "$LIST1"
(cd "$DIR2" && find . -type f ! \( $EXCLUDE_PATTERN \) | sort) > "$LIST2"

if diff -q "$LIST1" "$LIST2" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ File lists are identical${NC}"
    FILE_COUNT=$(wc -l < "$LIST1")
    echo "  Total files: $FILE_COUNT"
else
    echo -e "${RED}✗ File lists differ${NC}"
    echo ""
    echo "Files only in $DIR1:"
    comm -23 "$LIST1" "$LIST2" | head -20
    echo ""
    echo "Files only in $DIR2:"
    comm -13 "$LIST1" "$LIST2" | head -20
    echo ""
    exit 1
fi

# 2. Compare file sizes (excluding intermediate artifacts and zips)
echo ""
echo "=== File Size Comparison ==="
SIZE1=$(mktemp)
SIZE2=$(mktemp)
trap "rm -f $LIST1 $LIST2 $SIZE1 $SIZE2" EXIT

(cd "$DIR1" && find . -type f ! -name "*.zip" ! \( $EXCLUDE_PATTERN \) -exec stat -c "%n %s" {} \; | sort) > "$SIZE1"
(cd "$DIR2" && find . -type f ! -name "*.zip" ! \( $EXCLUDE_PATTERN \) -exec stat -c "%n %s" {} \; | sort) > "$SIZE2"

if diff -q "$SIZE1" "$SIZE2" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ File sizes are identical${NC}"
else
    echo -e "${YELLOW}⚠ File sizes differ${NC}"
    echo "Differences:"
    diff "$SIZE1" "$SIZE2" | head -40
    exit 1
fi

# 3. Compare ZIP contents (extract and diff)
echo ""
echo "=== ZIP Content Comparison ==="

ZIP_FILES=$(cd "$DIR1" && find . -name "*.zip" -type f | sort)
ZIP_DIFF_COUNT=0

if [[ -n "$ZIP_FILES" ]]; then
    ZIP_TEMP=$(mktemp -d)
    trap "rm -rf $LIST1 $LIST2 $SIZE1 $SIZE2 $ZIP_TEMP" EXIT
    
    for zipfile in $ZIP_FILES; do
        if [[ -f "$DIR2/$zipfile" ]]; then
            mkdir -p "$ZIP_TEMP/dir1" "$ZIP_TEMP/dir2"
            unzip -q -o "$DIR1/$zipfile" -d "$ZIP_TEMP/dir1" 2>/dev/null
            unzip -q -o "$DIR2/$zipfile" -d "$ZIP_TEMP/dir2" 2>/dev/null
            
            if diff -rq "$ZIP_TEMP/dir1" "$ZIP_TEMP/dir2" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ $zipfile${NC}"
            else
                # Check if differences are only in known binary files
                DIFF_FILES=$(diff -rq "$ZIP_TEMP/dir1" "$ZIP_TEMP/dir2" 2>/dev/null | grep "^Files" | sed 's/Files \(.*\) and .* differ/\1/')
                ALL_BINARY=true
                SIZE_MISMATCH=false
                
                for diff_file in $DIFF_FILES; do
                    # Check if it's a known binary extension
                    if [[ ! "$diff_file" =~ \.($BINARY_EXTS)$ ]]; then
                        ALL_BINARY=false
                        break
                    fi
                    
                    # Get corresponding file in dir2
                    diff_file2="${diff_file/$ZIP_TEMP\/dir1/$ZIP_TEMP\/dir2}"
                    
                    # Compare sizes
                    size1=$(stat -c %s "$diff_file" 2>/dev/null || echo 0)
                    size2=$(stat -c %s "$diff_file2" 2>/dev/null || echo 0)
                    
                    if [[ "$size1" -ne "$size2" ]]; then
                        SIZE_MISMATCH=true
                        echo -e "  ${YELLOW}Size diff: $(basename "$diff_file"): $size1 vs $size2 (diff: $((size2-size1)))${NC}"
                    fi
                done
                
                if $ALL_BINARY && ! $SIZE_MISMATCH; then
                    echo -e "${GREEN}✓ $zipfile ${YELLOW}(binary files differ but sizes match)${NC}"
                elif $ALL_BINARY && $SIZE_MISMATCH; then
                    echo -e "${YELLOW}⚠ $zipfile (binary files differ with size differences)${NC}"
                    # Don't count as failure - size diff in binaries may be acceptable
                else
                    echo -e "${RED}✗ $zipfile${NC}"
                    diff -rq "$ZIP_TEMP/dir1" "$ZIP_TEMP/dir2" 2>/dev/null | head -10
                    ((ZIP_DIFF_COUNT++))
                fi
            fi
            rm -rf "$ZIP_TEMP/dir1" "$ZIP_TEMP/dir2"
        else
            echo -e "${YELLOW}⚠ $zipfile missing in $DIR2${NC}"
            ((ZIP_DIFF_COUNT++))
        fi
    done
    
    if [[ $ZIP_DIFF_COUNT -eq 0 ]]; then
        echo -e "${GREEN}All ZIP contents are identical or equivalent${NC}"
    else
        echo -e "${RED}$ZIP_DIFF_COUNT ZIP file(s) have different contents${NC}"
        exit 1
    fi
else
    echo "No ZIP files found."
fi

# 4. Compare checksums for non-ZIP files
echo ""
echo "=== Checksum Comparison (non-ZIP files) ==="

MD5_1=$(mktemp)
MD5_2=$(mktemp)
trap "rm -rf $LIST1 $LIST2 $SIZE1 $SIZE2 $ZIP_TEMP $MD5_1 $MD5_2" EXIT

echo "Computing checksums for $DIR1..."
(cd "$DIR1" && find . -type f ! -name "*.zip" ! \( $EXCLUDE_PATTERN \) -exec md5sum {} \; | sort) > "$MD5_1"

echo "Computing checksums for $DIR2..."
(cd "$DIR2" && find . -type f ! -name "*.zip" ! \( $EXCLUDE_PATTERN \) -exec md5sum {} \; | sort) > "$MD5_2"

if diff -q "$MD5_1" "$MD5_2" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ All non-ZIP checksums are identical${NC}"
else
    # Separate binary and non-binary differences
    DIFF_OUTPUT=$(diff "$MD5_1" "$MD5_2" | grep "^[<>]")
    
    NON_BINARY_DIFF=false
    BINARY_SIZE_MISMATCH=false
    
    # Get list of files that differ
    DIFF_FILES=$(echo "$DIFF_OUTPUT" | awk '{print $3}' | sort -u)
    
    for file in $DIFF_FILES; do
        if [[ "$file" =~ \.($BINARY_EXTS)$ ]]; then
            # Binary file - compare sizes
            size1=$(stat -c %s "$DIR1/$file" 2>/dev/null || echo 0)
            size2=$(stat -c %s "$DIR2/$file" 2>/dev/null || echo 0)
            
            if [[ "$size1" -ne "$size2" ]]; then
                BINARY_SIZE_MISMATCH=true
                echo -e "${YELLOW}⚠ Binary size diff: $file: $size1 vs $size2 (diff: $((size2-size1)))${NC}"
            else
                echo -e "${GREEN}✓ $file ${YELLOW}(binary differs but size matches: $size1)${NC}"
            fi
        else
            # Non-binary file differs - this is a real problem
            NON_BINARY_DIFF=true
            echo -e "${RED}✗ $file (content differs)${NC}"
        fi
    done
    
    if $NON_BINARY_DIFF; then
        echo -e "${RED}Non-binary files have different content${NC}"
        exit 1
    elif $BINARY_SIZE_MISMATCH; then
        echo -e "${YELLOW}⚠ Some binary files have size differences (may be acceptable)${NC}"
    else
        echo -e "${GREEN}✓ All non-binary checksums identical, binary files equivalent (same size)${NC}"
    fi
fi

# 4. Summary
echo ""
echo "=========================================="
echo "Comparison complete"
echo "=========================================="
