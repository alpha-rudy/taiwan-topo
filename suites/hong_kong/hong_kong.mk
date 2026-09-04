# Suite: hong_kong - Hong-Kong mapsforge build
ifeq ($(SUITE),hong_kong)
REGION := Hong-Kong
DEM_NAME := AW3D30
READING_LANG := zh
MAP_LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_hong_kong_10_100_500.pbf
ELEVATION_MIX_FILE = ele_hong_kong_10_100_500_mix.pbf
EXTRACT_FILE := hong-kong-latest
EXTRACT_URL := https://download.geofabrik.de/asia/china
POLY_FILE := hong-kong.poly
BOUNDING_BOX := true
LEFT := 113.813
RIGHT := 114.506
BOTTOM := 22.13
TOP := 22.569
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/hong_kong_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := hong_kong_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
HONG_KONG_SUITES := hong_kong hong_kong_bc_dem hong_kong_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,hong_kong,HONG_KONG_SUITES,$(ROOT_DIR)/install-hong_kong,hong_kong))
