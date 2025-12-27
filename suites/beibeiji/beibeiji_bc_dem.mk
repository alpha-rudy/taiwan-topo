# Suite: beibeiji_bc_dem - Beibeiji basecamp style with DEM
ifeq ($(SUITE),beibeiji_bc_dem)
REGION := Beibeiji
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2025.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1317)
TARGETS := gmapsupp_zip gmap nsis
endif
