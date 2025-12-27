# Suite: yushan_odc - Yushan outdoor classic style
ifeq ($(SUITE),yushan_odc)
REGION := Yushan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
MAPID := $(shell printf %d 0x1412)
TARGETS := gmap
endif
