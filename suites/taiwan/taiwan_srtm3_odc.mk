# Suite: taiwan_srtm3_odc - Taiwan SRTM3 outdoor classic style
ifeq ($(SUITE),taiwan_srtm3_odc)
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
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
MAPID := $(shell printf %d 0x2012)
TARGETS := gmap
endif
