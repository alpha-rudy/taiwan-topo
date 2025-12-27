# Suite: sheipa_bc_dem - Sheipa basecamp style with DEM
ifeq ($(SUITE),sheipa_bc_dem)
REGION := Sheipa
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
LEFT := 120.993
RIGHT := 121.353
BOTTOM := 24.241
TOP := 24.535
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1019)
TARGETS := gmapsupp_zip gmap nsis
endif
