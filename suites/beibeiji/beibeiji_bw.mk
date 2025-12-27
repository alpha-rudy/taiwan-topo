# Suite: beibeiji_bw - Beibeiji black & white style
ifeq ($(SUITE),beibeiji_bw)
REGION := Beibeiji
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x1313)
TARGETS := gmap
endif
