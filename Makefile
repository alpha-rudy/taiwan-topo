# base (0x2000) + region x lang x style
# where, ...
# - 1st hex, dem -> moi(1), srtm(2)
# - 2nd hex, region -> taiwan(0), taipei(1), kyushu(2), Beibeiji(3), Yushan(4), bbox(f)
# - 3rd hex, lang -> en(0), zh(1),
# - 4th hex, style -> jing(0), outdoor(1), odc(2), bw(3), odc_dem(4), bw_dem(5), bc(6), bc_dem(7), exp(8)

SHELL := /usr/bin/env bash

# suggestion: no more than CPU*2
MAPWITER_THREADS = 8
# suggestion: doesn't matter
SPLITTER_THREADS = 8
# suggestion: CPU*1
MKGMAP_JOBS = 8
# finetune options
JAVACMD_OPTIONS ?= -Xmx68G -server

# directory variables
ROOT_DIR := $(shell pwd)
TOOLS_DIR := $(ROOT_DIR)/tools
OSMOSIS_CMD := $(TOOLS_DIR)/osmosis-0.48.2/bin/osmosis
ifeq ($(shell uname),Darwin)
OSMCONVERT_CMD := $(TOOLS_DIR)/osmconvert-0.8.11/osx/osmconvert
else
OSMCONVERT_CMD := $(TOOLS_DIR)/osmconvert-0.8.11/linux/osmconvert64
endif
SEA_DIR := $(ROOT_DIR)/sea
BOUNDS_DIR := $(ROOT_DIR)/bounds
CITIES_DIR := $(ROOT_DIR)/cities
POLIES_DIR := $(ROOT_DIR)/polies
WORKS_DIR := $(ROOT_DIR)/work
BUILD_DIR := $(ROOT_DIR)/install
DOWNLOAD_DIR := $(ROOT_DIR)/download
ELEVATIONS_DIR := $(DOWNLOAD_DIR)/osm_elevations
EXTRACT_DIR := $(DOWNLOAD_DIR)/extracts


# target SUITE, no default
ifeq ($(SUITE),yushan)
REGION := Yushan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
ELEVATION_MIX_FILE = ele_taiwan_10_50_100_500_marker-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
MAPSFORGE_BBOX := 23.226,120.822,23.578,121.249
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
TARGETS := mapsforge

else ifeq ($(SUITE),exp)
# none

else ifeq ($(SUITE),bbox)
# REGION: specify your REGION name for bbox
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
ELEVATION_MIX_FILE = ele_taiwan_10_50_100_500_marker-2019.7.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TARGETS := mapsforge

else ifeq ($(SUITE),bbox_bw)
# REGION: specify your REGION name for bbox
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x1f13)
TARGETS := gmap

else ifeq ($(SUITE),bbox_odc)
# REGION: specify your REGION name for bbox
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
MAPID := $(shell printf %d 0x1f12)
TARGETS := gmap

else ifeq ($(SUITE),bbox_odc_dem)
# REGION: specify your REGION name for bbox
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1f14)
TARGETS := gmap

else ifeq ($(SUITE),bbox_bc_dem)
# REGION: specify your REGION name for bbox
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1f17)
TARGETS := gmap

else ifeq ($(SUITE),taiwan)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
ELEVATION_MIX_FILE = ele_taiwan_10_50_100_500_marker-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
MAPSFORGE_BBOX := 21.55682,118.12141,26.44212,122.31377
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
HGT := $(ROOT_DIR)/hgt/hgtmix.zip
GTS_STYLE = $(HS_STYLE)
GTS_ALL := $(BUILD_DIR)/$(NAME_MAPSFORGE)
CARTO_ALL := $(BUILD_DIR)/carto_all
TARGETS := mapsforge_zip poi_zip gts_all carto_all

else ifeq ($(SUITE),taiwan_lite)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_20_100_500-2019.7.o5m
ELEVATION_MIX_FILE = ele_taiwan_20_100_500_marker-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
MAPSFORGE_BBOX := 21.55682,118.12141,26.44212,122.31377
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Lite
HGT := $(ROOT_DIR)/hgt/hgt90.zip
GTS_STYLE = $(LITE_STYLE)
GTS_ALL := $(BUILD_DIR)/$(NAME_MAPSFORGE)
TARGETS := mapsforge_zip gts_all

else ifeq ($(SUITE),beibeiji)
REGION := Beibeiji
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
ELEVATION_MIX_FILE = ele_taiwan_10_50_100_500_marker-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
MAPSFORGE_BBOX := 24.6731646,121.2826336,25.2997353,122.0064049
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
TARGETS := mapsforge

else ifeq ($(SUITE),taipei)
REGION := Taipei
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
ELEVATION_MIX_FILE = ele_taiwan_10_50_100_500_marker-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
MAPSFORGE_BBOX := 24.96034,121.4570,25.21024,121.6659
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
TARGETS := mapsforge_zip

else ifeq ($(SUITE),yushan_bw)
REGION := Yushan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x1413)
TARGETS := gmap

else ifeq ($(SUITE),yushan_odc)
REGION := Yushan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
MAPID := $(shell printf %d 0x1412)
TARGETS := gmap

else ifeq ($(SUITE),yushan_odc_dem)
REGION := Yushan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1414)
TARGETS := gmap

else ifeq ($(SUITE),yushan_bc)
REGION := Yushan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp
MAPID := $(shell printf %d 0x1416)
TARGETS := gmap

else ifeq ($(SUITE),beibeiji_bw)
REGION := Beibeiji
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x1313)
TARGETS := gmap

else ifeq ($(SUITE),beibeiji_bw_en)
REGION := Beibeiji
DEM_NAME := MOI
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x1303)
TARGETS := gmapsupp_zip

else ifeq ($(SUITE),beibeiji_odc)
REGION := Beibeiji
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
MAPID := $(shell printf %d 0x1312)
TARGETS := gmap

else ifeq ($(SUITE),beibeiji_bc_dem)
REGION := Beibeiji
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1317)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taiwan_jing)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := jing
HR_STYLE := jing
LR_STYLE := jing
STYLE_NAME := jing
MAPID := $(shell printf %d 0x2010)
TARGETS := gmap

else ifeq ($(SUITE),taiwan_srtm3_odr)
REGION := Taiwan
DEM_NAME := SRTM3
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_view1,srtm1,view3,srtm3.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := outdoor
HR_STYLE := fzk
LR_STYLE := fzk
STYLE_NAME := odr
MAPID := $(shell printf %d 0x2011)
TARGETS := gmap

else ifeq ($(SUITE),taiwan_srtm3_odc)
REGION := Taiwan
DEM_NAME := SRTM3
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_view1,srtm1,view3,srtm3.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
MAPID := $(shell printf %d 0x2012)
TARGETS := gmap

else ifeq ($(SUITE),taiwan_srtm3_bw)
REGION := Taiwan
DEM_NAME := SRTM3
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_view1,srtm1,view3,srtm3.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x2013)
TARGETS := gmap

else ifeq ($(SUITE),taiwan_bw)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x1013)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taiwan_bw_en)
REGION := Taiwan
DEM_NAME := MOI
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x1003)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taiwan_odc)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
MAPID := $(shell printf %d 0x1012)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taiwan_bw_dem)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1015)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taiwan_odc_dem)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1014)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taiwan_bc)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp
MAPID := $(shell printf %d 0x1016)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taiwan_bc_dem)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1017)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taiwan_bc_dem_en)
REGION := Taiwan
DEM_NAME := MOI
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1007)
TARGETS := gmap nsis

else ifeq ($(SUITE),taiwan_exp)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
ELEVATION_MIX_FILE = ele_taiwan_10_50_100_500_marker-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
MAPSFORGE_BBOX := 20.150,115.650,26.44212,122.31377
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
TARGETS := mapsforge_zip

else ifeq ($(SUITE),taiwan_exp2)
REGION := Taiwan
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_20_100_500-2019.7.o5m
ELEVATION_MIX_FILE = ele_taiwan_20_100_500_marker-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
MAPSFORGE_BBOX := 21.55682,118.12141,26.44212,122.31377
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
HGT := $(ROOT_DIR)/hgt/hgt90.zip
TARGETS := mapsforge_zip mapsforge_style gts_all

else ifeq ($(SUITE),taipei_odc)
REGION := Taipei
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
TYP := outdoorc
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := odc
MAPID := $(shell printf %d 0x2112)
TARGETS := gmap

else ifeq ($(SUITE),taipei_bw)
REGION := Taipei
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x2113)
TARGETS := gmap

else ifeq ($(SUITE),taipei_bc)
REGION := Taipei
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp
MAPID := $(shell printf %d 0x1116)
TARGETS := gmap

else ifeq ($(SUITE),taipei_bc_dem)
REGION := Taipei
DEM_NAME := MOI
LANG := zh
CODE_PAGE := 65001
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/hgtmix.zip
MAPID := $(shell printf %d 0x1117)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taipei_en_bw)
REGION := Taipei
DEM_NAME := MOI
LANG := en
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500-2019.7.o5m
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x2103)
TARGETS := gmap

else ifeq ($(SUITE),kyushu_srtm3_en_bw)
REGION := Kyushu
DEM_NAME := SRTM3
LANG := en
CODE_PAGE := 950
#CODE_PAGE := 1252
ELEVATION_FILE = ele_japan_10_100_500_view1,view3.o5m
EXTRACT_FILE := japan-latest
POLY_FILE := Kyushu.poly
TYP := bw
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := bw
MAPID := $(shell printf %d 0x2313)
TARGETS := gmap

endif

# auto variables
VERSION := $(shell date +%Y.%m.%d)
MAPID_LO_HEX := $(shell printf '%x' $(MAPID) | cut -c3-4)
MAPID_HI_HEX := $(shell printf '%x' $(MAPID) | cut -c1-2)
DUMMYID = 9999

ifeq ($(LANG),zh)
NAME_LONG := $(DEM_NAME).OSM.$(STYLE_NAME) - $(REGION) TOPO v$(VERSION) (by Rudy)
NAME_SHORT := $(DEM_NAME).OSM.$(STYLE_NAME) - $(REGION) TOPO v$(VERSION) (by Rudy)
NAME_WORD := $(DEM_NAME)_$(REGION)_TOPO_$(STYLE_NAME)
else
NAME_LONG := $(DEM_NAME).OSM.$(STYLE_NAME).$(LANG) - $(REGION) TOPO v$(VERSION) (by Rudy)
NAME_SHORT := $(DEM_NAME).OSM.$(STYLE_NAME).$(LANG) - $(REGION) TOPO v$(VERSION) (by Rudy)
NAME_WORD := $(DEM_NAME)_$(REGION)_TOPO_$(STYLE_NAME)_$(LANG)
endif

COMMON_TILES_DIR := $(WORKS_DIR)/$(REGION)/tiles
TILES_DIR := $(WORKS_DIR)/$(REGION)/tiles-$(MAPID)
MAP_DIR := $(WORKS_DIR)/$(REGION)/$(NAME_WORD)
MAP_HIDEM_DIR := $(MAP_DIR)_hidem
MAP_LODEM_DIR := $(MAP_DIR)_lodem
MAP_NODEM_HR_DIR := $(MAP_DIR)_nodemhr
MAP_NODEM_LR_DIR := $(MAP_DIR)_nodemlr
MAP_HIDEM := $(MAP_HIDEM_DIR)/.MAP_HIDEM.done
MAP_LODEM := $(MAP_LODEM_DIR)/.MAP_LOWDEM.done
MAP_NODEM_HR := $(MAP_NODEM_HR_DIR)/.MAP_NODEM_HR.done
MAP_NODEM_LR := $(MAP_NODEM_LR_DIR)/.MAP_NODEM_LR.done
ifeq ($(GMAPDEM),)
MAP_PC_DIR := $(MAP_NODEM_HR_DIR)
MAP_HAND_DIR := $(MAP_NODEM_LR_DIR)
MAP_PC := $(MAP_NODEM_HR)
MAP_HAND := $(MAP_NODEM_LR)
else
MAP_PC_DIR := $(MAP_HIDEM_DIR)
MAP_HAND_DIR := $(MAP_LODEM_DIR)
MAP_PC := $(MAP_HIDEM)
MAP_HAND := $(MAP_LODEM)
endif

# these elevation files are converted to o5m format by
#   osmconvert --drop-version file.osm.pbf -o=file.o5m
ELEVATION := $(ELEVATIONS_DIR)/$(ELEVATION_FILE)
ELEVATION_MIX := $(ELEVATIONS_DIR)/marker/$(ELEVATION_MIX_FILE)
EXTRACT := $(EXTRACT_DIR)/$(EXTRACT_FILE)
CITY := $(CITIES_DIR)/TW.zip
COMMON_TILES := $(COMMON_TILES_DIR)/.COMMON_TILES.done
TILES := $(TILES_DIR)/.TILES.done
GMAP_INPUT := $(BUILD_DIR)/$(REGION).o5m
TYP_FILE := $(ROOT_DIR)/TYPs/$(TYP).txt
HR_STYLE_DIR := $(ROOT_DIR)/styles/$(HR_STYLE)
LR_STYLE_DIR := $(ROOT_DIR)/styles/$(LR_STYLE)
TAG_MAPPING := $(ROOT_DIR)/osm_scripts/tag-mapping.xml
POI_MAPPING := $(ROOT_DIR)/osm_scripts/poi-mapping.xml

DEM_FIX := $(shell echo $(DEM_NAME) | tr A-Z a-z)

GMAPSUPP := $(BUILD_DIR)/gmapsupp_$(REGION)_$(DEM_FIX)_$(LANG)_$(STYLE_NAME).img
GMAPSUPP_ZIP := $(GMAPSUPP).zip
GMAP := $(BUILD_DIR)/$(REGION)_$(DEM_FIX)_$(LANG)_$(STYLE_NAME).gmap.zip
NSIS := $(BUILD_DIR)/Install_$(NAME_WORD).exe
POI := $(BUILD_DIR)/$(NAME_MAPSFORGE).poi
POI_ZIP := $(POI).zip
MAPSFORGE := $(BUILD_DIR)/$(NAME_MAPSFORGE).map
MAPSFORGE_ZIP := $(MAPSFORGE).zip
MAPSFORGE_PBF := $(BUILD_DIR)/$(NAME_MAPSFORGE)_zls.osm.pbf
LICENSE := $(BUILD_DIR)/taiwan_topo.html

ifeq ($(shell uname),Darwin)
MD5_CMD := md5 -q $$EXAM_FILE
JMC_CMD := jmc/osx/jmc_cli
SED_CMD := gsed
else
MD5_CMD := md5sum $$EXAM_FILE | cut -d' ' -f1
JMC_CMD := jmc/linux/jmc_cli
SED_CMD := sed
endif

ZIP_CMD := 7z a -tzip -mx=6
MAKE_CMD := make

all: $(TARGETS)

clean:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(WORKS_DIR)" ]
	-rm -rf $(BUILD_DIR)
	-rm -rf $(WORKS_DIR)

.PHONY: clean-elevations
clean-elevations:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(WORKS_DIR)" ]
	-rm -rf $(BUILD_DIR)
	-rm -rf $(WORKS_DIR)
	-rm -rf $(ELEVATIONS_DIR)

.PHONY: clean-extracts
clean-extracts:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(WORKS_DIR)" ]
	-rm -rf $(BUILD_DIR)
	-rm -rf $(WORKS_DIR)
	-rm -rf $(EXTRACT_DIR)

.PHONY: distclean
distclean:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(WORKS_DIR)" ]
	-rm -rf $(BUILD_DIR)
	-rm -rf $(WORKS_DIR)
	-rm -rf $(DOWNLOAD_DIR)

.PHONY: install
install: $(LICENSE) $(GMAPSUPP)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(INSTALL_DIR)" ]
	[ -d "$(INSTALL_DIR)" ]
	cp -r $(GMAPSUPP) $(INSTALL_DIR)
	cp -r $(BUILD_DIR)/docs/images $(INSTALL_DIR)
	cp $(LICENSE) $(INSTALL_DIR)/taiwan_topo.html

.PHONY: drop
drop:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(INSTALL_DIR)" ]
	[ -d "$(INSTALL_DIR)" ]
	cp -r docs/images auto-install/*.xml $(INSTALL_DIR)
	cat docs/index.json | $(SED_CMD) -e "s|__version__|$(VERSION)|g" > $(INSTALL_DIR)/index.json
	cp -r $(BUILD_DIR)/{*.zip,*.exe,*.html} $(INSTALL_DIR)
	-cp -r $(BUILD_DIR)/*.cpkg $(INSTALL_DIR)
	cd $(INSTALL_DIR) && md5sum *.zip *.exe *.html *.xml > md5sum.txt
	cat docs/beta.md | $(SED_CMD) -e "s|__version__|$(VERSION)|g" | \
		markdown -f +autolink > $(BUILD_DIR)/beta.article
	cat docs/github_flavor.html | $(SED_CMD) "/__article_body__/ r $(BUILD_DIR)/beta.article" > $(INSTALL_DIR)/beta.html
	cp -r docs/gts $(INSTALL_DIR) && \
		cat docs/gts/index.html | $(SED_CMD) -e "s|__version__|$(VERSION)|g" > $(INSTALL_DIR)/gts/index.html

.PHONY: styles
styles:
	$(MAKE_CMD) mapsforge_style lite_style hs_style locus_style twmap_style bn_style dn_style tn_style extra_style


.PHONY: daily
daily:
	$(MAKE_CMD) styles
	$(MAKE_CMD) SUITE=taiwan mapsforge_zip
	$(MAKE_CMD) SUITE=taiwan_bc_dem gmap nsis

.PHONY: suites
suites:
	$(MAKE_CMD) styles
	$(MAKE_CMD) SUITE=taiwan all
	$(MAKE_CMD) SUITE=taiwan_lite all
	$(MAKE_CMD) SUITE=taiwan_bw all
	$(MAKE_CMD) SUITE=taiwan_odc all
	$(MAKE_CMD) SUITE=taiwan_bc all
	$(MAKE_CMD) SUITE=taiwan_bw_dem all
	$(MAKE_CMD) SUITE=taiwan_odc_dem all
	$(MAKE_CMD) SUITE=taiwan_bc_dem all
	$(MAKE_CMD) SUITE=taiwan_bc_dem_en all
	$(MAKE_CMD) SUITE=taiwan_bw_en all

.PHONY: exps
exps:
	date +'DS: %H:%M:%S $(shell basename $@)'
	#-make SUITE=taiwan_exp all
	echo No exps target needed

.PHONY: license $(LICENSE)
license: $(LICENSE)
$(LICENSE):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(VERSION)" ]
	mkdir -p $(BUILD_DIR)
	cp -a docs/images $(BUILD_DIR)
	cat docs/beta.md | $(SED_CMD) -e "s|__version__|$(VERSION)|g" | \
		markdown -f +autolink > $(BUILD_DIR)/beta.article
	cat docs/github_flavor.html | $(SED_CMD) "/__article_body__/ r $(BUILD_DIR)/beta.article" > $(BUILD_DIR)/beta.html
	cat docs/local.md | $(SED_CMD) -e "s|__version__|$(VERSION)|g" | \
		markdown -f +autolink > $(BUILD_DIR)/local.article
	cat docs/github_flavor.html | $(SED_CMD) "/__article_body__/ r $(BUILD_DIR)/local.article" > $(BUILD_DIR)/local.html
	cat docs/taiwan_topo.md | $(SED_CMD) -e "s|__version__|$(VERSION)|g" | \
		markdown -f +autolink > $(BUILD_DIR)/taiwan_topo.article
	cat docs/github_flavor.html | $(SED_CMD) "/__article_body__/ r $(BUILD_DIR)/taiwan_topo.article" > $@

.PHONY: gts_all
gts_all: $(GTS_ALL).zip
$(GTS_ALL).zip: $(MAPSFORGE_ZIP) $(GTS_STYLE) $(HGT)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(GTS_ALL)" ]
	rm -rf $(GTS_ALL) $(GTS_ALL).zip
	mkdir -p $(GTS_ALL)
	cd $(GTS_ALL) && \
		unzip $(MAPSFORGE_ZIP) -d map && \
		unzip $(GTS_STYLE) -d mapthemes && \
		unzip $(HGT) -d hgt && \
		$(ZIP_CMD) $(GTS_ALL).zip map/ mapthemes/ hgt/
	rm -rf $(GTS_ALL)

.PHONY: carto_all
carto_all: $(CARTO_ALL).zip
$(CARTO_ALL).zip: $(MAPSFORGE) $(POI) $(BUILD_DIR)/MOI_OSM_Taiwan_TOPO_Rudy_style.zip $(HGT)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(CARTO_ALL)" ]
	unzip $(HGT) -d $(BUILD_DIR)
	cp auto-install/carto/*.cpkg $(BUILD_DIR)/
	cd $(BUILD_DIR) && $(ZIP_CMD) ./carto_map.cpkg $(shell basename $(MAPSFORGE)) $(shell basename $(POI))
	cd $(BUILD_DIR) && $(ZIP_CMD) ./carto_style.cpkg MOI_OSM_Taiwan_TOPO_Rudy_style.zip
	cd $(BUILD_DIR) && $(ZIP_CMD) ./carto_dem.cpkg N2*.hgt
	cd $(BUILD_DIR) && $(ZIP_CMD) carto_upgrade.cpkg $(shell basename $(MAPSFORGE)) $(shell basename $(POI)) MOI_OSM_Taiwan_TOPO_Rudy_style.zip
	cd $(BUILD_DIR) && $(ZIP_CMD) carto_all.cpkg N2*.hgt $(shell basename $(MAPSFORGE)) $(shell basename $(POI)) MOI_OSM_Taiwan_TOPO_Rudy_style.zip

.PHONY: nsis
nsis: $(NSIS)
$(NSIS): $(MAP_PC)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(MAPID)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cd $(MAP_PC_DIR) && \
		rm -rf $@ && \
		for i in $(shell cd $(MAP_PC_DIR); ls $(MAPID)*.img ); do \
			echo '  CopyFiles "$$MyTempDir\'"$${i}"'" "$$INSTDIR\'"$${i}"'"  '; \
			echo '  Delete "$$MyTempDir\'"$${i}"'"  '; \
		done > copy_tiles.txt && \
		for i in $(shell cd $(MAP_PC_DIR); ls $(MAPID)*.img ); do \
			echo '  Delete "$$INSTDIR\'"$${i}"'"  '; \
		done > delete_tiles.txt && \
		cat $(ROOT_DIR)/mkgmaps/makensis.cfg | $(SED_CMD) \
			-e "s|__root_dir__|$(ROOT_DIR)|g" \
			-e "s|__name_word__|$(NAME_WORD)|g" \
			-e "s|__version__|$(VERSION)|g" \
			-e "s|__mapid_lo_hex__|$(MAPID_LO_HEX)|g" \
			-e "s|__mapid_hi_hex__|$(MAPID_HI_HEX)|g" \
			-e "s|__mapid__|$(MAPID)|g" > $(NAME_WORD).nsi && \
		$(SED_CMD) "/__copy_tiles__/ r copy_tiles.txt" -i $(NAME_WORD).nsi && \
		$(SED_CMD) "/__delete_tiles__/ r delete_tiles.txt" -i $(NAME_WORD).nsi && \
		$(ZIP_CMD) "$(NAME_WORD)_InstallFiles.zip" $(MAPID)*.img $(MAPID).TYP $(NAME_WORD){.img,_mdr.img,.tdb,.mdx} && \
		cat $(ROOT_DIR)/docs/nsis-readme.txt | $(SED_CMD) \
			-e "s|__version__|$(VERSION)|g" > readme.txt && \
		cp $(ROOT_DIR)/nsis/{Install.bmp,Deinstall.bmp} . && \
		makensis $(NAME_WORD).nsi && \
		rm "$(NAME_WORD)_InstallFiles.zip"
	mv "$(MAP_PC_DIR)/Install_$(NAME_WORD).exe" $@

.PHONY: poi
poi: $(POI)
$(POI): $(EXTRACT)-sed.osm.pbf
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(EXTRACT)" ]
	mkdir -p $(BUILD_DIR)
	-rm -rf $@
	export JAVACMD_OPTIONS="-server" && \
		sh $(OSMOSIS_CMD) \
			--rb file="$(EXTRACT)-sed.osm.pbf" \
			--poi-writer \
			all-tags=true \
			bbox=$(MAPSFORGE_BBOX) \
			ways=true \
			tag-conf-file="$(POI_MAPPING)" \
			comment="$(VERSION)  /  (c) Map data: OSM contributors" \
			file="$@"

.PHONY: gmap
gmap: $(GMAP)
$(GMAP): $(MAP_PC)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(MAPID)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cd $(MAP_PC_DIR) && \
		rm -rf $@ && \
		cat $(ROOT_DIR)/mkgmaps/jmc_cli.cfg | $(SED_CMD) \
			-e "s|__map_dir__|$(MAP_PC_DIR)|g" \
			-e "s|__name_word__|$(NAME_WORD)|g" \
			-e "s|__mapid__|$(MAPID)|g" > jmc_cli.cfg && \
		$(TOOLS_DIR)/$(JMC_CMD) -v -config="$(MAP_PC_DIR)/jmc_cli.cfg"
	-cd $(MAP_PC_DIR) && [ -d "$(NAME_SHORT).gmap" ] && mv "$(NAME_SHORT).gmap" "$(NAME_WORD).gmap"
	cd $(MAP_PC_DIR) && \
		$(ZIP_CMD) $@ "$(NAME_WORD).gmap"

.PHONY: gmapsupp
gmapsupp: $(GMAPSUPP)
$(GMAPSUPP): $(MAP_HAND)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(MAPID)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cd $(MAP_HAND_DIR) && \
		java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
			--license-file=$(ROOT_DIR)/docs/license.txt \
			--index \
			--gmapsupp \
			--product-id=1 \
			--family-id=$(MAPID) \
			--series-name="$(NAME_WORD)" \
			--family-name="$(NAME_SHORT)" \
			--description="$(NAME_SHORT)" \
			--overview-mapnumber=$(MAPID)0000 \
			--product-version=$(VERSION) \
		$(MAPID)*.img $(MAPID).TYP
	mv $(MAP_HAND_DIR)/gmapsupp.img $@

.PHONY: gmapsupp_zip
gmapsupp_zip: $(GMAPSUPP_ZIP)
$(GMAPSUPP_ZIP): $(GMAPSUPP)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -d "$(BUILD_DIR)" ]
	[ -f "$(GMAPSUPP)" ]
	-rm -rf $@
	cd $(BUILD_DIR) && $(ZIP_CMD) $@ $(shell basename $(GMAPSUPP))

MAPSFORGE_NTL := zh,en
ifeq ($(LANG),zh)
NTL := name,name:zh,name:en
else ifeq ($(LANG),en)
NTL := name:en,name:zh_pinyin
endif

.PHONY: map_hidem
map_hidem: $(MAP_HIDEM)
$(MAP_HIDEM): $(TILES) $(TYP_FILE) $(HR_STYLE_DIR) $(GMAPDEM)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(MAPID)" ]
	rm -rf $(MAP_HIDEM_DIR)
	mkdir -p $(MAP_HIDEM_DIR)
	cd $(MAP_HIDEM_DIR) && \
		cat $(TYP_FILE) | $(SED_CMD) \
			-e "s|ä|a|g" \
			-e "s|é|e|g" \
			-e "s|ß|b|g" \
			-e "s|ü|u|g" \
			-e "s|ö|o|g" \
			-e "s|FID=.*|FID=$(MAPID)|g" \
			-e "s|CodePage=.*|CodePage=$(CODE_PAGE)|g" > $(TYP).txt && \
		java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
			--product-id=1 \
			--family-id=$(MAPID) \
			$(TYP).txt
	cd $(MAP_HIDEM_DIR) && \
		cp $(TYP).typ $(MAPID).TYP && \
		mkdir $(MAP_HIDEM_DIR)/style && \
		cp -a $(HR_STYLE_DIR) $(MAP_HIDEM_DIR)/style/$(HR_STYLE) && \
		cp $(ROOT_DIR)/styles/style-translations $(MAP_HIDEM_DIR)/ && \
		cat $(ROOT_DIR)/mkgmaps/mkgmap.cfg | $(SED_CMD) \
			-e "s|__root_dir__|$(ROOT_DIR)|g" \
			-e "s|__map_dir__|$(MAP_HIDEM_DIR)|g" \
			-e "s|__version__|$(VERSION)|g" \
			-e "s|__style__|$(HR_STYLE)|g" \
			-e "s|__name_tag_list__|$(NTL)|g" \
			-e "s|__code_page__|$(CODE_PAGE)|g" \
			-e "s|__name_long__|$(NAME_LONG)|g" \
			-e "s|__name_short__|$(NAME_SHORT)|g" \
			-e "s|__name_word__|$(NAME_WORD)|g" \
			-e "s|__mapid__|$(MAPID)|g" > mkgmap.cfg && \
		cat $(TILES_DIR)/template.args | $(SED_CMD) \
			-e "s|input-file: \(.*\)|input-file: $(TILES_DIR)/\\1|g" >> mkgmap.cfg && \
		ln -s $(GMAPDEM) ./moi-hgt.zip && \
		$(SED_CMD) "/__dem_section__/ r $(ROOT_DIR)/mkgmaps/gmapdem_camp.cfg" -i mkgmap.cfg && \
		java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
			--max-jobs=$(MKGMAP_JOBS) \
			-c mkgmap.cfg \
			--check-styles
	touch $(MAP_HIDEM)

.PHONY: map_lodem
map_lodem: $(MAP_LODEM)
$(MAP_LODEM): $(TILES) $(TYP_FILE) $(LR_STYLE_DIR) $(GMAPDEM)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(MAPID)" ]
	rm -rf $(MAP_LODEM_DIR)
	mkdir -p $(MAP_LODEM_DIR)
	cd $(MAP_LODEM_DIR) && \
		cat $(TYP_FILE) | $(SED_CMD) \
			-e "s|ä|a|g" \
			-e "s|é|e|g" \
			-e "s|ß|b|g" \
			-e "s|ü|u|g" \
			-e "s|ö|o|g" \
			-e "s|FID=.*|FID=$(MAPID)|g" \
			-e "s|CodePage=.*|CodePage=$(CODE_PAGE)|g" > $(TYP).txt && \
		java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
			--product-id=1 \
			--family-id=$(MAPID) \
			$(TYP).txt
	cd $(MAP_LODEM_DIR) && \
		cp $(TYP).typ $(MAPID).TYP && \
		mkdir $(MAP_LODEM_DIR)/style && \
		cp -a $(LR_STYLE_DIR) $(MAP_LODEM_DIR)/style/$(LR_STYLE) && \
		cp $(ROOT_DIR)/styles/style-translations $(MAP_LODEM_DIR)/ && \
		cat $(ROOT_DIR)/mkgmaps/mkgmap.cfg | $(SED_CMD) \
			-e "s|__root_dir__|$(ROOT_DIR)|g" \
			-e "s|__map_dir__|$(MAP_LODEM_DIR)|g" \
			-e "s|__version__|$(VERSION)|g" \
			-e "s|__style__|$(LR_STYLE)|g" \
			-e "s|__name_tag_list__|$(NTL)|g" \
			-e "s|__code_page__|$(CODE_PAGE)|g" \
			-e "s|__name_long__|$(NAME_LONG)|g" \
			-e "s|__name_short__|$(NAME_SHORT)|g" \
			-e "s|__name_word__|$(NAME_WORD)|g" \
			-e "s|__mapid__|$(MAPID)|g" > mkgmap.cfg && \
		cat $(TILES_DIR)/template.args | $(SED_CMD) \
			-e "s|input-file: \(.*\)|input-file: $(TILES_DIR)/\\1|g" >> mkgmap.cfg && \
		ln -s $(GMAPDEM) ./moi-hgt.zip && \
		$(SED_CMD) "/__dem_section__/ r $(ROOT_DIR)/mkgmaps/gmapdem.cfg" -i mkgmap.cfg && \
		java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
			--max-jobs=$(MKGMAP_JOBS) \
			-c mkgmap.cfg \
			--check-styles
	touch $(MAP_LODEM)

.PHONY: map_nodem_hr
map_nodem_hr: $(MAP_NODEM_HR)
$(MAP_NODEM_HR): $(TILES) $(TYP_FILE) $(HR_STYLE_DIR)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(MAPID)" ]
	rm -rf $(MAP_NODEM_HR_DIR)
	mkdir -p $(MAP_NODEM_HR_DIR)
	cd $(MAP_NODEM_HR_DIR) && \
		cat $(TYP_FILE) | $(SED_CMD) \
			-e "s|ä|a|g" \
			-e "s|é|e|g" \
			-e "s|ß|b|g" \
			-e "s|ü|u|g" \
			-e "s|ö|o|g" \
			-e "s|FID=.*|FID=$(MAPID)|g" \
			-e "s|CodePage=.*|CodePage=$(CODE_PAGE)|g" > $(TYP).txt && \
		java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
			--product-id=1 \
			--family-id=$(MAPID) \
			$(TYP).txt
	cd $(MAP_NODEM_HR_DIR) && \
		cp $(TYP).typ $(MAPID).TYP && \
		mkdir $(MAP_NODEM_HR_DIR)/style && \
		cp -a $(HR_STYLE_DIR) $(MAP_NODEM_HR_DIR)/style/$(HR_STYLE) && \
		cp $(ROOT_DIR)/styles/style-translations $(MAP_NODEM_HR_DIR)/ && \
		cat $(ROOT_DIR)/mkgmaps/mkgmap.cfg | $(SED_CMD) \
			-e "s|__root_dir__|$(ROOT_DIR)|g" \
			-e "s|__map_dir__|$(MAP_NODEM_HR_DIR)|g" \
			-e "s|__version__|$(VERSION)|g" \
			-e "s|__style__|$(HR_STYLE)|g" \
			-e "s|__name_tag_list__|$(NTL)|g" \
			-e "s|__code_page__|$(CODE_PAGE)|g" \
			-e "s|__name_long__|$(NAME_LONG)|g" \
			-e "s|__name_short__|$(NAME_SHORT)|g" \
			-e "s|__name_word__|$(NAME_WORD)|g" \
			-e "s|__mapid__|$(MAPID)|g" > mkgmap.cfg && \
		cat $(TILES_DIR)/template.args | $(SED_CMD) \
			-e "s|input-file: \(.*\)|input-file: $(TILES_DIR)/\\1|g" >> mkgmap.cfg && \
		java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
			--max-jobs=$(MKGMAP_JOBS) \
			-c mkgmap.cfg \
			--check-styles
	touch $(MAP_NODEM_HR)

.PHONY: map_nodem_lr
map_nodem_lr: $(MAP_NODEM_LR)
$(MAP_NODEM_LR): $(TILES) $(TYP_FILE) $(LR_STYLE_DIR)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(MAPID)" ]
	rm -rf $(MAP_NODEM_LR_DIR)
	mkdir -p $(MAP_NODEM_LR_DIR)
	cd $(MAP_NODEM_LR_DIR) && \
		cat $(TYP_FILE) | $(SED_CMD) \
			-e "s|ä|a|g" \
			-e "s|é|e|g" \
			-e "s|ß|b|g" \
			-e "s|ü|u|g" \
			-e "s|ö|o|g" \
			-e "s|FID=.*|FID=$(MAPID)|g" \
			-e "s|CodePage=.*|CodePage=$(CODE_PAGE)|g" > $(TYP).txt && \
		java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
			--product-id=1 \
			--family-id=$(MAPID) \
			$(TYP).txt
	cd $(MAP_NODEM_LR_DIR) && \
		cp $(TYP).typ $(MAPID).TYP && \
		mkdir $(MAP_NODEM_LR_DIR)/style && \
		cp -a $(LR_STYLE_DIR) $(MAP_NODEM_LR_DIR)/style/$(LR_STYLE) && \
		cp $(ROOT_DIR)/styles/style-translations $(MAP_NODEM_LR_DIR)/ && \
		cat $(ROOT_DIR)/mkgmaps/mkgmap.cfg | $(SED_CMD) \
			-e "s|__root_dir__|$(ROOT_DIR)|g" \
			-e "s|__map_dir__|$(MAP_NODEM_LR_DIR)|g" \
			-e "s|__version__|$(VERSION)|g" \
			-e "s|__style__|$(LR_STYLE)|g" \
			-e "s|__name_tag_list__|$(NTL)|g" \
			-e "s|__code_page__|$(CODE_PAGE)|g" \
			-e "s|__name_long__|$(NAME_LONG)|g" \
			-e "s|__name_short__|$(NAME_SHORT)|g" \
			-e "s|__name_word__|$(NAME_WORD)|g" \
			-e "s|__mapid__|$(MAPID)|g" > mkgmap.cfg && \
		cat $(TILES_DIR)/template.args | $(SED_CMD) \
			-e "s|input-file: \(.*\)|input-file: $(TILES_DIR)/\\1|g" >> mkgmap.cfg && \
		java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
			--max-jobs=$(MKGMAP_JOBS) \
			-c mkgmap.cfg \
			--check-styles
	touch $(MAP_NODEM_LR)

.DELETE_ON_ERROR: $(ELEVATION)
ELEVATIONS_URL := http://moi.kcwu.csie.org/osm_elevations
$(ELEVATION):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(ELEVATIONS_DIR)
	cd $(ELEVATIONS_DIR) && \
		curl $(ELEVATIONS_URL)/$(ELEVATION_FILE) -o $(ELEVATION_FILE) && \
		curl $(ELEVATIONS_URL)/$(ELEVATION_FILE).md5 -o $(ELEVATION_FILE).md5 && \
		EXAM_FILE=$@; [ "$$($(MD5_CMD))" == "$$(cat $(ELEVATION_FILE).md5 | cut -d' ' -f1)" ]

.DELETE_ON_ERROR: $(ELEVATION_MIX)
$(ELEVATION_MIX):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(ELEVATIONS_DIR)/marker
	cd $(ELEVATIONS_DIR)/marker && \
		curl $(ELEVATIONS_URL)/$(ELEVATION_MIX_FILE) -o $(ELEVATION_MIX_FILE) && \
		curl $(ELEVATIONS_URL)/$(ELEVATION_MIX_FILE).md5 -o $(ELEVATION_MIX_FILE).md5 && \
		EXAM_FILE=$@; [ "$$($(MD5_CMD))" == "$$(cat $(ELEVATION_MIX_FILE).md5 | cut -d' ' -f1)" ]

.DELETE_ON_ERROR: $(EXTRACT).o5m
EXTRACT_URL := http://osm.kcwu.csie.org/download/tw-extract/recent
$(EXTRACT).o5m:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(EXTRACT_DIR)
	cd $(EXTRACT_DIR) && \
		aria2c -x 5 $(EXTRACT_URL)/$(EXTRACT_FILE).o5m.zst && \
		aria2c -x 5 $(EXTRACT_URL)/$(EXTRACT_FILE).o5m.zst.md5 && \
		EXAM_FILE=$(EXTRACT_FILE).o5m.zst; [ "$$($(MD5_CMD))" == "$$(cat $(EXTRACT_FILE).o5m.zst.md5 | $(SED_CMD) -e 's/^.* = //')" ] && \
		zstd --decompress --rm $(EXTRACT_FILE).o5m.zst

$(EXTRACT)_name.o5m: $(EXTRACT).o5m
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(EXTRACT_DIR)
	-rm -rf $@
	python3 $(ROOT_DIR)/osm_scripts/complete_en.py $(EXTRACT).o5m $(EXTRACT)_name.pbf
	$(OSMCONVERT_CMD) \
		$(EXTRACT)_name.pbf \
		--out-o5m \
		-o=$(EXTRACT)_name.o5m
	-rm -rf $(EXTRACT)_name.pbf

$(EXTRACT)-sed.osm.pbf: $(EXTRACT)_name.o5m osm_scripts/process_osm.sh osm_scripts/process_osm.py
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(EXTRACT_DIR)
	-rm -rf $@
	cd $(EXTRACT_DIR) && $(ROOT_DIR)/osm_scripts/process_osm.sh $(EXTRACT_FILE)_name.o5m $@

# OSMCONVERT_BOUNDING
ifneq (,$(strip $(POLY_FILE)))
ifeq (Taiwan,$(REGION))
OSMCONVERT_BOUNDING :=
else
OSMCONVERT_BOUNDING := -B="$(POLIES_DIR)/$(POLY_FILE)" --complete-ways --complete-multipolygons --complete-boundaries --drop-broken-refs
endif
else
ifneq (,$(strip $(BOUNDING_BOX)))
OSMCONVERT_BOUNDING := -b=$(BOTTOM),$(LEFT),$(TOP),$(RIGHT) --complete-ways --complete-multipolygons --complete-boundaries --drop-broken-refs
MAPSFORGE_BBOX := $(BOTTOM),$(LEFT),$(TOP),$(RIGHT)
endif
endif

$(GMAP_INPUT): $(EXTRACT)_name.o5m $(ELEVATION)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cp $< $@.o5m
	sh $(TOOLS_DIR)/osmium-append.sh $@.o5m $(ELEVATION)
	$(OSMCONVERT_CMD) \
		--drop-version \
		$(OSMCONVERT_BOUNDING) \
		$@.o5m \
		-o=$@
	-rm -f $@.o5m

$(MAPSFORGE_PBF): $(EXTRACT)-sed.osm.pbf $(ELEVATION_MIX)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cp $< $@.pbf
	sh $(TOOLS_DIR)/osmium-append.sh $@.pbf $(ELEVATION_MIX)
	$(OSMCONVERT_CMD) \
		--drop-version \
		$(OSMCONVERT_BOUNDING) \
		$@.pbf \
		-o=$@
	-rm -f $@.pbf


MAPSFORGE_STYLE := $(BUILD_DIR)/MOI_OSM_Taiwan_TOPO_Rudy_style.zip

.PHONY: mapsforge_style $(MAPSFORGE_STYLE)
mapsforge_style: $(MAPSFORGE_STYLE)
$(MAPSFORGE_STYLE):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -f $@
	-rm -rf $(BUILD_DIR)/mapsforge_style
	mkdir -p $(BUILD_DIR)
	cp -a styles/mapsforge_style $(BUILD_DIR)
	cat styles/mapsforge_style/MOI_OSM.xml | \
		$(SED_CMD) -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/mapsforge_style/MOI_OSM.xml
	cd $(BUILD_DIR)/mapsforge_style && $(ZIP_CMD) $@ *


LOCUS_STYLE := $(BUILD_DIR)/MOI_OSM_Taiwan_TOPO_Rudy_locus_style.zip
LOCUS_STYLE_INST := MOI_OSM_Taiwan_TOPO_Rudy_style

.PHONY: locus_style $(LOCUS_STYLE)
locus_style: $(LOCUS_STYLE)
$(LOCUS_STYLE):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -f $@
	-rm -rf $(BUILD_DIR)/$(LOCUS_STYLE_INST)
	mkdir -p $(BUILD_DIR)
	cp -a styles/locus_style $(BUILD_DIR)/$(LOCUS_STYLE_INST)
	cat styles/locus_style/MOI_OSM.xml | \
		$(SED_CMD) -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/$(LOCUS_STYLE_INST)/MOI_OSM.xml
	cd $(BUILD_DIR) && $(ZIP_CMD) $@ $(LOCUS_STYLE_INST)/


LITE_STYLE := $(BUILD_DIR)/MOI_OSM_Taiwan_TOPO_Lite_style.zip

.PHONY: lite_style $(LITE_STYLE)
lite_style: $(LITE_STYLE)
$(LITE_STYLE):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -f $@
	-rm -rf $(BUILD_DIR)/mapsforge_lite
	mkdir -p $(BUILD_DIR)/mapsforge_lite
	cp -a styles/mapsforge_style/License.txt $(BUILD_DIR)/mapsforge_lite
	cp -a styles/mapsforge_style/moiosm_res $(BUILD_DIR)/mapsforge_lite/moiosmlite_res
	cat styles/mapsforge_style/MOI_OSM.xml | \
		$(SED_CMD) \
			-e "s/__version__/$(VERSION)/g" \
			-e "s/file:moiosm_res/file:moiosmlite_res/g" \
			-e "s,file:/moiosm_res,file:/moiosmlite_res,g" \
			-e "s,<!-- hillshading -->,<hillshading />,g" \
			-e "/-- contours-begin --/,/-- contours-end --/d" \
			-e "/-- contours --/ r styles/mapsforge_lite/Lite_contours.part" \
		> $(BUILD_DIR)/mapsforge_lite/MOI_OSM_Lite.xml
	cd $(BUILD_DIR)/mapsforge_lite && \
		$(ZIP_CMD) $@ *


HS_STYLE := $(BUILD_DIR)/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip

.PHONY: hs_style $(HS_STYLE)
hs_style: $(HS_STYLE)
$(HS_STYLE):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -f $@
	-rm -rf $(BUILD_DIR)/mapsforge_hs
	mkdir -p $(BUILD_DIR)/mapsforge_hs
	cp -a styles/mapsforge_style/License.txt $(BUILD_DIR)/mapsforge_hs
	cp -a styles/mapsforge_style/moiosm_res $(BUILD_DIR)/mapsforge_hs/moiosmhs_res
	cat styles/mapsforge_style/MOI_OSM.xml | \
		$(SED_CMD) \
			-e "s/__version__/$(VERSION)/g" \
			-e "s/file:moiosm_res/file:moiosmhs_res/g" \
			-e "s,file:/moiosm_res,file:/moiosmhs_res,g" \
			-e "s,<!-- hillshading -->,<hillshading />,g" \
		> $(BUILD_DIR)/mapsforge_hs/MOI_OSM.xml
	cd $(BUILD_DIR)/mapsforge_hs && \
		$(ZIP_CMD) $@ *


BN_STYLE := $(BUILD_DIR)/MOI_OSM_bn_style.zip

.PHONY: bn_style $(BN_STYLE)
bn_style: $(BN_STYLE)
$(BN_STYLE):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -f $@
	-rm -rf $(BUILD_DIR)/mapsforge_bn
	mkdir -p $(BUILD_DIR)
	cp -a styles/mapsforge_bn $(BUILD_DIR)
	cat styles/mapsforge_bn/MOI_OSM_BN.xml | \
		$(SED_CMD) -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/mapsforge_bn/MOI_OSM_BN.xml
	cd $(BUILD_DIR)/mapsforge_bn && $(ZIP_CMD) $@ *


DN_STYLE := $(BUILD_DIR)/MOI_OSM_dn_style.zip

.PHONY: dn_style $(DN_STYLE)
dn_style: $(DN_STYLE)
$(DN_STYLE):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -f $@
	-rm -rf $(BUILD_DIR)/mapsforge_dn
	mkdir -p $(BUILD_DIR)
	cp -a styles/mapsforge_dn $(BUILD_DIR)
	cat styles/mapsforge_dn/MOI_OSM_DN.xml | \
		$(SED_CMD) -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/mapsforge_dn/MOI_OSM_DN.xml
	cd $(BUILD_DIR)/mapsforge_dn && $(ZIP_CMD) $@ *


EXTRA_STYLE := $(BUILD_DIR)/MOI_OSM_extra_style.zip

.PHONY: extra_style $(EXTRA_STYLE)
extra_style: $(EXTRA_STYLE)
$(EXTRA_STYLE):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -f $@
	-rm -rf $(BUILD_DIR)/extra
	mkdir -p $(BUILD_DIR)
	cp -a styles/extra $(BUILD_DIR)
	cat styles/extra/MOI_OSM_EXTRA.xml | \
		$(SED_CMD) -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/extra/MOI_OSM_EXTRA.xml
	cd $(BUILD_DIR)/extra && $(ZIP_CMD) $@ *


TWMAP_STYLE := $(BUILD_DIR)/MOI_OSM_twmap_style.zip

.PHONY: twmap_style $(TWMAP_STYLE)
twmap_style: $(TWMAP_STYLE)
$(TWMAP_STYLE):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -r $@
	-rm -rf $(BUILD_DIR)/twmap_style
	mkdir -p $(BUILD_DIR)
	cp -a styles/twmap_style $(BUILD_DIR)
	cat styles/twmap_style/MOI_OSM_twmap.xml | \
		$(SED_CMD) -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/twmap_style/MOI_OSM_twmap.xml
	cd $(BUILD_DIR)/twmap_style && $(ZIP_CMD) $@ *


TN_STYLE := $(BUILD_DIR)/MOI_OSM_tn_style.zip

.PHONY: tn_style $(TN_STYLE)
tn_style: $(TN_STYLE)
$(TN_STYLE):
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -f $@
	-rm -rf $(BUILD_DIR)/mapsforge_tn
	mkdir -p $(BUILD_DIR)/mapsforge_tn
	cp -a styles/mapsforge_style/License.txt $(BUILD_DIR)/mapsforge_tn
	cp -a styles/mapsforge_style/moiosm_res $(BUILD_DIR)/mapsforge_tn/tn_res
	cat styles/mapsforge_style/MOI_OSM.xml | \
		$(SED_CMD) \
			-e "s/__version__/$(VERSION)/g" \
			-e "s/file:moiosm_res/file:tn_res/g" \
			-e "s,file:/moiosm_res,file:/tn_res,g" \
			-e 's/outside="#FFFFFF"/outside="#00FFFFFF"/g' \
			-e "s,<!-- hillshading -->,<hillshading />,g" \
			-e "/TN-REMOVED-FROM/,/TN-REMOVED-TO/d" \
			-e "/-- coastlines --/ r styles/mapsforge_tn/coastlines.part" \
			-e 's/id="elmt-landcover" enabled="true"/id="elmt-landcover" enabled="false"/g' \
		> $(BUILD_DIR)/mapsforge_tn/MOI_OSM_TN.xml
	cd $(BUILD_DIR)/mapsforge_tn && \
		$(ZIP_CMD) $@ *


.PHONY: mapsforge_zip
mapsforge_zip: $(MAPSFORGE_ZIP)
$(MAPSFORGE_ZIP): $(MAPSFORGE) $(POI)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -d "$(BUILD_DIR)" ]
	[ -f "$(MAPSFORGE)" ]
	-rm -rf $@
	cd $(BUILD_DIR) && $(ZIP_CMD) $@ $(shell basename $(MAPSFORGE)) $(shell basename $(POI))

.PHONY: poi_zip
poi_zip: $(POI_ZIP)
$(POI_ZIP): $(POI)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -d "$(BUILD_DIR)" ]
	[ -f "$(POI)" ]
	-rm -rf $@
	cd $(BUILD_DIR) && $(ZIP_CMD) $@ $(shell basename $(POI))


GPX_OSM ?= $(BUILD_DIR)/Happyman-gpx.osm
GPX_BASE = $(basename $(GPX_OSM))
TAIWAN_BBOX=21.55682,118.12141,26.44212,122.31377

.PHONY: gpx
gpx: $(GPX_BASE).map
$(GPX_BASE).map: $(GPX_BASE).osm
	[ -f $(GPX_BASE).osm ]
	rm -f $(GPX_BASE)-sed.pbf $(GPX_BASE)-ren.pbf
	python3 osm_scripts/gpx_handler.py $(GPX_BASE).osm $(GPX_BASE)-sed.pbf
	osmium renumber \
		-s 1,1,0 \
		$(GPX_BASE)-sed.pbf \
		-Oo $(GPX_BASE)-ren.pbf
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && \
	sh $(OSMOSIS_CMD) \
		--read-pbf $(GPX_BASE)-ren.pbf \
		--buffer \
		--mapfile-writer \
			type=ram \
			threads=$(MAPWITER_THREADS) \
			bbox=$(TAIWAN_BBOX) \
			preferred-languages="zh,en" \
			tag-conf-file=osm_scripts/gpx-mapping.xml \
			polygon-clipping=true way-clipping=true label-position=true \
			zoom-interval-conf=6,0,6,10,7,11,14,12,21 \
			map-start-zoom=12 \
			comment="$(VERSION) / (c) GPX: $(notdir $(GPX_BASE))" \
			file="$@"


WITH_GPX = $(dir $(GPX_OSM))MOI_OSM_$(basename $(notdir $(GPX_OSM)))

.PHONY: with_gpx
with_gpx: $(WITH_GPX).map
$(WITH_GPX).map: $(MAPSFORGE_PBF) $(TAG_MAPPING) $(GPX_BASE).osm
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	[ -f $(GPX_BASE).osm ]
	mkdir -p $(BUILD_DIR)
	rm -rf $(GPX_BASE)-sed.pbf $(WITH_GPX)-add.pbf
	python3 osm_scripts/gpx_handler.py $(GPX_BASE).osm $(GPX_BASE)-sed.pbf
	cp -a $(MAPSFORGE_PBF) $(WITH_GPX)-add.pbf
	osm_scripts/osium-append.sh $(WITH_GPX)-add.pbf $(GPX_BASE)-sed.pbf
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && \
		sh $(OSMOSIS_CMD) \
			--read-pbf "$(WITH_GPX)-add.pbf" \
			--buffer \
			--mapfile-writer \
				type=ram \
				threads=$(MAPWITER_THREADS) \
				bbox=$(MAPSFORGE_BBOX) \
				preferred-languages="$(MAPSFORGE_NTL)" \
				tag-conf-file="$(TAG_MAPPING)" \
				polygon-clipping=true way-clipping=true label-position=true \
				zoom-interval-conf=6,0,6,10,7,11,14,12,21 \
				map-start-zoom=12 \
				comment="$(VERSION)  /  (c) Map: Rudy; Map data: OSM contributors; DEM data: Taiwan MOI; GPX: $(notdir $(WITH_GPX))" \
				file="$@" > /dev/null 2> /dev/null


GPX_MAPSFORGE ?= $(BUILD_DIR)/Happyman-wptgpx.map

.PHONY: gpx-2
gpx-2: $(GPX_MAPSFORGE)
$(GPX_MAPSFORGE): $(BUILD_DIR)/track.pbf $(BUILD_DIR)/waypoint.pbf
	rm -f $(BUILD_DIR)/track-sed.pbf $(BUILD_DIR)/waypoint-sed.pbf
	python3 osm_scripts/gpx_handler.py $(BUILD_DIR)/track.pbf $(BUILD_DIR)/track-sed.pbf
	python3 osm_scripts/gpx_handler.py $(BUILD_DIR)/waypoint.pbf $(BUILD_DIR)/waypoint-sed.pbf
	osmium renumber \
		-s 1,1,0 \
		$(BUILD_DIR)/track-sed.pbf \
		-Oo $(@:.map=.pbf)
	osm_scripts/osium-append.sh $(@:.map=.pbf) $(BUILD_DIR)/waypoint-sed.pbf
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && \
	sh $(OSMOSIS_CMD) \
		--read-pbf $(@:.map=.pbf) \
		--buffer \
		--mapfile-writer \
			type=ram \
			threads=$(MAPWITER_THREADS) \
			bbox=$(TAIWAN_BBOX) \
			preferred-languages="zh,en" \
			tag-conf-file=osm_scripts/gpx-mapping.xml \
			polygon-clipping=true way-clipping=true label-position=true \
			zoom-interval-conf=6,0,6,10,7,11,14,12,21 \
			map-start-zoom=12 \
			comment="$(VERSION) / (c) Map: Happyman" \
			file="$@"

.PHONY: mapsforge
mapsforge: $(MAPSFORGE)
$(MAPSFORGE): $(MAPSFORGE_PBF) $(TAG_MAPPING)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(BUILD_DIR)
	mkdir -p $(HOME)/log
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && \
		sh $(OSMOSIS_CMD) \
			--read-pbf "$(MAPSFORGE_PBF)" \
			--buffer \
			--mapfile-writer \
				type=ram \
				threads=$(MAPWITER_THREADS) \
				bbox=$(MAPSFORGE_BBOX) \
				preferred-languages="$(MAPSFORGE_NTL)" \
				tag-conf-file="$(TAG_MAPPING)" \
				polygon-clipping=true way-clipping=true label-position=true \
				zoom-interval-conf=6,0,6,10,7,11,14,12,21 \
				map-start-zoom=12 \
				comment="$(VERSION)  /  (c) Map: Rudy; Map data: OSM contributors; DEM data: Taiwan MOI" \
				file="$@"
	
$(COMMON_TILES): $(GMAP_INPUT)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(MAPID)" ]
	rm -rf $(COMMON_TILES_DIR)
	mkdir -p $(COMMON_TILES_DIR)
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && cd $(COMMON_TILES_DIR) && \
		java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/splitter/splitter.jar \
			--max-threads=$(SPLITTER_THREADS) \
			--geonames-file=$(CITY) \
			--no-trim \
			--precomp-sea=$(SEA_DIR) \
			--keep-complete=true \
			--mapid=$(DUMMYID)0001 \
			--max-areas=4096 \
			--max-nodes=800000 \
			--search-limit=1000000000 \
			--output=o5m \
			--output-dir=$(COMMON_TILES_DIR) \
			$(GMAP_INPUT)
	touch $@

$(TILES): $(COMMON_TILES)
	date +'DS: %H:%M:%S $(shell basename $@)'
	rm -rf $(TILES_DIR)
	mkdir -p $(TILES_DIR)
	cd $(TILES_DIR) && \
		for p in $(COMMON_TILES_DIR)/*.o5m; do \
			ln -s $$p $$(basename $$p | $(SED_CMD) -e 's/^$(DUMMYID)/$(MAPID)/'); \
		done && \
		cat $(COMMON_TILES_DIR)/template.args | $(SED_CMD) \
			-e 's/mapname: $(DUMMYID)/mapname: $(MAPID)/' \
			-e 's/input-file: $(DUMMYID)/input-file: $(MAPID)/' \
			> template.args
	touch $@
