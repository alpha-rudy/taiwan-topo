# Suite: alps_fareast_bc_dem_en - Alps-Fareast basecamp style with DEM (English)
ifeq ($(SUITE),alps_fareast_bc_dem_en)
REGION := Alps-Fareast
DESC_PREFIX := EuroPeak
DEM_NAME := AW3D30
NATIVE_LANG := de
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_alps_fareast_10_100_500.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 13.9
RIGHT := 15.9
BOTTOM := 46.3
TOP := 47.85
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/alps_fareast_hgtmix.zip
MAPID := $(shell printf %d 0x200b)
TARGETS := gmapsupp_zip gmap nsis
endif
