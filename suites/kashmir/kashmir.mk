# Suite: kashmir - Kashmir (India) mapsforge build
ifeq ($(SUITE),kashmir)
REGION := Kashmir
DEM_NAME := AW3D30
LANG := hi
CODE_PAGE := 65001
ELEVATION_FILE = ele_kashmir_10_100_500.pbf
ELEVATION_MIX_FILE = ele_kashmir_10_100_500_mix.pbf
EXTRACT_FILE := india-latest
BOUNDING_BOX := true
LEFT := 74.5
RIGHT := 75.5
BOTTOM := 34.0
TOP := 34.75
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/kashmir_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := kashmir_topo
TARGETS := mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif
