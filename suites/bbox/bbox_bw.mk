# Suite: bbox_bw - Generic bounding box black & white style
# REGION: specify your REGION name for bbox
ifeq ($(SUITE),bbox_bw)
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x1f13)
TARGETS := gmap
endif
