# Suite: alps_pyrenees_bc_dem_en - Alps-Pyrenees basecamp style with DEM (English)
ifeq ($(SUITE),alps_pyrenees_bc_dem_en)
REGION := Alps-Pyrenees
DEM_NAME := AW3D30
NATIVE_LANG := es
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_alps_pyrenees_10_100_500.pbf
EXTRACT_FILE := spain-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := -2.0
RIGHT := 3.5
BOTTOM := 42.0
TOP := 43.5
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/alps_pyrenees_hgtmix.zip
MAPID := $(shell printf %d 0x200a)
TARGETS := gmapsupp_zip gmap nsis
endif
