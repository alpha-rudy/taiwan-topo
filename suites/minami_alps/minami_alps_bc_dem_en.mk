# Suite: minami_alps_bc_dem_en - Minami-Alps basecamp style with DEM (English)
ifeq ($(SUITE),minami_alps_bc_dem_en)
REGION := Minami-Alps
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_minami_alps_10_100_500.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 137.7
RIGHT := 138.65
BOTTOM := 35.15
TOP := 35.9
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/minami_alps_hgtmix.zip
MAPID := $(shell printf %d 0x201c)
TARGETS := gmapsupp_zip gmap nsis
endif
