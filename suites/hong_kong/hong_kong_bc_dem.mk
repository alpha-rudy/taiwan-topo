# Suite: hong_kong_bc_dem - Hong-Kong basecamp style with DEM
ifeq ($(SUITE),hong_kong_bc_dem)
REGION := Hong-Kong
DEM_NAME := AW3D30
READING_LANG := zh
MAP_LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_hong_kong_10_100_500.pbf
EXTRACT_FILE := hong-kong-latest
EXTRACT_URL := https://download.geofabrik.de/asia/china
POLY_FILE := hong-kong.poly
BOUNDING_BOX := true
LEFT := 113.813
RIGHT := 114.506
BOTTOM := 22.13
TOP := 22.569
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/hong_kong_hgtmix.zip
MAPID := $(shell printf %d 0x101b)
TARGETS := gmapsupp_zip gmap nsis
endif
