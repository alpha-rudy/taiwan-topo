# Suite: kita_alps_bc_dem - Kita-Alps basecamp style with DEM
ifeq ($(SUITE),kita_alps_bc_dem)
REGION := Kita-Alps
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_kita_alps_10_100_500.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 137.15
RIGHT := 138.25
BOTTOM := 35.9
TOP := 37.05
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/kita_alps_hgtmix.zip
MAPID := $(shell printf %d 0x1018)
TARGETS := gmapsupp_zip gmap nsis
endif
