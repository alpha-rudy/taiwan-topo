# Suite: alps_core - Alps-Core mapsforge build
ifeq ($(SUITE),alps_core)
REGION := Alps-Core
DESC_PREFIX := EuroPeak
DEM_NAME := AW3D30
READING_LANG := de
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_core_10_100_500.pbf
ELEVATION_MIX_FILE = ele_alps_core_10_100_500_mix.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 7.15
RIGHT := 10.75
BOTTOM := 45.8
TOP := 47.3
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/alps_core_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := alps_core_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
ALPS_CORE_SUITES := alps_core alps_core_bc_dem alps_core_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,alps_core,ALPS_CORE_SUITES,$(ROOT_DIR)/install-alps_core,alps_core))
