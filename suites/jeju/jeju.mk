# Suite: jeju - Jeju mapsforge build
ifeq ($(SUITE),jeju)
REGION := Jeju
DEM_NAME := AW3D30
READING_LANG := ko
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_jeju_10_100_500.pbf
ELEVATION_MIX_FILE = ele_jeju_10_100_500_mix.pbf
EXTRACT_FILE := south-korea-latest
BOUNDING_BOX := true
LEFT := 126.138
RIGHT := 126.978
BOTTOM := 33.108
TOP := 34.018
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/jeju_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := jeju_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
JEJU_SUITES := jeju jeju_bc_dem jeju_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,jeju,JEJU_SUITES,$(ROOT_DIR)/install-jeju,jeju))
