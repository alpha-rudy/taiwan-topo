# Suite: kashmir_bc_dem - Kashmir basecamp style with DEM
ifeq ($(SUITE),kashmir_bc_dem)
REGION := Kashmir
DEM_NAME := AW3D30
LANG := hi
CODE_PAGE := 65001
ELEVATION_FILE = ele_kashmir_10_100_500.pbf
EXTRACT_FILE := india-latest
BOUNDING_BOX := true
LEFT := 74.5
RIGHT := 75.5
BOTTOM := 34.0
TOP := 34.75
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/kashmir_hgtmix.zip
MAPID := $(shell printf %d 0x1003)
TARGETS := gmapsupp_zip gmap nsis
endif
