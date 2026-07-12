# Suite: saint_petersburg - Saint-Petersburg mapsforge build, no contours / no DEM
ifeq ($(SUITE),saint_petersburg)
REGION := Saint-Petersburg
READING_LANG := ru
MAP_LANG := zh
CODE_PAGE := 65001
EXTRACT_FILE := northwestern-fed-district-latest
EXTRACT_URL := https://download.geofabrik.de/russia
BOUNDING_BOX := true
LEFT := 29.99
RIGHT := 30.62
BOTTOM := 59.69
TOP := 60.15
NAME_MAPSFORGE := OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
# Coastal region without contours: generate the mapsforge sea/nosea overlay
# locally (normally carried by the kcwu ele_*_mix.pbf, which this suite omits)
LANDSEA := true
TOPO_PAGE := saint_petersburg_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip locus_map
endif

# Suite lists for batch builds
SAINT_PETERSBURG_SUITES := saint_petersburg saint_petersburg_bc saint_petersburg_bc_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,saint_petersburg,SAINT_PETERSBURG_SUITES,$(ROOT_DIR)/install-saint_petersburg,saint_petersburg))
