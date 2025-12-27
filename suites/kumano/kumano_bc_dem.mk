# Suite: kumano_bc_dem - Kumano basecamp style with DEM
ifeq ($(SUITE),kumano_bc_dem)
REGION := Kumano
DEM_NAME := AW3D30
LANG := ja
CODE_PAGE := 65001
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
MAPID := $(shell printf %d 0x1018)
TARGETS := gmapsupp_zip gmap nsis
endif
