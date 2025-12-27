# Suite: taipei_bw - Taipei black & white style
ifeq ($(SUITE),taipei_bw)
REGION := Taipei
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x2113)
TARGETS := gmap
endif
