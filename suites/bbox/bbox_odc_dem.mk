# Suite: bbox_odc_dem - Generic bounding box outdoor classic style with DEM
# REGION: specify your REGION name for bbox
ifeq ($(SUITE),bbox_odc_dem)
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1f14)
TARGETS := gmap
endif
