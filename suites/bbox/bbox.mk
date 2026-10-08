# Suite: bbox - Generic bounding box mapsforge build
# REGION: specify your REGION name for bbox
ifeq ($(SUITE),bbox)
DEM_NAME := MOI
MAP_LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2026.pbf
ELEVATION_MIX_FILE = ele_taiwan_10_100_500_mix-2026.pbf
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
TARGETS := mapsforge
endif
