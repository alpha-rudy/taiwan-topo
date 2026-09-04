# Suite: minami_alps_bc_dem - Minami-Alps basecamp style with DEM
ifeq ($(SUITE),minami_alps_bc_dem)
REGION := Minami-Alps
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := zh
CODE_PAGE := 65001
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
MAPID := $(shell printf %d 0x101c)
TARGETS := gmapsupp_zip gmap nsis
endif
