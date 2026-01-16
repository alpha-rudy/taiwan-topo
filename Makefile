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
JAVACMD_OPTIONS ?= -Xmx68G -server -Dfile.encoding=UTF-8

# directory variables
ROOT_DIR := $(shell pwd)
TOOLS_DIR := $(ROOT_DIR)/tools
OSMOSIS_POI_V2_CMD := $(TOOLS_DIR)/osmosis-0.48.3-poiv2/bin/osmosis
OSMOSIS_CMD := $(TOOLS_DIR)/osmosis-0.49.2/bin/osmosis
ifeq ($(shell uname),Darwin)
OSMCONVERT_CMD := $(TOOLS_DIR)/osmconvert-0.8.11/osx/osmconvert
else
OSMCONVERT_CMD := $(TOOLS_DIR)/osmconvert-0.8.11/linux/osmconvert64
endif
MKGMAP_JAR := $(TOOLS_DIR)/mkgmap-r4923/mkgmap.jar
SPLITTER_JAR := $(TOOLS_DIR)/splitter-r654/splitter.jar
LOCUS_POI_CONVERTER := python3 $(TOOLS_DIR)/poi_converter-0.6.1/poiconverter.py
SEA_DIR := $(ROOT_DIR)/sea-20220816001514
BOUNDS_DIR := $(ROOT_DIR)/bounds-20220826
CITIES_DIR := $(ROOT_DIR)/cities
POLIES_DIR := $(ROOT_DIR)/polies
BUILD_DIR ?= $(ROOT_DIR)/build
INSTALL_DIR ?= $(ROOT_DIR)/install
DOWNLOAD_DIR ?= $(ROOT_DIR)/download
ELEVATIONS_DIR := $(DOWNLOAD_DIR)/osm_elevations
EXTRACT_DIR := $(DOWNLOAD_DIR)/extracts
META := $(EXTRACT_DIR)/meta.osm


# Include suite definitions from external files
# Each suite is defined in its own .mk file under suites/<region>/
include $(wildcard $(ROOT_DIR)/suites/taiwan/*.mk)
include $(wildcard $(ROOT_DIR)/suites/taipei/*.mk)
include $(wildcard $(ROOT_DIR)/suites/yushan/*.mk)
include $(wildcard $(ROOT_DIR)/suites/beibeiji/*.mk)
include $(wildcard $(ROOT_DIR)/suites/sheipa/*.mk)
include $(wildcard $(ROOT_DIR)/suites/fujisan/*.mk)
include $(wildcard $(ROOT_DIR)/suites/kumano/*.mk)
include $(wildcard $(ROOT_DIR)/suites/annapurna/*.mk)
include $(wildcard $(ROOT_DIR)/suites/kashmir/*.mk)
include $(wildcard $(ROOT_DIR)/suites/kyushu/*.mk)
include $(wildcard $(ROOT_DIR)/suites/bbox/*.mk)

# Include reusable build macros
include $(ROOT_DIR)/macros.mk

# auto variables
VERSION := $(shell date +%Y.%m.%d)
MAPID_LO_HEX := $(shell printf '%x' $(MAPID) | cut -c3-4)
MAPID_HI_HEX := $(shell printf '%x' $(MAPID) | cut -c1-2)
DUMMYID = 9999

ifeq ($(LANG),zh)
NAME_LONG ?= $(DEM_NAME).OSM.$(STYLE_NAME) - $(REGION) TOPO v$(VERSION)
NAME_SHORT ?= $(DEM_NAME).OSM.$(STYLE_NAME) - $(REGION) TOPO v$(VERSION)
NAME_WORD ?= $(DEM_NAME)_$(REGION)_TOPO_$(STYLE_NAME)
else
NAME_LONG ?= $(DEM_NAME).OSM.$(STYLE_NAME).$(LANG) - $(REGION) v$(VERSION)
NAME_SHORT ?= $(DEM_NAME).OSM.$(STYLE_NAME).$(LANG) - $(REGION) v$(VERSION)
NAME_WORD ?= $(DEM_NAME)_$(REGION)_TOPO_$(STYLE_NAME)_$(LANG)
endif

COMMON_TILES_DIR := $(BUILD_DIR)/$(REGION)/tiles
TILES_DIR := $(BUILD_DIR)/$(REGION)/tiles-$(MAPID)
MAP_DIR := $(BUILD_DIR)/$(REGION)/$(NAME_WORD)
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
REGION_EXTRACT := $(BUILD_DIR)/latest-$(REGION)
POI_EXTRACT := $(REGION_EXTRACT)-poi
CITY := $(CITIES_DIR)/TW.zip
COMMON_TILES := $(COMMON_TILES_DIR)/.COMMON_TILES.done
TILES := $(TILES_DIR)/.TILES.done
GMAP_INPUT := $(BUILD_DIR)/$(REGION).o5m
TYP_FILE := $(ROOT_DIR)/TYPs/$(TYP).txt
HR_STYLE_DIR := $(ROOT_DIR)/styles/$(HR_STYLE)
LR_STYLE_DIR := $(ROOT_DIR)/styles/$(LR_STYLE)
TAG_MAPPING := $(ROOT_DIR)/osm_scripts/tag-mapping.xml
POI_V2_MAPPING := $(ROOT_DIR)/osm_scripts/poi-mapping-v2.xml
POI_MAPPING := $(ROOT_DIR)/osm_scripts/poi-mapping-v2.xml
ADDR_MAPPING := $(ROOT_DIR)/osm_scripts/poi-addr-mapping.xml

DEM_FIX := $(shell echo $(DEM_NAME) | tr A-Z a-z)

GMAPSUPP := $(BUILD_DIR)/gmapsupp_$(REGION)_$(DEM_FIX)_$(LANG)_$(STYLE_NAME).img
GMAPSUPP_ZIP := $(GMAPSUPP).zip
GMAP := $(BUILD_DIR)/$(REGION)_$(DEM_FIX)_$(LANG)_$(STYLE_NAME).gmap.zip
NSIS := $(BUILD_DIR)/Install_$(NAME_WORD).exe
POI_V2 := $(BUILD_DIR)/$(NAME_MAPSFORGE)_v2.poi
POI := $(BUILD_DIR)/$(NAME_MAPSFORGE).poi
ADDR := $(BUILD_DIR)/$(NAME_MAPSFORGE)-addr.poi
POI_ZIP := $(POI).zip
POI_V2_ZIP := $(POI_V2).zip
ADDR_ZIP := $(ADDR).zip
LOCUS_POI := $(BUILD_DIR)/$(NAME_MAPSFORGE).db
LOCUS_POI_ZIP := $(BUILD_DIR)/$(NAME_MAPSFORGE).db.zip
MAPSFORGE := $(BUILD_DIR)/$(NAME_MAPSFORGE).map
MAPSFORGE_ZIP := $(MAPSFORGE).zip
MAPSFORGE_PBF := $(BUILD_DIR)/$(NAME_MAPSFORGE)_zls.osm.pbf
ADS_OSM := $(ROOT_DIR)/precompiled/NPA_Taiwan_ADShelter-ren.pbf
LICENSE := $(BUILD_DIR)/taiwan_topo.html

GTS_ALL ?= $(BUILD_DIR)/gts-no_defined
CARTO_ALL ?= $(BUILD_DIR)/carto-no_defined
LOCUS_MAP ?= $(BUILD_DIR)/locus-no_defined

GTS_ALL := $(BUILD_DIR)/$(NAME_MAPSFORGE)
CARTO_ALL := $(BUILD_DIR)/carto_all
LOCUS_MAP := $(BUILD_DIR)/$(NAME_MAPSFORGE)_locus

ifeq ($(shell uname),Darwin)
MD5_CMD := md5 -q $$EXAM_FILE
JMC_CMD := jmc-0.8/macos/jmc_cli
SED_CMD := gsed
else
MD5_CMD := md5sum $$EXAM_FILE | cut -d' ' -f1
JMC_CMD := jmc-0.8/linux/jmc_cli
SED_CMD := sed
endif

# BOUNDING settings
ifneq (,$(strip $(POLY_FILE)))
OSMCONVERT_BOUNDING := -B=$(POLIES_DIR)/$(POLY_FILE) --complete-ways --complete-multipolygons --complete-boundaries --drop-broken-refs
OSMIUM_BOUNDING := --polygon $(POLIES_DIR)/$(POLY_FILE)
OSMOSIS_BOUNDING := --bounding-polygon file=$(POLIES_DIR)/$(POLY_FILE) completeWays=yes completeRelations=yes clipIncompleteEntities=false
else ifneq (,$(strip $(BOUNDING_BOX)))
OSMCONVERT_BOUNDING := -b=$(LEFT),$(BOTTOM),$(RIGHT),$(TOP) --complete-ways --complete-multipolygons --complete-boundaries --drop-broken-refs
OSMIUM_BOUNDING := --bbox $(LEFT),$(BOTTOM),$(RIGHT),$(TOP)
OSMOSIS_BOUNDING := --bounding-box left=$(LEFT) bottom=$(BOTTOM) right=$(RIGHT) top=$(TOP) completeWays=yes completeRelations=yes clipIncompleteEntities=false
endif

ZIP_CMD := 7z a -tzip -mx=6
UNZIP_CMD := unzip -o
MAKE_CMD := make

all: $(TARGETS)

clean:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(EXTRACT_DIR)" ]
	-rm -rf $(INSTALL_DIR)/
	-rm -rf $(BUILD_DIR)

.PHONY: distclean-elevations
distclean-elevations:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -rf $(INSTALL_DIR)/
	-rm -rf $(BUILD_DIR)
	-rm -rf $(ELEVATIONS_DIR)

.PHONY: distclean-extracts
distclean-extracts:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -rf $(INSTALL_DIR)/
	-rm -rf $(BUILD_DIR)
	-rm -rf $(EXTRACT_DIR)

.PHONY: distclean
distclean:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(BUILD_DIR)" ]
	-rm -rf $(INSTALL_DIR)/
	-rm -rf $(BUILD_DIR)
	-rm -rf $(DOWNLOAD_DIR)

.PHONY: install
install:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(INSTALL_DIR)" ] && [ -d "$(BUILD_DIR)" ] && [ -n "$(REGION)" ] && [ -n "$(SUITE)" ] && [ -n "$(VERSION)" ]
	rm -rf $(INSTALL_DIR)
	mkdir -p $(INSTALL_DIR)
	cp -r docs/images auto-install/locus/$(REGION)/*.xml $(INSTALL_DIR)
	[ -f docs/$(REGION)/$(SUITE)_topo.md ] && \
		cat docs/$(REGION)/$(SUITE)_topo.md | $(SED_CMD) -e "s|__version__|$(VERSION)|g" | \
		markdown -f +autolink > $(BUILD_DIR)/$(SUITE)_topo.article && \
		cat docs/github_flavor.html | $(SED_CMD) "/__article_body__/ r $(BUILD_DIR)/$(SUITE)_topo.article" > $(INSTALL_DIR)/$(SUITE)_topo.html
	-[ -f docs/$(REGION)/index.json ] && \
		cat docs/$(REGION)/index.json | $(SED_CMD) -e "s|__version__|$(VERSION)|g" > $(INSTALL_DIR)/index.json
	-[ -f docs/$(REGION)/beta.md ] && \
		cat docs/$(REGION)/beta.md | $(SED_CMD) -e "s|__version__|$(VERSION)|g" | \
		markdown -f +autolink > $(BUILD_DIR)/beta.article && \
		cat docs/github_flavor.html | $(SED_CMD) "/__article_body__/ r $(BUILD_DIR)/beta.article" > $(INSTALL_DIR)/beta.html
	-[ -f docs/$(REGION)/local.md ] && \
		cat docs/$(REGION)/local.md | $(SED_CMD) -e "s|__version__|$(VERSION)|g" | \
		markdown -f +autolink > $(BUILD_DIR)/local.article && \
		cat docs/github_flavor.html | $(SED_CMD) "/__article_body__/ r $(BUILD_DIR)/local.article" > $(BUILD_DIR)/local.html
	-[ -d docs/$(REGION)/gts ] && cp -r docs/$(REGION)/gts $(INSTALL_DIR) && \
		cat docs/$(REGION)/gts/index.html | $(SED_CMD) -e "s|__version__|$(VERSION)|g" > $(INSTALL_DIR)/gts/index.html
	cp -r $(BUILD_DIR)/{*.zip,*.exe} $(INSTALL_DIR)
	-cp -r $(BUILD_DIR)/*.cpkg $(INSTALL_DIR)
	cd $(INSTALL_DIR) && md5sum *.zip *.exe *.html *.xml > md5sum.txt

.PHONY: exps
exps:
	date +'DS: %H:%M:%S $(shell basename $@)'
	#-make SUITE=taiwan_exp all
	echo No exps target needed

# Alias for Taiwan suites
.PHONY: suites
suites: taiwan_suites

.PHONY: daily
daily:
	$(MAKE_CMD) BUILD_DIR=$(ROOT_DIR)/build-taiwan styles
	$(MAKE_CMD) BUILD_DIR=$(ROOT_DIR)/build-taiwan SUITE=taiwan mapsforge_zip poi_zip poi_v2_zip locus_poi_zip
	$(MAKE_CMD) BUILD_DIR=$(ROOT_DIR)/build-taiwan SUITE=taiwan_bc_dem gmap nsis
	$(MAKE_CMD) BUILD_DIR=$(ROOT_DIR)/build-taiwan INSTALL_DIR=$(INSTALL_DIR) SUITE=taiwan install

.PHONY: styles
styles:
	$(MAKE_CMD) mapsforge_style lite_style hs_style locus_style twmap_style bn_style dn_style tn_style extra_style

.PHONY: gts_all
gts_all: $(GTS_ALL).zip
$(GTS_ALL).zip: $(MAPSFORGE_ZIP) $(GTS_STYLE) $(HGT)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(GTS_ALL)" ]
	rm -rf $(GTS_ALL) $(GTS_ALL).zip
	mkdir -p $(GTS_ALL)
	cd $(GTS_ALL) && \
		$(UNZIP_CMD) $(MAPSFORGE_ZIP) -d map && \
		$(UNZIP_CMD) $(GTS_STYLE) -d mapthemes && \
		$(UNZIP_CMD) $(HGT) -d hgt && \
		$(ZIP_CMD) $(GTS_ALL).zip map/ mapthemes/ hgt/
	rm -rf $(GTS_ALL)

.PHONY: carto_all
carto_all: $(CARTO_ALL).zip
$(CARTO_ALL).zip: $(MAPSFORGE) $(POI_V2) $(POI) $(HS_STYLE) $(HGT)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(CARTO_ALL)" ]
	mv $(POI) $(POI).bak && cp $(POI_V2) $(POI)
	$(UNZIP_CMD) $(HGT) -d $(BUILD_DIR)
	cp auto-install/carto/$(REGION)/*.cpkg $(BUILD_DIR)/
	cd $(BUILD_DIR) && $(ZIP_CMD) ./$(NAME_CARTO)_map.cpkg $(shell basename $(MAPSFORGE)) $(shell basename $(POI))
	cd $(BUILD_DIR) && $(ZIP_CMD) ./$(NAME_CARTO)_style.cpkg $(shell basename $(HS_STYLE))
	cd $(BUILD_DIR) && $(ZIP_CMD) ./$(NAME_CARTO)_dem.cpkg N*.hgt
	cd $(BUILD_DIR) && $(ZIP_CMD) ./$(NAME_CARTO)_upgrade.cpkg $(shell basename $(MAPSFORGE)) $(shell basename $(POI)) $(shell basename $(HS_STYLE))
	cd $(BUILD_DIR) && $(ZIP_CMD) ./$(NAME_CARTO)_all.cpkg N*.hgt $(shell basename $(MAPSFORGE)) $(shell basename $(POI)) $(shell basename $(HS_STYLE))
	mv $(POI).bak $(POI)

.PHONY: locus_map
locus_map: $(LOCUS_MAP).zip
$(LOCUS_MAP).zip: $(MAPSFORGE) $(LOCUS_POI) 
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(LOCUS_MAP)" ]
	@rm -rf $(LOCUS_MAP) $(LOCUS_MAP).zip
	mkdir -p $(LOCUS_MAP)
	cp $(MAPSFORGE) $(LOCUS_MAP)/$(shell basename $(MAPSFORGE:%.map=%.osm.map))
	cp $(LOCUS_POI) $(LOCUS_MAP)/$(shell basename $(LOCUS_POI:%.db=%.osm.db))
	cd $(LOCUS_MAP) && $(ZIP_CMD) $(LOCUS_MAP).zip *

.PHONY: nsis
nsis: $(NSIS)
$(NSIS): $(MAP_PC)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(MAPID)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	$(TOOLS_DIR)/nsis-build.sh "$(MAP_PC_DIR)" "$(MAPID)" "$(NAME_WORD)" "$(VERSION)" "$(MAPID_LO_HEX)" "$(MAPID_HI_HEX)" "$(ROOT_DIR)" "$@"

.PHONY: poi_extract
poi_extract: $(POI_EXTRACT).osm.pbf
$(POI_EXTRACT).osm.pbf: $(REGION_EXTRACT)-sed.osm.pbf
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION_EXTRACT)" ]
	[ -n "$(OSMIUM_BOUNDING)" ]
	mkdir -p $(dir $@)
	-rm -rf $@
	osmium extract $(OSMIUM_BOUNDING) --strategy=smart \
		$< -o $@ --overwrite

#==============================================================================
# POI Build Target Instantiations
#==============================================================================
# Using the POI_BUILD macro to create POI database targets.
# Parameters: target, output, input, deps, mapping, osmosis_cmd, extra_opts, java_env

# poi: Standard POI database with bounding
$(eval $(call POI_BUILD,poi,$(POI),$(POI_EXTRACT).osm.pbf,$(POI_EXTRACT).osm.pbf $(POI_MAPPING),$(POI_MAPPING),$(OSMOSIS_CMD),$(OSMOSIS_BOUNDING),))

# poi_v2: POI v2 database using Java 8 osmosis
$(eval $(call POI_BUILD,poi_v2,$(POI_V2),$(POI_EXTRACT).osm.pbf,$(POI_EXTRACT).osm.pbf $(POI_V2_MAPPING),$(POI_V2_MAPPING),$(OSMOSIS_POI_V2_CMD),,JAVA_HOME=$(JAVA8_HOME) PATH=$(JAVA8_HOME)/bin:$$$$PATH))

# addr: Address POI database from sed-processed extract using Java 8 osmosis
$(eval $(call POI_BUILD,addr,$(ADDR),$(REGION_EXTRACT)-sed.osm.pbf,$(REGION_EXTRACT)-sed.osm.pbf $(ADDR_MAPPING),$(ADDR_MAPPING),$(OSMOSIS_POI_V2_CMD),,JAVA_HOME=$(JAVA8_HOME) PATH=$(JAVA8_HOME)/bin:$$$$PATH))

.PHONY: locus_poi
locus_poi: $(LOCUS_POI)
$(LOCUS_POI): $(POI_V2)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(EXTRACT)" ]
	mkdir -p $(BUILD_DIR)
	-rm -rf $@
	$(LOCUS_POI_CONVERTER) -if poi -om create '$<' '$@'

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
		java $(JAVACMD_OPTIONS) -jar $(MKGMAP_JAR) \
			--code-page=$(CODE_PAGE) \
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

MAPSFORGE_NTL := $(LANG),en
ifeq ($(LANG),en)
NTL := name:en,name:zh_pinyin
else
NTL := name,name:$(LANG),name:en
endif

#==============================================================================
# Map Build Target Instantiations
#==============================================================================
# Using the MAP_BUILD macro to create map generation targets.
# Parameters: target_name, done_file, output_dir, style_dir, style_name, dem_config, extra_deps

# map_hidem: High-resolution map with DEM (camping config)
$(eval $(call MAP_BUILD,map_hidem,$(MAP_HIDEM),$(MAP_HIDEM_DIR),$(HR_STYLE_DIR),$(HR_STYLE),gmapdem_camp.cfg,$(GMAPDEM)))

# map_lodem: Low-resolution map with DEM (standard config)
$(eval $(call MAP_BUILD,map_lodem,$(MAP_LODEM),$(MAP_LODEM_DIR),$(LR_STYLE_DIR),$(LR_STYLE),gmapdem.cfg,$(GMAPDEM)))

# map_nodem_hr: High-resolution map without DEM
$(eval $(call MAP_BUILD,map_nodem_hr,$(MAP_NODEM_HR),$(MAP_NODEM_HR_DIR),$(HR_STYLE_DIR),$(HR_STYLE),,))

# map_nodem_lr: Low-resolution map without DEM
$(eval $(call MAP_BUILD,map_nodem_lr,$(MAP_NODEM_LR),$(MAP_NODEM_LR_DIR),$(LR_STYLE_DIR),$(LR_STYLE),,))

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
# Determine EXTRACT_URL and download method based on the EXTRACT_FILE
ifeq ($(EXTRACT_FILE),taiwan-latest)
EXTRACT_URL := http://osm.kcwu.csie.org/download/tw-extract/recent
$(EXTRACT).o5m:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(dir $@)
	cd $(EXTRACT_DIR) && \
		aria2c -x 5 $(EXTRACT_URL)/$(EXTRACT_FILE).o5m.zst && \
		aria2c -x 5 $(EXTRACT_URL)/$(EXTRACT_FILE).o5m.zst.md5 && \
		EXAM_FILE=$(EXTRACT_FILE).o5m.zst; [ "$$($(MD5_CMD))" == "$$(cat $(EXTRACT_FILE).o5m.zst.md5 | $(SED_CMD) -e 's/^.* = //')" ] && \
		zstd --decompress --rm $(EXTRACT_FILE).o5m.zst
else
EXTRACT_URL := https://download.geofabrik.de/asia
$(EXTRACT).o5m:
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(dir $@)
	cd $(EXTRACT_DIR) && \
		aria2c -x 5 -o $(EXTRACT_FILE).osm.pbf $(EXTRACT_URL)/$(EXTRACT_FILE).osm.pbf && \
		aria2c -x 5 -o $(EXTRACT_FILE).osm.pbf.md5 $(EXTRACT_URL)/$(EXTRACT_FILE).osm.pbf.md5 && \
		md5sum -c $(EXTRACT_FILE).osm.pbf.md5 && \
		$(OSMCONVERT_CMD) $(EXTRACT_FILE).osm.pbf -o=$(EXTRACT_FILE).o5m
endif

# .DELETE_ON_ERROR: $(EXTRACT).o5m $(EXTRACT).osm.pbf
# EXTRACT_URL := https://download.geofabrik.de/asia
# $(EXTRACT).o5m:
# 	date +'DS: %H:%M:%S $(shell basename $@)'
# 	[ -n "$(REGION)" ]
# 	mkdir -p $(dir $@)
# 	cd $(EXTRACT_DIR) && \
# 	    wget $(EXTRACT_URL)/$(EXTRACT_FILE).osm.pbf.md5 && \
# 		wget $(EXTRACT_URL)/$(EXTRACT_FILE).osm.pbf && \
# 		md5sum -c $(EXTRACT_FILE).osm.pbf.md5 && \
# 		$(OSMCONVERT_CMD) $(EXTRACT_FILE).osm.pbf -o=$(EXTRACT).o5m

$(EXTRACT)_extra.o5m: $(EXTRACT).o5m $(ADS_OSM)
	date +'DS: %H:%M:%S $(shell basename $@)'
ifeq ($(EXTRACT_FILE),taiwan-latest)
	cp $< $@
	bash $(TOOLS_DIR)/osmium-append.sh $@ $(ADS_OSM)
	bash $(TOOLS_DIR)/osmium-append.sh $@ $(ROOT_DIR)/precompiled/TFRI_Taiwan_GiantTree-ren.osm
else
	$(OSMCONVERT_CMD) \
		$< \
		--modify-tags="natural=peak man_made=summit_board" \
		--out-o5m \
		-o=$@
endif

$(REGION_EXTRACT).o5m: $(EXTRACT)_extra.o5m
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(dir $@)
	-rm -rf $@
	$(OSMCONVERT_CMD) \
		--drop-version \
		$(OSMCONVERT_BOUNDING) \
		$< \
		-o=$@

$(REGION_EXTRACT)_name.o5m: $(REGION_EXTRACT).o5m
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(dir $@)
	-rm -rf $@
	LANG_CODE=$(LANG) python3 $(ROOT_DIR)/osm_scripts/complete_en.py $< $(REGION_EXTRACT)_name.pbf
	$(OSMCONVERT_CMD) \
		$(REGION_EXTRACT)_name.pbf \
		--out-o5m \
		-o=$(REGION_EXTRACT)_name.o5m
	-rm -f $(REGION_EXTRACT)_name.pbf

.PHONY: sed
sed: $(REGION_EXTRACT)-sed.osm.pbf
$(REGION_EXTRACT)-sed.osm.pbf: $(REGION_EXTRACT)_name.o5m osm_scripts/process_osm.sh osm_scripts/process_osm.py
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	mkdir -p $(dir $@)
	-rm -rf $@
	cd $(EXTRACT_DIR) && \
	  OSMCONVERT_CMD=$(OSMCONVERT_CMD) $(ROOT_DIR)/osm_scripts/process_osm.sh $< $@

.PHONY: meta
meta: $(META)
$(META): meta/meta.osm
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(VERSION)" ]
	mkdir -p $(dir $@)
	-rm -rf $@
	cd $(EXTRACT_DIR) && cat $(ROOT_DIR)/meta/meta.osm | $(SED_CMD) -e "s/__version__/$(VERSION)/g" > $@

$(GMAP_INPUT): $(REGION_EXTRACT)_name.o5m $(ELEVATION)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	-rm -rf $@
	$(TOOLS_DIR)/gmap-input-build.sh "$(REGION_EXTRACT)_name" "$(ELEVATION)" "$(OSMCONVERT_CMD)" "$(OSMCONVERT_BOUNDING)" "$(BUILD_DIR)" "$@"

$(MAPSFORGE_PBF): $(REGION_EXTRACT)-sed.osm.pbf $(META) $(ELEVATION_MIX) $(ADS_OSM)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	-rm -rf $@
	$(TOOLS_DIR)/mapsforge-pbf-build.sh "$<" "$(META)" "$(ELEVATION_MIX)" "$(OSMCONVERT_CMD)" "$(OSMCONVERT_BOUNDING)" "$(BUILD_DIR)" "$@"


#==============================================================================
# Style Target Instantiations
#==============================================================================
# Using the style macros defined above to create style build targets.
# Each $(eval $(call ...)) instantiates a style target with the given parameters.

# mapsforge_style: Main mapsforge style with documentation
$(eval $(call STYLE_WITH_DOCS,mapsforge_style,MOI_OSM_Taiwan_TOPO_Rudy_style,styles/mapsforge_style,mapsforge_style,MOI_OSM.xml,MOI_OSM.pdf,MOI_OSM.png))
MAPSFORGE_STYLE := $(mapsforge_style_VAR)

# locus_style: Locus-specific style packaging
$(eval $(call STYLE_LOCUS,locus_style,MOI_OSM_Taiwan_TOPO_Rudy_locus_style,styles/locus_style,MOI_OSM_Taiwan_TOPO_Rudy_style,MOI_OSM.xml,MOI_OSM.pdf,MOI_OSM.png))
LOCUS_STYLE := $(locus_style_VAR)
LOCUS_STYLE_INST := MOI_OSM_Taiwan_TOPO_Rudy_style

# lite_style: Lite version with hillshading enabled and simplified contours
# This has custom sed transformations that don't fit the standard macro
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
			-e "/-- contours-body --/ r styles/mapsforge_lite/Lite_contours.part" \
		> $(BUILD_DIR)/mapsforge_lite/MOI_OSM_Lite.xml
	cp docs/legend_V1R3.pdf $(BUILD_DIR)/mapsforge_lite/MOI_OSM_Lite.pdf
	cd $(BUILD_DIR)/mapsforge_lite && \
		$(ZIP_CMD) $@ *

# hs_style: Hillshading-enabled style variant
$(eval $(call STYLE_TRANSFORM,hs_style,MOI_OSM_Taiwan_TOPO_Rudy_hs_style,mapsforge_hs,moiosmhs_res,MOI_OSM.xml,-e "s$$(COMMA)<!-- hillshading -->$$(COMMA)<hillshading />$$(COMMA)g",MOI_OSM.pdf,MOI_OSM.png))
HS_STYLE := $(hs_style_VAR)

# bn_style: Basic night style
$(eval $(call STYLE_SIMPLE,bn_style,MOI_OSM_bn_style,styles/mapsforge_bn,mapsforge_bn,MOI_OSM_BN.xml))
BN_STYLE := $(bn_style_VAR)

# dn_style: Dark night style
$(eval $(call STYLE_SIMPLE,dn_style,MOI_OSM_dn_style,styles/mapsforge_dn,mapsforge_dn,MOI_OSM_DN.xml))
DN_STYLE := $(dn_style_VAR)

# extra_style: Extra style variant
$(eval $(call STYLE_SIMPLE,extra_style,MOI_OSM_extra_style,styles/extra,extra,MOI_OSM_EXTRA.xml))
EXTRA_STYLE := $(extra_style_VAR)

# twmap_style: Taiwan map style
$(eval $(call STYLE_SIMPLE,twmap_style,MOI_OSM_twmap_style,styles/twmap_style,twmap_style,MOI_OSM_twmap.xml))
TWMAP_STYLE := $(twmap_style_VAR)

# tn_style: TN style with custom transformations
# This has custom sed transformations and extra resource copying that don't fit the standard macro
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
	cp styles/mapsforge_tn/tn_res/* $(BUILD_DIR)/mapsforge_tn/tn_res/
	cat styles/mapsforge_style/MOI_OSM.xml | \
		$(SED_CMD) \
			-e "s/__version__/$(VERSION)/g" \
			-e "s/file:moiosm_res/file:tn_res/g" \
			-e "s,file:/moiosm_res,file:/tn_res,g" \
			-e 's/outside="#FFFFFF"/outside="#00FFFFFF"/g' \
			-e "s,<!-- hillshading -->,<hillshading />,g" \
			-e "/TN-REMOVED-FROM/,/TN-REMOVED-TO/d" \
			-e "/-- coastlines-body --/ r styles/mapsforge_tn/coastlines.part" \
			-e 's/id="elmt-landcover" enabled="true"/id="elmt-landcover" enabled="false"/g' \
		> $(BUILD_DIR)/mapsforge_tn/MOI_OSM_TN.xml
	cd $(BUILD_DIR)/mapsforge_tn && \
		$(ZIP_CMD) $@ *


#==============================================================================
# ZIP Package Target Instantiations
#==============================================================================
# Using the ZIP_PACKAGE macro to create ZIP archive targets.
# Parameters: target_name, zip_file, dependencies, files_to_zip

# gmapsupp_zip: ZIP archive of gmapsupp.img for handheld devices
$(eval $(call ZIP_PACKAGE,gmapsupp_zip,$(GMAPSUPP_ZIP),$(GMAPSUPP),$(GMAPSUPP)))

# mapsforge_zip: ZIP of mapsforge map and POI database
$(eval $(call ZIP_PACKAGE,mapsforge_zip,$(MAPSFORGE_ZIP),$(MAPSFORGE) $(POI),$(MAPSFORGE) $(POI)))

# poi_zip: ZIP of POI database only
$(eval $(call ZIP_PACKAGE,poi_zip,$(POI_ZIP),$(POI),$(POI)))

# locus_poi_zip: ZIP of Locus-format POI database
$(eval $(call ZIP_PACKAGE,locus_poi_zip,$(LOCUS_POI_ZIP),$(LOCUS_POI),$(LOCUS_POI)))

# addr_zip: ZIP of address database
$(eval $(call ZIP_PACKAGE,addr_zip,$(ADDR_ZIP),$(ADDR),$(ADDR)))

# poi_v2_zip: Special handling - swaps POI_V2 into POI filename before zipping
# This target has unique logic that doesn't fit the standard macro
.PHONY: poi_v2_zip
poi_v2_zip: $(POI_V2_ZIP)
$(POI_V2_ZIP): $(POI_V2) $(POI)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -d "$(BUILD_DIR)" ]
	[ -f "$(POI)" ]
	[ -f "$(POI_V2)" ]
	-rm -rf $@
	cd $(BUILD_DIR) && \
		mv $(POI) $(POI).bak && cp $(POI_V2) $(POI) && \
		$(ZIP_CMD) $@ $(shell basename $(POI)) && \
		mv $(POI).bak $(POI)


GPX_OSM ?= $(BUILD_DIR)/Happyman-gpx.osm
GPX_BASE = $(basename $(GPX_OSM))
GPX_BASE_EXT = $(notdir $(GPX_OSM))

.PHONY: gpx
gpx: $(GPX_BASE).map
$(GPX_BASE).map: $(GPX_BASE_EXT)
	[ -f $(GPX_BASE_EXT) ]
	[ -n "$(OSMOSIS_BOUNDING)" ]
	rm -f $(GPX_BASE)-sed.pbf $(GPX_BASE)-ren.pbf
	python3.10 osm_scripts/gpx_handler.py $(GPX_BASE_EXT) $(GPX_BASE)-sed.pbf
	osmium renumber \
		-s 1,1,0 \
		$(GPX_BASE)-sed.pbf \
		-Oo $(GPX_BASE)-ren.pbf
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && \
		$(TOOLS_DIR)/gpx-build.sh \
			"$(GPX_BASE)-ren.pbf" \
			"$@" \
			"$(OSMOSIS_CMD)" \
			"$(OSMOSIS_BOUNDING)" \
			"$(MAPWITER_THREADS)" \
			"zh,en" \
			"osm_scripts/gpx-mapping.xml" \
			"$(VERSION) / (c) GPX: $(notdir $(GPX_BASE))" \
			""


WITH_GPX = $(dir $(GPX_OSM))MOI_OSM_$(basename $(notdir $(GPX_OSM)))

.PHONY: with_gpx
with_gpx: $(WITH_GPX).map
$(WITH_GPX).map: $(MAPSFORGE_PBF) $(TAG_MAPPING) $(GPX_BASE_EXT)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	[ -f $(GPX_BASE_EXT) ]
	[ -n "$(OSMOSIS_BOUNDING)" ]
	mkdir -p $(BUILD_DIR)
	rm -rf $(GPX_BASE)-sed.pbf $(WITH_GPX)-add.pbf
	python3 osm_scripts/gpx_handler.py $(GPX_BASE_EXT) $(GPX_BASE)-sed.pbf
	cp -a $(MAPSFORGE_PBF) $(WITH_GPX)-add.pbf
	osm_scripts/osium-append.sh $(WITH_GPX)-add.pbf $(GPX_BASE)-sed.pbf
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && \
		$(TOOLS_DIR)/gpx-build.sh \
			"$(WITH_GPX)-add.pbf" \
			"$@" \
			"$(OSMOSIS_CMD)" \
			"$(OSMOSIS_BOUNDING)" \
			"$(MAPWITER_THREADS)" \
			"$(MAPSFORGE_NTL)" \
			"$(TAG_MAPPING)" \
			"$(VERSION)  /  (c) Map: Rudy; GPX: $(notdir $(WITH_GPX))" \
			"" \
		> /dev/null 2> /dev/null


GPX_MAPSFORGE ?= $(BUILD_DIR)/Happyman-wptgpx.map

.PHONY: gpx-2
gpx-2: $(GPX_MAPSFORGE)
$(GPX_MAPSFORGE): $(BUILD_DIR)/track.pbf $(BUILD_DIR)/waypoint.pbf
	[ -n "$(OSMOSIS_BOUNDING)" ]
	rm -f $(BUILD_DIR)/track-sed.pbf $(BUILD_DIR)/waypoint-sed.pbf
	python3 osm_scripts/gpx_handler.py $(BUILD_DIR)/track.pbf $(BUILD_DIR)/track-sed.pbf
	python3 osm_scripts/gpx_handler.py $(BUILD_DIR)/waypoint.pbf $(BUILD_DIR)/waypoint-sed.pbf
	osmium renumber \
		-s 1,1,0 \
		$(BUILD_DIR)/track-sed.pbf \
		-Oo $(@:.map=.pbf)
	osm_scripts/osium-append.sh $(@:.map=.pbf) $(BUILD_DIR)/waypoint-sed.pbf
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && \
		$(TOOLS_DIR)/gpx-build.sh \
			"$(@:.map=.pbf)" \
			"$@" \
			"$(OSMOSIS_CMD)" \
			"$(OSMOSIS_BOUNDING)" \
			"$(MAPWITER_THREADS)" \
			"zh,en" \
			"osm_scripts/gpx-mapping.xml" \
			"$(VERSION) / (c) Map: Happyman" \
			""

.PHONY: mapsforge
mapsforge: $(MAPSFORGE)
$(MAPSFORGE): $(MAPSFORGE_PBF) $(TAG_MAPPING)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(REGION)" ]
	[ -n "$(OSMOSIS_BOUNDING)" ]
	mkdir -p $(BUILD_DIR)
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && \
		$(TOOLS_DIR)/gpx-build.sh \
			"$(MAPSFORGE_PBF)" \
			"$@" \
			"$(OSMOSIS_CMD)" \
			"$(OSMOSIS_BOUNDING)" \
			"$(MAPWITER_THREADS)" \
			"$(MAPSFORGE_NTL)" \
			"$(TAG_MAPPING)" \
			"$(VERSION)  /  (c) Map: Rudy; Map data: OSM contributors; DEM data: $(DEM_NAME)" \
			"polylabel=false simplification-factor=2.5 simplification-max-zoom=12"
	
$(COMMON_TILES): $(GMAP_INPUT)
	date +'DS: %H:%M:%S $(shell basename $@)'
	[ -n "$(MAPID)" ]
	rm -rf $(COMMON_TILES_DIR)
	mkdir -p $(COMMON_TILES_DIR)
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && cd $(COMMON_TILES_DIR) && \
		java $(JAVACMD_OPTIONS) -jar $(SPLITTER_JAR) \
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
