# Suite: nikko_oze_bc_dem_en - Nikko-Oze basecamp style with DEM (English)
ifeq ($(SUITE),nikko_oze_bc_dem_en)
REGION := Nikko-Oze
DEM_NAME := AW3D30
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_nikko_oze_10_100_500.pbf
EXTRACT_FILE := japan-latest
BOUNDING_BOX := true
LEFT := 138.52
RIGHT := 140.62
BOTTOM := 36.5
TOP := 37.68
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/nikko_oze_hgtmix.zip
MAPID := $(shell printf %d 0x2005)
TARGETS := gmapsupp_zip gmap nsis
endif
