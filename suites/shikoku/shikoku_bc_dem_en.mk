# Suite: shikoku_bc_dem_en - Shikoku basecamp style with DEM (English)
ifeq ($(SUITE),shikoku_bc_dem_en)
REGION := Shikoku
DEM_NAME := AW3D30
READING_LANG := ja
MAP_LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_shikoku_10_100_500.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 132.0
RIGHT := 134.846
BOTTOM := 32.702
TOP := 34.428
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/shikoku_hgtmix.zip
MAPID := $(shell printf %d 0x200f)
TARGETS := gmapsupp_zip gmap nsis
endif
