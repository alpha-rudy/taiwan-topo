# Suite: beibeiji_bw_en - Beibeiji black & white style (English)
ifeq ($(SUITE),beibeiji_bw_en)
REGION := Beibeiji
DEM_NAME := MOI
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x1303)
TARGETS := gmapsupp_zip
endif
