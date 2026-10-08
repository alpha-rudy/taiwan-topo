# Suite: taiwan_exp - Taiwan experimental build
ifeq ($(SUITE),taiwan_exp)
REGION := Taiwan
DEM_NAME := MOI
MAP_LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2026.pbf
ELEVATION_MIX_FILE = ele_taiwan_10_100_500_mix-2026.pbf
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
LEFT := 118.0000
RIGHT := 123.0348
BOTTOM := 20.62439
TOP := 26.70665
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
TARGETS := mapsforge_zip
endif
