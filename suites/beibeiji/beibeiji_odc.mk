# Suite: beibeiji_odc - Beibeiji outdoor classic style
ifeq ($(SUITE),beibeiji_odc)
REGION := Beibeiji
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
MAPID := $(shell printf %d 0x1312)
TARGETS := gmap
endif
