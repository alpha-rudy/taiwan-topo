# Suite: kita_alps - Kita-Alps mapsforge build
ifeq ($(SUITE),kita_alps)
REGION := Kita-Alps
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_kita_alps_10_100_500.pbf
ELEVATION_MIX_FILE = ele_kita_alps_10_100_500_mix.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 137.15
RIGHT := 138.25
BOTTOM := 35.9
TOP := 37.05
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/kita_alps_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := kita_alps_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
KITA_ALPS_SUITES := kita_alps kita_alps_bc_dem kita_alps_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,kita_alps,KITA_ALPS_SUITES,$(ROOT_DIR)/install-kita_alps,kita_alps))
