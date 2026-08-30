# Suite: chuo_alps_bc_dem_en - Chuo-Alps basecamp style with DEM (English)
ifeq ($(SUITE),chuo_alps_bc_dem_en)
REGION := Chuo-Alps
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_chuo_alps_10_100_500.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 137.3
RIGHT := 138.1
BOTTOM := 35.35
TOP := 36.05
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/chuo_alps_hgtmix.zip
MAPID := $(shell printf %d 0x201a)
TARGETS := gmapsupp_zip gmap nsis
endif
