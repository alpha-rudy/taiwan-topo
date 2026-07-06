# Suite: alps_eastern - Alps-Eastern mapsforge build
ifeq ($(SUITE),alps_eastern)
REGION := Alps-Eastern
DESC_PREFIX := EuroPeak
DEM_NAME := AW3D30
READING_LANG := de
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_eastern_10_100_500.pbf
ELEVATION_MIX_FILE = ele_alps_eastern_10_100_500_mix.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 10.5
RIGHT := 14.0
BOTTOM := 45.8
TOP := 47.55
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/alps_eastern_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := alps_eastern_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
ALPS_EASTERN_SUITES := alps_eastern alps_eastern_bc_dem alps_eastern_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,alps_eastern,ALPS_EASTERN_SUITES,$(ROOT_DIR)/install-alps_eastern,alps_eastern))
