# Suite: nikko_oze_bc_dem - Nikko-Oze basecamp style with DEM
ifeq ($(SUITE),nikko_oze_bc_dem)
REGION := Nikko-Oze
DEM_NAME := AW3D30
LANG := ja
CODE_PAGE := 65001
ELEVATION_FILE = ele_nikko_oze_10_100_500.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 138.68
RIGHT := 139.86
BOTTOM := 36.50
TOP := 37.47
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/nikko_oze_hgtmix.zip
MAPID := $(shell printf %d 0x1005)
TARGETS := gmapsupp_zip gmap nsis
endif
