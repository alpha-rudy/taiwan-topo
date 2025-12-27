# Suite: bbox_odc - Generic bounding box outdoor classic style
# REGION: specify your REGION name for bbox
ifeq ($(SUITE),bbox_odc)
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
MAPID := $(shell printf %d 0x1f12)
TARGETS := gmap
endif
