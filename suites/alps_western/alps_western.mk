# Suite: alps_western - Alps-Western mapsforge build
ifeq ($(SUITE),alps_western)
REGION := Alps-Western
DEM_NAME := AW3D30
NATIVE_LANG := fr
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_western_10_100_500.pbf
ELEVATION_MIX_FILE = ele_alps_western_10_100_500_mix.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 6.0
RIGHT := 8.0
BOTTOM := 44.0
TOP := 46.2
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/alps_western_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := alps_western_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
ALPS_WESTERN_SUITES := alps_western alps_western_bc_dem alps_western_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,alps_western,ALPS_WESTERN_SUITES,$(ROOT_DIR)/install-alps_western,alps_western))
