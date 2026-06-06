# Suite: alps_julian - Alps-Julian mapsforge build
ifeq ($(SUITE),alps_julian)
REGION := Alps-Julian
DEM_NAME := AW3D30
NATIVE_LANG := sl
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_julian_10_100_500.pbf
ELEVATION_MIX_FILE = ele_alps_julian_10_100_500_mix.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 13.3
RIGHT := 16.6
BOTTOM := 45.3
TOP := 46.9
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/alps_julian_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := alps_julian_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
ALPS_JULIAN_SUITES := alps_julian alps_julian_bc_dem alps_julian_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,alps_julian,ALPS_JULIAN_SUITES,$(ROOT_DIR)/install-alps_julian,alps_julian))
