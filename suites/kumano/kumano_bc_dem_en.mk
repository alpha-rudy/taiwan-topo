# Suite: kumano_bc_dem_en - Kumano basecamp style with DEM (English)
ifeq ($(SUITE),kumano_bc_dem_en)
REGION := Kumano
DEM_NAME := AW3D30
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_kumano_10_100_500.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 135.0
RIGHT := 137.0
BOTTOM := 33.0
TOP := 35.0
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/kumano_hgtmix.zip
MAPID := $(shell printf %d 0x4701)
TARGETS := gmapsupp_zip gmap nsis
endif
