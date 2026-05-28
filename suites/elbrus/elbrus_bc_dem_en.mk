# Suite: elbrus_bc_dem_en - Elbrus basecamp style with DEM (English)
ifeq ($(SUITE),elbrus_bc_dem_en)
REGION := Elbrus
DEM_NAME := AW3D30
NATIVE_LANG := ru
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_elbrus_10_100_500.pbf
EXTRACT_FILE := north-caucasus-fed-district-latest
EXTRACT_URL := https://download.geofabrik.de/russia
BOUNDING_BOX := true
LEFT := 41.90
RIGHT := 43.80
BOTTOM := 43.10
TOP := 43.75
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/elbrus_hgtmix.zip
MAPID := $(shell printf %d 0x2006)
TARGETS := gmapsupp_zip gmap nsis
endif
