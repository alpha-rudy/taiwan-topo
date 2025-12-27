# Suite: taiwan_bw_en - Taiwan black & white style (English)
ifeq ($(SUITE),taiwan_bw_en)
REGION := Taiwan
DEM_NAME := MOI
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
BOUNDING_BOX := true
LEFT := 118.0000
RIGHT := 123.0348
BOTTOM := 20.62439
TOP := 26.70665
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x1003)
TARGETS := gmapsupp_zip
endif
