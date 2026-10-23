# Suite: jeju_bc_dem_en - Jeju basecamp style with DEM (English)
ifeq ($(SUITE),jeju_bc_dem_en)
REGION := Jeju
DEM_NAME := AW3D30
READING_LANG := ko
MAP_LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_jeju_10_100_500.pbf
EXTRACT_FILE := south-korea-latest
BOUNDING_BOX := true
LEFT := 126.138
RIGHT := 126.978
BOTTOM := 33.108
TOP := 34.018
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/jeju_hgtmix.zip
MAPID := $(shell printf %d 0x201d)
TARGETS := gmapsupp_zip gmap nsis
endif
