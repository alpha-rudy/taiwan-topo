# Suite: nikko_oze - Nikko-Oze mapsforge build
ifeq ($(SUITE),nikko_oze)
REGION := Nikko-Oze
DEM_NAME := AW3D30
LANG := ja
CODE_PAGE := 65001
ELEVATION_FILE = ele_nikko_oze_10_100_500.pbf
ELEVATION_MIX_FILE = ele_nikko_oze_10_100_500_mix.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 138.68
RIGHT := 139.86
BOTTOM := 36.50
TOP := 37.47
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/nikko_oze_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := nikko_oze_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
NIKKO_OZE_SUITES := nikko_oze nikko_oze_bc_dem nikko_oze_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,nikko_oze,NIKKO_OZE_SUITES,$(ROOT_DIR)/install-nikko_oze,nikko_oze))
