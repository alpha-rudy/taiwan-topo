# Suite: taiwan_bc_dem_en - Taiwan basecamp style with DEM (English)
ifeq ($(SUITE),taiwan_bc_dem_en)
REGION := Taiwan
DEM_NAME := MOI
LANG := en
CODE_PAGE := 1252
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
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1007)
TARGETS := gmap nsis
endif
