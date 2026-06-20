# Suite: alps_dolomites_bc_dem - Alps-Dolomites basecamp style with DEM
ifeq ($(SUITE),alps_dolomites_bc_dem)
REGION := Alps-Dolomites
DEM_NAME := AW3D30
NATIVE_LANG := it
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_dolomites_10_100_500.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 9.5
RIGHT := 13.5
BOTTOM := 45.5
TOP := 47.1
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/alps_dolomites_hgtmix.zip
MAPID := $(shell printf %d 0x100c)
TARGETS := gmapsupp_zip gmap nsis
endif
