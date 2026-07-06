# Suite: alps_core_bc_dem - Alps-Core basecamp style with DEM
ifeq ($(SUITE),alps_core_bc_dem)
REGION := Alps-Core
DESC_PREFIX := EuroPeak
DEM_NAME := AW3D30
READING_LANG := de
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_core_10_100_500.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 7.15
RIGHT := 10.75
BOTTOM := 45.8
TOP := 47.3
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/alps_core_hgtmix.zip
MAPID := $(shell printf %d 0x1008)
TARGETS := gmapsupp_zip gmap nsis
endif
