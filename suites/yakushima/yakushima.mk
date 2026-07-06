# Suite: yakushima - Yakushima mapsforge build
ifeq ($(SUITE),yakushima)
REGION := Yakushima
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_yakushima_10_100_500.pbf
ELEVATION_MIX_FILE = ele_yakushima_10_100_500_mix.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 129.83
RIGHT := 131.16
BOTTOM := 30.16
TOP := 30.93
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/yakushima_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := yakushima_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
YAKUSHIMA_SUITES := yakushima yakushima_bc_dem yakushima_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,yakushima,YAKUSHIMA_SUITES,$(ROOT_DIR)/install-yakushima,yakushima))
