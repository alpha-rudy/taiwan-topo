# Suite: kumano - Kumano (Japan) mapsforge build
ifeq ($(SUITE),kumano)
REGION := Kumano
DEM_NAME := AW3D30
LANG := ja
CODE_PAGE := 65001
ELEVATION_FILE = ele_kumano_10_100_500.pbf
ELEVATION_MIX_FILE = ele_kumano_10_100_500_mix.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 135.0
RIGHT := 137.0
BOTTOM := 33.0
TOP := 35.0
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/kumano_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := kumano_topo
TARGETS := mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif
