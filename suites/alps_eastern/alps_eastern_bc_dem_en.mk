# Suite: alps_eastern_bc_dem_en - Alps-Eastern basecamp style with DEM (English)
ifeq ($(SUITE),alps_eastern_bc_dem_en)
REGION := Alps-Eastern
DESC_PREFIX := EuroPeak
DEM_NAME := AW3D30
NATIVE_LANG := de
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_alps_eastern_10_100_500.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 10.5
RIGHT := 14.0
BOTTOM := 45.8
TOP := 47.55
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/alps_eastern_hgtmix.zip
MAPID := $(shell printf %d 0x2009)
TARGETS := gmapsupp_zip gmap nsis
endif
