# Suite: annapurna_bc_dem_en - Annapurna basecamp style with DEM (English)
ifeq ($(SUITE),annapurna_bc_dem_en)
REGION := Annapurna
DEM_NAME := AW3D30
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_annapurna_10_100_500.pbf
EXTRACT_FILE := nepal-latest
BOUNDING_BOX := true
LEFT := 83.0
RIGHT := 85.0
BOTTOM := 28.0
TOP := 29.0
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/annapurna_hgtmix.zip
MAPID := $(shell printf %d 0x4702)
TARGETS := gmapsupp_zip gmap nsis
endif
