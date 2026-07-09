# Suite: moscow - Moscow (Russia) mapsforge build, no contours / no DEM
ifeq ($(SUITE),moscow)
REGION := Moscow
READING_LANG := ru
MAP_LANG := zh
CODE_PAGE := 65001
EXTRACT_FILE := central-fed-district-latest
EXTRACT_URL := https://download.geofabrik.de/russia
BOUNDING_BOX := true
LEFT := 36.03
RIGHT := 39.00
BOTTOM := 54.94
TOP := 56.48
NAME_MAPSFORGE := OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
TOPO_PAGE := moscow_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip locus_map
endif

# Suite lists for batch builds
MOSCOW_SUITES := moscow moscow_bc moscow_bc_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,moscow,MOSCOW_SUITES,$(ROOT_DIR)/install-moscow,moscow))
