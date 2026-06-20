# Suite: alps_eastern_bc_dem - Alps-Eastern basecamp style with DEM
ifeq ($(SUITE),alps_eastern_bc_dem)
REGION := Alps-Eastern
DEM_NAME := AW3D30
NATIVE_LANG := de
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_eastern_10_100_500.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 9.5
RIGHT := 13.5
BOTTOM := 46.8
TOP := 48.0
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/alps_eastern_hgtmix.zip
MAPID := $(shell printf %d 0x1009)
TARGETS := gmapsupp_zip gmap nsis
endif
