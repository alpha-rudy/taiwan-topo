# Suite: shikoku - Shikoku mapsforge build
ifeq ($(SUITE),shikoku)
REGION := Shikoku
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_shikoku_10_100_500.pbf
ELEVATION_MIX_FILE = ele_shikoku_10_100_500_mix.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 132.0
RIGHT := 134.846
BOTTOM := 32.702
TOP := 34.428
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/shikoku_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := shikoku_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
SHIKOKU_SUITES := shikoku shikoku_bc_dem shikoku_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,shikoku,SHIKOKU_SUITES,$(ROOT_DIR)/install-shikoku,shikoku))
