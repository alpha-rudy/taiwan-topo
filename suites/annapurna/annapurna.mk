# Suite: annapurna - Annapurna (Nepal) mapsforge build
ifeq ($(SUITE),annapurna)
REGION := Annapurna
DEM_NAME := AW3D30
LANG := ne
CODE_PAGE := 65001
ELEVATION_FILE = ele_annapurna_10_100_500.pbf
ELEVATION_MIX_FILE = ele_annapurna_10_100_500_mix.pbf
EXTRACT_FILE := nepal-latest
BOUNDING_BOX := true
LEFT := 83.0
RIGHT := 85.0
BOTTOM := 28.0
TOP := 29.0
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/annapurna_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := annapurna_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif
