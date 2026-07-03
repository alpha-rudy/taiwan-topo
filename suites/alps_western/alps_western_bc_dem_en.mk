# Suite: alps_western_bc_dem_en - Alps-Western basecamp style with DEM (English)
ifeq ($(SUITE),alps_western_bc_dem_en)
REGION := Alps-Western
DESC_PREFIX := EuroPeak
DEM_NAME := AW3D30
READING_LANG := fr
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_alps_western_10_100_500.pbf
EXTRACT_FILE := alps-latest
EXTRACT_URL := https://download.geofabrik.de/europe
BOUNDING_BOX := true
LEFT := 6.0
RIGHT := 8.0
BOTTOM := 44.0
TOP := 46.2
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/alps_western_hgtmix.zip
MAPID := $(shell printf %d 0x200a)
TARGETS := gmapsupp_zip gmap nsis
endif
