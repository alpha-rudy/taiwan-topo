# Suite: annapurna_bc_dem - Annapurna basecamp style with DEM
ifeq ($(SUITE),annapurna_bc_dem)
REGION := Annapurna
DEM_NAME := AW3D30
LANG := ne
CODE_PAGE := 65001
ELEVATION_FILE = ele_annapurna_10_100_500.pbf
EXTRACT_FILE := nepal-latest
BOUNDING_BOX := true
LEFT := 83.0
RIGHT := 85.0
BOTTOM := 28.0
TOP := 29.0
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/annapurna_hgtmix.zip
MAPID := $(shell printf %d 0x3702)
TARGETS := gmapsupp_zip gmap nsis
endif
