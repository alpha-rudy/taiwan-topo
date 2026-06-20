# Suite: alps_dolomites - Alps-Dolomites mapsforge build
ifeq ($(SUITE),alps_dolomites)
REGION := Alps-Dolomites
DEM_NAME := AW3D30
NATIVE_LANG := it
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_dolomites_10_100_500.pbf
ELEVATION_MIX_FILE = ele_alps_dolomites_10_100_500_mix.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 9.5
RIGHT := 13.5
BOTTOM := 45.5
TOP := 47.1
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/alps_dolomites_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := alps_dolomites_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
ALPS_DOLOMITES_SUITES := alps_dolomites alps_dolomites_bc_dem alps_dolomites_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,alps_dolomites,ALPS_DOLOMITES_SUITES,$(ROOT_DIR)/install-alps_dolomites,alps_dolomites))
