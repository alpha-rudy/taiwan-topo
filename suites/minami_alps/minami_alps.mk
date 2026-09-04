# Suite: minami_alps - Minami-Alps mapsforge build
ifeq ($(SUITE),minami_alps)
REGION := Minami-Alps
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_minami_alps_10_100_500.pbf
ELEVATION_MIX_FILE = ele_minami_alps_10_100_500_mix.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 137.7
RIGHT := 138.65
BOTTOM := 35.15
TOP := 35.9
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/minami_alps_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := minami_alps_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
MINAMI_ALPS_SUITES := minami_alps minami_alps_bc_dem minami_alps_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,minami_alps,MINAMI_ALPS_SUITES,$(ROOT_DIR)/install-minami_alps,minami_alps))
