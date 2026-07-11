# Suite: saint_petersburg_bc - Saint-Petersburg basecamp style, no DEM
ifeq ($(SUITE),saint_petersburg_bc)
REGION := Saint-Petersburg
READING_LANG := ru
MAP_LANG := zh
CODE_PAGE := 65001
EXTRACT_FILE := northwestern-fed-district-latest
EXTRACT_URL := https://download.geofabrik.de/russia
BOUNDING_BOX := true
LEFT := 29.99
RIGHT := 30.62
BOTTOM := 59.69
TOP := 60.15
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp
MAPID := $(shell printf %d 0x100e)
TARGETS := gmapsupp_zip gmap nsis
endif
