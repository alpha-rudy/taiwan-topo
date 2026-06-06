# Suite: alps_pyrenees_bc_dem - Alps-Pyrenees basecamp style with DEM
ifeq ($(SUITE),alps_pyrenees_bc_dem)
REGION := Alps-Pyrenees
DEM_NAME := AW3D30
NATIVE_LANG := es
LANG := zh
CODE_PAGE := 65001
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
MAPID := $(shell printf %d 0x100a)
TARGETS := gmapsupp_zip gmap nsis
endif
