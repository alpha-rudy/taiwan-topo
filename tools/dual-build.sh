#!/usr/bin/env bash
#
# Run builds with both Makefile and Makefile-2, then compare outputs
# Usage: ./tools/dual-build.sh [SUITE] [TARGET] [extra make args...]
#
# Examples:
#   ./tools/dual-build.sh taiwan mapsforge_zip
#   ./tools/dual-build.sh taiwan mapsforge_style
#   ./tools/dual-build.sh taiwan "mapsforge_style locus_style"
#   ./tools/dual-build.sh taiwan mapsforge_zip VERSION=2025.12.25
#

set -e

SUITE="${1:-taiwan}"
TARGET="${2:-mapsforge_style}"
shift 2 2>/dev/null || true
EXTRA_ARGS="$@"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR_1="$ROOT_DIR/build"
BUILD_DIR_2="$ROOT_DIR/build-2"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=========================================="
echo "Dual Build: Makefile vs Makefile-2"
echo -e "==========================================${NC}"
echo "SUITE:  $SUITE"
echo "TARGET: $TARGET"
echo "EXTRA:  $EXTRA_ARGS"
echo ""

# Build with Makefile
echo -e "${YELLOW}>>> Building with Makefile -> $BUILD_DIR_1${NC}"
make -f "$ROOT_DIR/Makefile" \
    BUILD_DIR="$BUILD_DIR_1" \
    SUITE="$SUITE" \
    $EXTRA_ARGS \
    $TARGET

echo ""

# Build with Makefile-2
echo -e "${YELLOW}>>> Building with Makefile-2 -> $BUILD_DIR_2${NC}"
make -f "$ROOT_DIR/Makefile-2" \
    BUILD_DIR="$BUILD_DIR_2" \
    SUITE="$SUITE" \
    $EXTRA_ARGS \
    $TARGET

echo ""

# Compare
echo -e "${YELLOW}>>> Comparing outputs${NC}"
"$ROOT_DIR/tools/compare-builds.sh" "$BUILD_DIR_1" "$BUILD_DIR_2"
