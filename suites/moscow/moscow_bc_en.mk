# Suite: moscow_bc_en - Moscow basecamp style, no DEM (English)
ifeq ($(SUITE),moscow_bc_en)
REGION := Moscow
READING_LANG := ru
MAP_LANG := en
CODE_PAGE := 1252
EXTRACT_FILE := central-fed-district-latest
EXTRACT_URL := https://download.geofabrik.de/russia
BOUNDING_BOX := true
LEFT := 36.03
RIGHT := 39.00
BOTTOM := 54.94
TOP := 56.48
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp
MAPID := $(shell printf %d 0x200d)
TARGETS := gmapsupp_zip gmap nsis
endif
