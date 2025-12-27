# Suite: taiwan_srtm3_odr - Taiwan SRTM3 outdoor style
ifeq ($(SUITE),taiwan_srtm3_odr)
REGION := Taiwan
DEM_NAME := SRTM3
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_view1,srtm1,view3,srtm3.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
LEFT := 118.0000
RIGHT := 123.0348
BOTTOM := 20.62439
TOP := 26.70665
TYP := outdoor
HR_STYLE := fzk
LR_STYLE := fzk
STYLE_NAME := odr
MAPID := $(shell printf %d 0x2011)
TARGETS := gmap
endif
