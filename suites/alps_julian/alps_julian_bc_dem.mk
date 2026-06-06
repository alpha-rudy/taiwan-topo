# Suite: alps_julian_bc_dem - Alps-Julian basecamp style with DEM
ifeq ($(SUITE),alps_julian_bc_dem)
REGION := Alps-Julian
DEM_NAME := AW3D30
NATIVE_LANG := sl
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_alps_julian_10_100_500.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 13.3
RIGHT := 16.6
BOTTOM := 45.3
TOP := 46.9
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/alps_julian_hgtmix.zip
MAPID := $(shell printf %d 0x100b)
TARGETS := gmapsupp_zip gmap nsis
endif
