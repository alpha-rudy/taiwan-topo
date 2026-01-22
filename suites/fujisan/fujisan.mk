# Suite: fujisan - Fujisan (Japan) mapsforge build
ifeq ($(SUITE),fujisan)
REGION := Fujisan
DEM_NAME := AW3D30
LANG := ja
CODE_PAGE := 65001
ELEVATION_FILE = ele_fujisan_10_100_500.pbf
ELEVATION_MIX_FILE = ele_fujisan_10_100_500_mix.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 137.69
RIGHT := 139.55
BOTTOM := 34.30
TOP := 35.95
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/fujisan_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := fujisan_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
FUJISAN_SUITES := fujisan fujisan_bc_dem fujisan_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,fujisan,FUJISAN_SUITES,$(ROOT_DIR)/install-fujisan,fujisan))
