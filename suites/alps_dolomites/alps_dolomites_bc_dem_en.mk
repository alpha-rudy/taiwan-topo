# Suite: alps_dolomites_bc_dem_en - Alps-Dolomites basecamp style with DEM (English)
ifeq ($(SUITE),alps_dolomites_bc_dem_en)
REGION := Alps-Dolomites
DEM_NAME := AW3D30
NATIVE_LANG := it
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_alps_dolomites_10_100_500.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 9.5
RIGHT := 13.5
BOTTOM := 45.5
TOP := 47.1
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/alps_dolomites_hgtmix.zip
MAPID := $(shell printf %d 0x200c)
TARGETS := gmapsupp_zip gmap nsis
endif
