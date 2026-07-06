# Suite: yakushima_bc_dem - Yakushima basecamp style with DEM
ifeq ($(SUITE),yakushima_bc_dem)
REGION := Yakushima
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_yakushima_10_100_500.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 129.83
RIGHT := 131.16
BOTTOM := 30.16
TOP := 30.93
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/yakushima_hgtmix.zip
MAPID := $(shell printf %d 0x100c)
TARGETS := gmapsupp_zip gmap nsis
endif
