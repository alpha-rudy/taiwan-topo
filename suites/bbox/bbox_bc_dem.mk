# Suite: bbox_bc_dem - Generic bounding box basecamp style with DEM
# REGION: specify your REGION name for bbox
ifeq ($(SUITE),bbox_bc_dem)
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1f17)
TARGETS := gmap
endif
