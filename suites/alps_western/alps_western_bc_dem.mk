# Suite: alps_western_bc_dem - Alps-Western basecamp style with DEM
ifeq ($(SUITE),alps_western_bc_dem)
REGION := Alps-Western
DEM_NAME := AW3D30
NATIVE_LANG := fr
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_western_10_100_500.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 6.0
RIGHT := 8.0
BOTTOM := 44.0
TOP := 46.2
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/alps_western_hgtmix.zip
MAPID := $(shell printf %d 0x100a)
TARGETS := gmapsupp_zip gmap nsis
endif
