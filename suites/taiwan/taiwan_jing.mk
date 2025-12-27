# Suite: taiwan_jing - Taiwan jing style
ifeq ($(SUITE),taiwan_jing)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
LEFT := 118.0000
RIGHT := 123.0348
BOTTOM := 20.62439
TOP := 26.70665
TYP := jing
HR_STYLE := jing
LR_STYLE := jing
STYLE_NAME := jing
MAPID := $(shell printf %d 0x2010)
TARGETS := gmap
endif
