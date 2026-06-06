# Suite: alps_pyrenees - Alps-Pyrenees mapsforge build
ifeq ($(SUITE),alps_pyrenees)
REGION := Alps-Pyrenees
DEM_NAME := AW3D30
NATIVE_LANG := es
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_pyrenees_10_100_500.pbf
ELEVATION_MIX_FILE = ele_alps_pyrenees_10_100_500_mix.pbf
EXTRACT_FILE := spain-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := -2.0
RIGHT := 3.5
BOTTOM := 42.0
TOP := 43.5
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/alps_pyrenees_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := alps_pyrenees_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
ALPS_PYRENEES_SUITES := alps_pyrenees alps_pyrenees_bc_dem alps_pyrenees_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,alps_pyrenees,ALPS_PYRENEES_SUITES,$(ROOT_DIR)/install-alps_pyrenees,alps_pyrenees))
