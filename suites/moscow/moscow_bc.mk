# Suite: moscow_bc - Moscow basecamp style, no DEM
ifeq ($(SUITE),moscow_bc)
REGION := Moscow
READING_LANG := ru
MAP_LANG := zh
CODE_PAGE := 65001
EXTRACT_FILE := central-fed-district-latest
EXTRACT_URL := https://download.geofabrik.de/russia
BOUNDING_BOX := true
LEFT := 37.24
RIGHT := 38.02
BOTTOM := 55.46
TOP := 56.01
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp
MAPID := $(shell printf %d 0x100d)
TARGETS := gmapsupp_zip gmap nsis
endif
