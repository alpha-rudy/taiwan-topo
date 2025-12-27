# Suite: kyushu_srtm3_en_bw - Kyushu SRTM3 black & white style (English)
ifeq ($(SUITE),kyushu_srtm3_en_bw)
REGION := Kyushu
DEM_NAME := SRTM3
LANG := en
CODE_PAGE := 950
#CODE_PAGE := 1252
ELEVATION_FILE = ele_japan_10_100_500_view1,view3.o5m
EXTRACT_FILE := japan-latest
POLY_FILE := Kyushu.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x2313)
TARGETS := gmap
endif
