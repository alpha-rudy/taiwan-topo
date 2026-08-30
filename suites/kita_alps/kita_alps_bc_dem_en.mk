# Suite: kita_alps_bc_dem_en - Kita-Alps basecamp style with DEM (English)
ifeq ($(SUITE),kita_alps_bc_dem_en)
REGION := Kita-Alps
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := en
CODE_PAGE := 1252
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
MAPID := $(shell printf %d 0x2018)
TARGETS := gmapsupp_zip gmap nsis
endif
