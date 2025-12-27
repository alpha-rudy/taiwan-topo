# Suite: taiwan - Main Taiwan mapsforge build
ifeq ($(SUITE),taiwan)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
ELEVATION_MIX_FILE = ele_taiwan_10_50_100_500_marker-2025.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
LEFT := 118.0000
RIGHT := 123.0348
BOTTOM := 20.62439
TOP := 26.70665
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := carto
HGT := $(ROOT_DIR)/hgt/hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TARGETS := mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif
