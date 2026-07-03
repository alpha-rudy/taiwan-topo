# Suite: elbrus - Elbrus (Russia Caucasus) mapsforge build
ifeq ($(SUITE),elbrus)
REGION := Elbrus
DESC_PREFIX := EuroPeak
DEM_NAME := AW3D30
READING_LANG := ru
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_elbrus_10_100_500.pbf
ELEVATION_MIX_FILE = ele_elbrus_10_100_500_mix.pbf
EXTRACT_FILE := north-caucasus-fed-district-latest
EXTRACT_URL := https://download.geofabrik.de/russia
BOUNDING_BOX := true
LEFT := 41.90
RIGHT := 43.80
BOTTOM := 43.10
TOP := 43.75
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/elbrus_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := elbrus_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
ELBRUS_SUITES := elbrus elbrus_bc_dem elbrus_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,elbrus,ELBRUS_SUITES,$(ROOT_DIR)/install-elbrus,elbrus))
