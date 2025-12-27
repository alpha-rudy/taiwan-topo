# Suite: yushan_bc - Yushan basecamp style
ifeq ($(SUITE),yushan_bc)
REGION := Yushan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp
MAPID := $(shell printf %d 0x1416)
TARGETS := gmap
endif
