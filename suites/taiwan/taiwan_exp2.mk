# Suite: taiwan_exp2 - Taiwan experimental build 2
ifeq ($(SUITE),taiwan_exp2)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_20_100_500-2025.o5m
ELEVATION_MIX_FILE = ele_taiwan_20_100_500_marker-2025.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
LEFT := 118.0000
RIGHT := 123.0348
BOTTOM := 20.62439
TOP := 26.70665
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
HGT := $(ROOT_DIR)/hgt/hgt90.zip
TARGETS := mapsforge_zip mapsforge_style gts_all
endif
