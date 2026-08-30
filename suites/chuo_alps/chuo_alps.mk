# Suite: chuo_alps - Chuo-Alps mapsforge build
ifeq ($(SUITE),chuo_alps)
REGION := Chuo-Alps
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_chuo_alps_10_100_500.pbf
ELEVATION_MIX_FILE = ele_chuo_alps_10_100_500_mix.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 137.3
RIGHT := 138.1
BOTTOM := 35.35
TOP := 36.05
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/chuo_alps_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := chuo_alps_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
CHUO_ALPS_SUITES := chuo_alps chuo_alps_bc_dem chuo_alps_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,chuo_alps,CHUO_ALPS_SUITES,$(ROOT_DIR)/install-chuo_alps,chuo_alps))
