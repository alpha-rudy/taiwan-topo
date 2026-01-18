# Suite: fujisan_bc_dem - Fujisan basecamp style with DEM
ifeq ($(SUITE),fujisan_bc_dem)
REGION := Fujisan
DEM_NAME := AW3D30
LANG := ja
CODE_PAGE := 65001
ELEVATION_FILE = ele_fujisan_10_100_500.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 138.15
RIGHT := 139.55
BOTTOM := 34.30
TOP := 35.95
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/fujisan_hgtmix.zip
MAPID := $(shell printf %d 0x3704)
TARGETS := gmapsupp_zip gmap nsis
endif
