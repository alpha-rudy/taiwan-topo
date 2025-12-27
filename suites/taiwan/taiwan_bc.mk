# Suite: taiwan_bc - Taiwan basecamp style
ifeq ($(SUITE),taiwan_bc)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
LEFT := 118.0000
RIGHT := 123.0348
BOTTOM := 20.62439
TOP := 26.70665
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp
MAPID := $(shell printf %d 0x1016)
TARGETS := gmap nsis
endif
