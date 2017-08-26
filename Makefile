# base (0x2000) + region x lang x style
# where, ...
# - 1st hex, dem    -> moi(1), srtm(2)
# - 2nd hex, region -> taiwan(0), taipei(1), kyushu(2), Beibeiji(3), Yushan(4)
# - 3rd hex, lang   -> en(0), zh(1),
# - 4th hex, style  -> jing(0), outdoor(1), odc(2), bw(3), odc_dem(4), bw_dem(5)

# directory variables
ROOT_DIR := $(shell pwd)
TOOLS_DIR := $(ROOT_DIR)/tools
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
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = ele_taiwan_100_500_1000_moi_zls.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
MF_WRITER_OPTS := bbox=23.226,120.822,23.578,121.249
DEM_NAME := MOI
TARGETS := mapsforge

else ifeq ($(SUITE),bbox)
# REGION: specify your REGION name for bbox
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = ele_taiwan_100_500_1000_moi_zls.osm.pbf
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
DEM_NAME := MOI
TARGETS := mapsforge

else ifeq ($(SUITE),bbox_bw)
# REGION: specify your REGION name for bbox
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TYP := bw
STYLE := swisspopo
STYLE_NAME := bw
DEM_NAME := MOI
MAPID := $(shell printf %d 0x1f13)
TARGETS := gmap

else ifeq ($(SUITE),bbox_odc)
# REGION: specify your REGION name for bbox
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TYP := outdoorc
STYLE := swisspopo
STYLE_NAME := odc
DEM_NAME := MOI
MAPID := $(shell printf %d 0x1f12)
TARGETS := gmap

else ifeq ($(SUITE),bbox_odc_dem)
# REGION: specify your REGION name for bbox
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
BOUNDING_BOX := true
TYP := outdoorc
STYLE := swisspopo
STYLE_NAME := odc
DEM_NAME := MOI
GMAPDEM_ID := 05010000
GMAPDEM_FILE := $(GMAPDEM_ID).img
GMAPDEM := $(ELEVATIONS_DIR)/gmapdem/$(GMAPDEM_FILE)
MAPID := $(shell printf %d 0x1f14)
TARGETS := gmap

else ifeq ($(SUITE),taiwan)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = lab_taiwan_100_500_1000_moi_zls.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
MF_WRITER_OPTS := bbox=21.55682,118.12141,26.44212,122.31377
DEM_NAME := MOI
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
MAPSFORGE_STYLE_DIR := mapsforge_style
MAPSFORGE_STYLE_FILE := MOI_OSM.xml
MAPSFORGE_STYLE := $(BUILD_DIR)/$(NAME_MAPSFORGE)_style.zip
LOCUS_STYLE_DIR := locus_style
LOCUS_STYLE_INST := MOI_OSM_Taiwan_TOPO_Rudy_style
LOCUS_STYLE_FILE := MOI_OSM.xml
TARGETS := mapsforge_zip poi_zip mapsforge_style locus_style twmap_style

else ifeq ($(SUITE),taiwan_gts)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = lab_taiwan_100_500_1000_moi_zls.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
MF_WRITER_OPTS := bbox=21.55682,118.12141,26.44212,122.31377
DEM_NAME := MOI
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
MAPSFORGE_STYLE_DIR := mapsforge_hs
MAPSFORGE_STYLE_FILE := MOI_OSM.xml
MAPSFORGE_STYLE := $(BUILD_DIR)/$(NAME_MAPSFORGE)_hs_style.zip
HGT := $(ROOT_DIR)/hgt/moi-hgt-v3.zip
GTS_ALL := $(BUILD_DIR)/$(NAME_MAPSFORGE)
TARGETS := mapsforge_zip mapsforge_style gts_all

else ifeq ($(SUITE),taiwan_lite)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_20_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = lab_taiwan_100_500_1000_moi_zls_lite.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
MF_WRITER_OPTS := bbox=21.55682,118.12141,26.44212,122.31377
DEM_NAME := MOI
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Lite
MAPSFORGE_STYLE_DIR := mapsforge_lite
MAPSFORGE_STYLE_FILE := MOI_OSM_Lite.xml
MAPSFORGE_STYLE := $(BUILD_DIR)/$(NAME_MAPSFORGE)_style.zip
LOCUS_STYLE_DIR := locus_lite
LOCUS_STYLE_INST := MOI_OSM_Taiwan_TOPO_Rudy_lite
LOCUS_STYLE_FILE := MOI_OSM_Lite.xml
HGT := $(ROOT_DIR)/hgt/moi-hgt-lite.zip
GTS_ALL := $(BUILD_DIR)/$(NAME_MAPSFORGE)
TARGETS := mapsforge_zip mapsforge_style gts_all

else ifeq ($(SUITE),beibeiji)
REGION := Beibeiji
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = ele_taiwan_100_500_1000_moi_zls.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
MF_WRITER_OPTS := bbox=24.6731646,121.2826336,25.2997353,122.0064049
DEM_NAME := MOI
TARGETS := mapsforge

else ifeq ($(SUITE),taipei)
REGION := Taipei
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = ele_taiwan_100_500_1000_moi_zls.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
MF_WRITER_OPTS := bbox=24.96034,121.4570,25.21024,121.6659
DEM_NAME := MOI
TARGETS := mapsforge

else ifeq ($(SUITE),yushan_bw)
REGION := Yushan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
TYP := bw
STYLE := swisspopo
STYLE_NAME := bw
DEM_NAME := MOI
MAPID := $(shell printf %d 0x1413)
TARGETS := gmap

else ifeq ($(SUITE),yushan_odc)
REGION := Yushan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
TYP := outdoorc
STYLE := swisspopo
STYLE_NAME := odc
DEM_NAME := MOI
MAPID := $(shell printf %d 0x1412)
TARGETS := gmap

else ifeq ($(SUITE),yushan_odc_dem)
REGION := Yushan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
TYP := outdoorc
STYLE := swisspopo
STYLE_NAME := odc
DEM_NAME := MOI
GMAPDEM_ID := 05010000
GMAPDEM_FILE := $(GMAPDEM_ID).img
GMAPDEM := $(ELEVATIONS_DIR)/gmapdem/$(GMAPDEM_FILE)
MAPID := $(shell printf %d 0x1414)
TARGETS := gmap

else ifeq ($(SUITE),beibeiji_bw)
REGION := Beibeiji
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
TYP := bw
STYLE := swisspopo
STYLE_NAME := bw
DEM_NAME := MOI
MAPID := $(shell printf %d 0x1313)
TARGETS := gmap

else ifeq ($(SUITE),beibeiji_odc)
REGION := Beibeiji
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
TYP := outdoorc
STYLE := swisspopo
STYLE_NAME := odc
DEM_NAME := MOI
MAPID := $(shell printf %d 0x1312)
TARGETS := gmap

else ifeq ($(SUITE),taiwan_jing)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := jing
STYLE := jing
STYLE_NAME := jing
DEM_NAME := MOI
MAPID := $(shell printf %d 0x2010)
TARGETS := gmap

else ifeq ($(SUITE),taiwan_srtm3_odr)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_view1,srtm1,view3,srtm3.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := outdoor
STYLE := fzk
STYLE_NAME := odr
DEM_NAME := SRTM3
MAPID := $(shell printf %d 0x2011)
TARGETS := gmap

else ifeq ($(SUITE),taiwan_srtm3_odc)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_view1,srtm1,view3,srtm3.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := outdoorc
STYLE := swisspopo
STYLE_NAME := odc
DEM_NAME := SRTM3
MAPID := $(shell printf %d 0x2012)
TARGETS := gmap

else ifeq ($(SUITE),taiwan_srtm3_bw)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_view1,srtm1,view3,srtm3.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := bw
STYLE := swisspopo
STYLE_NAME := bw
DEM_NAME := SRTM3
MAPID := $(shell printf %d 0x2013)
TARGETS := gmap

else ifeq ($(SUITE),taiwan_bw)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := bw
STYLE := swisspopo
STYLE_NAME := bw
DEM_NAME := MOI
MAPID := $(shell printf %d 0x1013)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taiwan_odc)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := outdoorc
STYLE := swisspopo
STYLE_NAME := odc
DEM_NAME := MOI
MAPID := $(shell printf %d 0x1012)
TARGETS := gmapsupp_zip gmap nsis

else ifeq ($(SUITE),taiwan_bw_dem)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := bw
STYLE := swisspopo
STYLE_NAME := bw3D
DEM_NAME := MOI
GMAPDEM_ID := 05010000
GMAPDEM_FILE := $(GMAPDEM_ID).img
GMAPDEM := $(ELEVATIONS_DIR)/gmapdem/$(GMAPDEM_FILE)
MAPID := $(shell printf %d 0x1015)
TARGETS := gmap nsis

else ifeq ($(SUITE),taiwan_odc_dem)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
TYP := outdoorc
STYLE := swisspopo
STYLE_NAME := odc3D
DEM_NAME := MOI
GMAPDEM_ID := 05010000
GMAPDEM_FILE := $(GMAPDEM_ID).img
GMAPDEM := $(ELEVATIONS_DIR)/gmapdem/$(GMAPDEM_FILE)
MAPID := $(shell printf %d 0x1014)
TARGETS := gmap nsis

else ifeq ($(SUITE),taipei_odc)
REGION := Taipei
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
TYP := outdoorc
STYLE := swisspopo
STYLE_NAME := odc
DEM_NAME := MOI
MAPID := $(shell printf %d 0x2112)
TARGETS := gmap

else ifeq ($(SUITE),taipei_bw)
REGION := Taipei
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
TYP := bw
STYLE := swisspopo
STYLE_NAME := bw
DEM_NAME := MOI
MAPID := $(shell printf %d 0x2113)
TARGETS := gmap

else ifeq ($(SUITE),taipei_en_bw)
REGION := Taipei
LANG := en
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
TYP := bw
STYLE := swisspopo
STYLE_NAME := bw
DEM_NAME := MOI
MAPID := $(shell printf %d 0x2103)
TARGETS := gmap

else ifeq ($(SUITE),kyushu_srtm3_en_bw)
REGION := Kyushu
LANG := en
CODE_PAGE := 950
#CODE_PAGE := 1252
ELEVATION_FILE = ele_japan_10_100_500_view1,view3.osm.pbf
EXTRACT_FILE := japan-latest
POLY_FILE := Kyushu.poly
TYP := bw
STYLE := swisspopo
STYLE_NAME := bw
DEM_NAME := SRTM3
MAPID := $(shell printf %d 0x2313)
TARGETS := gmap

endif

# auto variables
VERSION := $(shell date +%Y.%m.%d)
MAPID_LO_HEX := $(shell printf '%x' $(MAPID) | cut -c3-4)
MAPID_HI_HEX := $(shell printf '%x' $(MAPID) | cut -c1-2)

NAME_LONG := $(DEM_NAME).OSM.$(STYLE_NAME) - $(REGION) TOPO v$(VERSION) (by Rudy)
NAME_SHORT := $(DEM_NAME).OSM.$(STYLE_NAME) - $(REGION) TOPO v$(VERSION) (by Rudy)
NAME_WORD := $(DEM_NAME)_$(REGION)_TOPO_$(STYLE_NAME)
NAME_MAPSFORGE ?= $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy

# finetune options
JAVACMD_OPTIONS := -Xmx72G -server

DATA_DIR := $(WORKS_DIR)/$(REGION)/data$(MAPID)
MAP_DIR := $(WORKS_DIR)/$(REGION)/$(NAME_WORD)

ELEVATION := $(ELEVATIONS_DIR)/$(ELEVATION_FILE)
ELEVATION_MARKER := $(ELEVATIONS_DIR)/marker/$(ELEVATION_MARKER_FILE)
EXTRACT := $(EXTRACT_DIR)/$(EXTRACT_FILE)
CITY := $(CITIES_DIR)/TW.zip
TILES := $(DATA_DIR)/.done
MAP := $(MAP_DIR)/.done
PBF := $(BUILD_DIR)/$(REGION).osm.pbf
TYP_FILE := $(ROOT_DIR)/TYPs/$(TYP).txt
STYLE_DIR := $(ROOT_DIR)/styles/$(STYLE)
TAG_MAPPING := $(ROOT_DIR)/osm_scripts/tag-mapping.xml

DEM_FIX := $(shell echo $(DEM_NAME) | tr A-Z a-z)

GMAPSUPP := $(BUILD_DIR)/gmapsupp_$(REGION)_$(DEM_FIX)_$(LANG)_$(STYLE_NAME).img
GMAPSUPP_ZIP := $(GMAPSUPP).zip
GMAP := $(BUILD_DIR)/$(REGION)_$(DEM_FIX)_$(LANG)_$(STYLE_NAME).gmap.zip
NSIS := $(BUILD_DIR)/Install_$(NAME_WORD).exe
POI := $(BUILD_DIR)/$(NAME_MAPSFORGE).poi
POI_ZIP := $(POI).zip
MAPSFORGE := $(BUILD_DIR)/$(NAME_MAPSFORGE).map
MAPSFORGE_ZIP := $(MAPSFORGE).zip
TWMAP_STYLE := $(BUILD_DIR)/MOI_OSM_twmap_style.zip
MAPSFORGE_PBF := $(BUILD_DIR)/$(NAME_MAPSFORGE)_zls.osm.pbf
LOCUS_STYLE := $(BUILD_DIR)/$(NAME_MAPSFORGE)_locus_style.zip
LICENSE := $(BUILD_DIR)/taiwan_topo.html

ifeq ($(shell uname),Darwin)
MD5_CMD := md5 -q $$EXAM_FILE
JMC_CMD := jmc/osx/jmc_cli
else
MD5_CMD := md5sum $$EXAM_FILE | cut -d' ' -f1
JMC_CMD := jmc/linux/jmc_cli
endif

all: $(TARGETS)

clean:
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(WORKS_DIR)" ]
	-rm -rf $(BUILD_DIR)
	-rm -rf $(WORKS_DIR)

distclean:
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(WORKS_DIR)" ]
	-rm -rf $(BUILD_DIR)
	-rm -rf $(WORKS_DIR)
	-rm -rf $(DOWNLOAD_DIR)

.PHONY: install
install: $(LICENSE) $(GMAPSUPP)
	[ -n "$(INSTALL_DIR)" ]
	[ -d "$(INSTALL_DIR)" ]
	cp -r $(GMAPSUPP) $(INSTALL_DIR)
	cp -r $(BUILD_DIR)/images $(INSTALL_DIR)
	cp $(LICENSE) $(INSTALL_DIR)/taiwan_topo.html

.PHONY: drop
drop:
	[ -n "$(INSTALL_DIR)" ]
	[ -d "$(INSTALL_DIR)" ]
	cp -r images auto-install/* $(INSTALL_DIR)
	cp -r $(BUILD_DIR)/{*.zip,*.exe,*.html} $(INSTALL_DIR)
	cd $(INSTALL_DIR) && md5sum *.zip *.exe *.html *.xml > md5sum.txt
	cat docs/beta.md | sed -e "s|__version__|$(VERSION)|g" | \
	    markdown -f +autolink > $(INSTALL_DIR)/beta.html
	cp -r docs/gts $(INSTALL_DIR) && \
		cat docs/gts/index.html | sed -e "s|__version__|$(VERSION)|g" > $(INSTALL_DIR)/gts/index.html

suites:
	echo "make SUITE taiwan_bw taiwan_odc taiwan"
	git pull --rebase
	git status
	make distclean
	make SUITE=taiwan_bw all
	make SUITE=taiwan_odc all
	make SUITE=taiwan all

.PHONY: license $(LICENSE)
license: $(LICENSE)
$(LICENSE):
	[ -n "$(VERSION)" ]
	mkdir -p $(BUILD_DIR)
	cp -a images $(BUILD_DIR)
	cat docs/taiwan_topo.md | sed -e "s|__version__|$(VERSION)|g" | \
	    markdown -f +autolink > $(BUILD_DIR)/taiwan_topo.article
	cat docs/github_flavor.html | sed "/__article_body__/ r $(BUILD_DIR)/taiwan_topo.article" > $@

.PHONY: gts_all
gts_all: $(GTS_ALL).zip
$(GTS_ALL).zip: $(MAPSFORGE_ZIP) $(MAPSFORGE_STYLE) $(HGT)
	[ -n "$(GTS_ALL)" ]
	rm -rf $(GTS_ALL) $(GTS_ALL).zip
	mkdir -p $(GTS_ALL)
	cd $(GTS_ALL) && \
		unzip $(MAPSFORGE_ZIP) -d map && \
		unzip $(MAPSFORGE_STYLE) -d mapthemes && \
		unzip $(HGT) -d hgt && \
		zip -r $(GTS_ALL).zip map/ mapthemes/ hgt/

.PHONY: nsis
nsis: $(NSIS)
$(NSIS): $(MAP)
	[ -n "$(MAPID)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cd $(MAP_DIR) && \
		rm -rf $@ && \
		for i in $(shell cd $(MAP_DIR); ls $(MAPID)*.img $(GMAPDEM_FILE)); do \
			echo '  CopyFiles "$$MyTempDir\'"$${i}"'" "$$INSTDIR\'"$${i}"'"  '; \
			echo '  Delete "$$MyTempDir\'"$${i}"'"  '; \
		done > copy_tiles.txt && \
		for i in $(shell cd $(MAP_DIR); ls $(MAPID)*.img $(GMAPDEM_FILE)); do \
			echo '  Delete "$$INSTDIR\'"$${i}"'"  '; \
		done > delete_tiles.txt && \
		cat $(ROOT_DIR)/mkgmaps/makensis.cfg | sed \
			-e "s|__root_dir__|$(ROOT_DIR)|g" \
			-e "s|__name_word__|$(NAME_WORD)|g" \
			-e "s|__version__|$(VERSION)|g" \
			-e "s|__mapid_lo_hex__|$(MAPID_LO_HEX)|g" \
			-e "s|__mapid_hi_hex__|$(MAPID_HI_HEX)|g" \
			-e "s|__mapid__|$(MAPID)|g" > $(NAME_WORD).nsi && \
		sed "/__copy_tiles__/ r copy_tiles.txt" -i $(NAME_WORD).nsi && \
		sed "/__delete_tiles__/ r delete_tiles.txt" -i $(NAME_WORD).nsi && \
		zip -r "$(NAME_WORD)_InstallFiles.zip" $(MAPID)*.img $(MAPID).TYP $(GMAPDEM_FILE) $(NAME_WORD){.img,_mdr.img,.tdb,.mdx} && \
		cat $(ROOT_DIR)/docs/taiwan_topo.md | sed \
			-e "s|__version__|$(VERSION)|g" | iconv -f UTF-8 -t BIG-5//TRANSLIT -o readme.txt && \
		cp $(ROOT_DIR)/nsis/{Install.bmp,Deinstall.bmp} . && \
		makensis $(NAME_WORD).nsi
	cp "$(MAP_DIR)/Install_$(NAME_WORD).exe" $@

.PHONY: poi
poi: $(POI)
$(POI): $(EXTRACT).osm.pbf
	[ -n "$(EXTRACT)" ]
	mkdir -p $(BUILD_DIR)
	-rm -rf $@
	export JAVACMD_OPTIONS="-server" && \
	    sh $(TOOLS_DIR)/osmosis/bin/osmosis \
		--rb file="$(EXTRACT).osm.pbf" \
		--poi-writer \
			all-tags=false \
			ways=true \
			comment="$(VERSION)  /  (c) Map data: OSM contributors" \
		    file="$@"

.PHONY: gmap
gmap: $(GMAP)
$(GMAP): $(MAP)
	[ -n "$(MAPID)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cd $(MAP_DIR) && \
	    rm -rf $@ && \
	    cat $(ROOT_DIR)/mkgmaps/jmc_cli.cfg | sed \
	    	-e "s|__map_dir__|$(MAP_DIR)|g" \
		-e "s|__name_word__|$(NAME_WORD)|g" \
		-e "s|__mapid__|$(MAPID)|g" > jmc_cli.cfg && \
	    $(TOOLS_DIR)/$(JMC_CMD) -v -config="$(MAP_DIR)/jmc_cli.cfg" && \
	    [ -d "$(NAME_SHORT).gmap" ] && mv "$(NAME_SHORT).gmap" "$(NAME_WORD).gmap" || true && \
	    zip -r $@ "$(NAME_WORD).gmap"

.PHONY: gmapsupp
gmapsupp: $(GMAPSUPP)
$(GMAPSUPP): $(MAP)
	[ -n "$(MAPID)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cd $(MAP_DIR) && \
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
	cp $(MAP_DIR)/gmapsupp.img $@

.PHONY: gmapsupp_zip
gmapsupp_zip: $(GMAPSUPP_ZIP)
$(GMAPSUPP_ZIP): $(GMAPSUPP)
	[ -d "$(BUILD_DIR)" ]
	[ -f "$(GMAPSUPP)" ]
	-rm -rf $@
	cd $(BUILD_DIR) && zip -r $@ $(shell basename $(GMAPSUPP))

ifeq ($(LANG),zh) 
NTL := name,name:zh,name:en
MAPSFORGE_NTL := zh,en
else ifeq ($(LANG),en)
NTL := name:en,name:zh,name
MAPSFORGE_NTL := en
endif

.PHONY: map
map: $(MAP)
$(MAP): $(TILES) $(TYP_FILE) $(STYLE_DIR) $(GMAPDEM)
	[ -n "$(MAPID)" ]
	rm -rf $(MAP_DIR)
	mkdir -p $(MAP_DIR)
	cd $(MAP_DIR) && \
	    cat $(TYP_FILE) | sed \
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
		$(TYP).txt && \
	    cp $(TYP).typ $(MAPID).TYP && \
	    mkdir $(MAP_DIR)/style && \
	    cp -a $(STYLE_DIR) $(MAP_DIR)/style/$(STYLE) && \
	    cp $(ROOT_DIR)/styles/style-translations $(MAP_DIR)/ && \
	    cat $(ROOT_DIR)/mkgmaps/mkgmap.cfg | sed \
		-e "s|__root_dir__|$(ROOT_DIR)|g" \
		-e "s|__map_dir__|$(MAP_DIR)|g" \
		-e "s|__version__|$(VERSION)|g" \
		-e "s|__style__|$(STYLE)|g" \
		-e "s|__name_tag_list__|$(NTL)|g" \
		-e "s|__code_page__|$(CODE_PAGE)|g" \
		-e "s|__name_long__|$(NAME_LONG)|g" \
		-e "s|__name_short__|$(NAME_SHORT)|g" \
		-e "s|__name_word__|$(NAME_WORD)|g" \
		-e "s|__mapid__|$(MAPID)|g" > mkgmap.cfg && \
	    cat $(DATA_DIR)/template.args | sed \
	        -e "s|input-file: \(.*\)|input-file: $(DATA_DIR)/\\1|g" >> mkgmap.cfg && \
	    { [ -n "$(GMAPDEM)" ] && \
		cp $(GMAPDEM) . && \
	        cat $(ROOT_DIR)/mkgmaps/gmapdem.cfg | sed \
	            -e "s|__gmapdem_id__|$(GMAPDEM_ID)|g" \
	            -e "s|__map_dir__|$(MAP_DIR)|g" >> mkgmap.cfg || \
		echo no gmapdem ; } && \
	    java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
	        --max-jobs=16 \
	        -c mkgmap.cfg \
		--check-styles
	touch $(MAP)

ELEVATIONS_URL := https://dl.dropboxusercontent.com/u/899714/src-data/osm_elevations
$(ELEVATION):
	[ -n "$(REGION)" ]
	mkdir -p $(ELEVATIONS_DIR)
	cd $(ELEVATIONS_DIR) && \
	    curl -k $(ELEVATIONS_URL)/$(ELEVATION_FILE) -o $(ELEVATION_FILE) && \
	    curl -k $(ELEVATIONS_URL)/$(ELEVATION_FILE).md5 -o $(ELEVATION_FILE).md5 && \
	    EXAM_FILE=$@; [ "$$($(MD5_CMD))" == "$$(cat $(ELEVATION_FILE).md5 | cut -d' ' -f1)" ] || \
	    	( rm -rf $@ && false )

$(ELEVATION_MARKER):
	[ -n "$(REGION)" ]
	mkdir -p $(ELEVATIONS_DIR)/marker
	cd $(ELEVATIONS_DIR)/marker && \
	    curl -k $(ELEVATIONS_URL)/$(ELEVATION_MARKER_FILE) -o $(ELEVATION_MARKER_FILE) && \
	    curl -k $(ELEVATIONS_URL)/$(ELEVATION_MARKER_FILE).md5 -o $(ELEVATION_MARKER_FILE).md5 && \
	    EXAM_FILE=$@; [ "$$($(MD5_CMD))" == "$$(cat $(ELEVATION_MARKER_FILE).md5 | cut -d' ' -f1)" ] || \
	    	( rm -rf $@ && false )

$(GMAPDEM):
	[ -n "$(REGION)" ]
	mkdir -p $(ELEVATIONS_DIR)/gmapdem
	cd $(ELEVATIONS_DIR)/gmapdem && \
	    curl -k $(ELEVATIONS_URL)/gmapdem/$(GMAPDEM_FILE) -o $(GMAPDEM_FILE) && \
	    curl -k $(ELEVATIONS_URL)/gmapdem/$(GMAPDEM_FILE).md5 -o $(GMAPDEM_FILE).md5 && \
	    EXAM_FILE=$@; [ "$$($(MD5_CMD))" == "$$(cat $(GMAPDEM_FILE).md5 | cut -d' ' -f1)" ] || \
	    	( rm -rf $@ && false )

EXTRACT_URL := http://osm.kcwu.csie.org/download/tw-extract/recent
$(EXTRACT).osm:
	[ -n "$(REGION)" ]
	mkdir -p $(EXTRACT_DIR)
	cd $(EXTRACT_DIR) && \
	    curl $(EXTRACT_URL)/$(EXTRACT_FILE).o5m -o $(EXTRACT_FILE).o5m && \
	    curl $(EXTRACT_URL)/$(EXTRACT_FILE).o5m.md5 -o $(EXTRACT_FILE).o5m.md5 && \
	    EXAM_FILE=$(EXTRACT_FILE).o5m; [ "$$($(MD5_CMD))" == "$$(cat $(EXTRACT_FILE).o5m.md5 | sed -e 's/^.* = //')" ] && \
	    osmconvert $(EXTRACT_FILE).o5m -o=$(EXTRACT_FILE).osm || \
	        ( rm -rf $(EXTRACT_FILE).o5m* && false )

$(EXTRACT).osm.pbf: $(EXTRACT).osm
	[ -n "$(REGION)" ]
	mkdir -p $(EXTRACT_DIR)
	cd $(EXTRACT_DIR) && \
	    cat $(EXTRACT_FILE).osm | osmconvert - -o=$@

$(EXTRACT)-sed.osm.pbf: $(EXTRACT).osm osm_scripts/parse_osm.py
	[ -n "$(REGION)" ]
	mkdir -p $(EXTRACT_DIR)
	cd $(EXTRACT_DIR) && \
		cat $(EXTRACT_FILE).osm | python2.7 $(ROOT_DIR)/osm_scripts/extrac_hknetwork.py > hknetworks.json && \
	    cat $(EXTRACT_FILE).osm | python2.7 $(ROOT_DIR)/osm_scripts/parse_osm.py | osmconvert - -o=$@

# OSMOSIS_OPTS
ifneq (,$(strip $(POLY_FILE)))
ifeq (Taiwan,$(REGION))
    OSMOSIS_OPTS := $(strip $(OSMOSIS_OPTS) --bounding-polygon file="$(POLIES_DIR)/$(POLY_FILE)" completeWays=no completeRelations=no cascadingRelations=no clipIncompleteEntities=true)
else
    OSMOSIS_OPTS := $(strip $(OSMOSIS_OPTS) --bounding-polygon file="$(POLIES_DIR)/$(POLY_FILE)" completeWays=yes completeRelations=yes cascadingRelations=yes clipIncompleteEntities=true)
endif
else ifneq (,$(strip $(BOUNDING_BOX)))
    OSMOSIS_OPTS := $(strip $(OSMOSIS_OPTS) --bounding-box top=$(TOP) bottom=$(BOTTOM) left=$(LEFT) right=$(RIGHT) completeWays=yes completeRelations=yes cascadingRelations=yes clipIncompleteEntities=true)
    MF_WRITER_OPTS := bbox=$(BOTTOM),$(LEFT),$(TOP),$(RIGHT)
endif

$(PBF): $(EXTRACT).osm.pbf $(ELEVATION)
	[ -n "$(REGION)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && \
	    sh $(TOOLS_DIR)/osmosis/bin/osmosis \
		--read-pbf $(EXTRACT).osm.pbf \
		--read-pbf $(ELEVATION) \
		--merge \
		$(OSMOSIS_OPTS) \
		--buffer --write-pbf $@ \
		omitmetadata=true

$(MAPSFORGE_PBF): $(EXTRACT)-sed.osm.pbf $(ELEVATION) $(ELEVATION_MARKER)
	[ -n "$(REGION)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && \
	    sh $(TOOLS_DIR)/osmosis/bin/osmosis \
		--read-pbf $(EXTRACT)-sed.osm.pbf \
		--read-pbf $(ELEVATION) --tag-transform file="$(ROOT_DIR)/osm_scripts/tt-ele.xml" \
		--read-pbf $(ELEVATION_MARKER) \
		--merge \
		--merge \
		$(OSMOSIS_OPTS) \
		--buffer --write-pbf $@ \
		omitmetadata=true

.PHONY: mapsforge_style $(MAPSFORGE_STYLE)
mapsforge_style: $(MAPSFORGE_STYLE)
$(MAPSFORGE_STYLE):
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(REGION)" ]
	-rm -rf $@
	-rm -rf $(BUILD_DIR)/$(MAPSFORGE_STYLE_DIR)
	mkdir -p $(BUILD_DIR)
	cp -a styles/$(MAPSFORGE_STYLE_DIR) $(BUILD_DIR)
	cat styles/$(MAPSFORGE_STYLE_DIR)/$(MAPSFORGE_STYLE_FILE) | \
	    sed -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/$(MAPSFORGE_STYLE_DIR)/$(MAPSFORGE_STYLE_FILE)
	cd $(BUILD_DIR)/$(MAPSFORGE_STYLE_DIR) && zip -r $@ *

.PHONY: locus_style $(LOCUS_STYLE)
locus_style: $(LOCUS_STYLE)
$(LOCUS_STYLE):
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(REGION)" ]
	-rm -rf $@
	-rm -rf $(BUILD_DIR)/$(LOCUS_STYLE_INST)
	mkdir -p $(BUILD_DIR)
	cp -a styles/$(LOCUS_STYLE_DIR) $(BUILD_DIR)/$(LOCUS_STYLE_INST)
	cat styles/$(LOCUS_STYLE_DIR)/$(LOCUS_STYLE_FILE) | \
	    sed -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/$(LOCUS_STYLE_INST)/$(LOCUS_STYLE_FILE)
	cd $(BUILD_DIR) && zip -r $@ $(LOCUS_STYLE_INST)/

.PHONY: twmap_style $(TWMAP_STYLE)
twmap_style: $(TWMAP_STYLE)
$(TWMAP_STYLE):
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(REGION)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cp -a styles/twmap_style $(BUILD_DIR)
	cat styles/twmap_style/MOI_OSM_twmap.xml | \
	    sed -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/twmap_style/MOI_OSM_twmap.xml
	cd $(BUILD_DIR)/twmap_style && zip -r $@ *

.PHONY: mapsforge_zip
mapsforge_zip: $(MAPSFORGE_ZIP)
$(MAPSFORGE_ZIP): $(MAPSFORGE)
	[ -d "$(BUILD_DIR)" ]
	[ -f "$(MAPSFORGE)" ]
	-rm -rf $@
	cd $(BUILD_DIR) && zip -r $@ $(shell basename $(MAPSFORGE))

.PHONY: poi_zip
poi_zip: $(POI_ZIP)
$(POI_ZIP): $(POI)
	[ -d "$(BUILD_DIR)" ]
	[ -f "$(POI)" ]
	-rm -rf $@
	cd $(BUILD_DIR) && zip -r $@ $(shell basename $(POI))

.PHONY: mapsforge
mapsforge: $(MAPSFORGE)
$(MAPSFORGE): $(MAPSFORGE_PBF) $(TAG_MAPPING)
	[ -n "$(REGION)" ]
	mkdir -p $(BUILD_DIR)
	export JAVACMD_OPTIONS="-Xmx64G -server" && \
	    sh $(TOOLS_DIR)/osmosis/bin/osmosis \
		--read-pbf "$(MAPSFORGE_PBF)" \
		--buffer --mapfile-writer \
		    type=ram $(MF_WRITER_OPTS) \
		    preferred-languages="$(MAPSFORGE_NTL)" \
		    tag-conf-file="$(TAG_MAPPING)" \
		    polygon-clipping=true way-clipping=true label-position=true \
		    zoom-interval-conf=6,0,6,10,7,11,14,12,21 \
		    map-start-zoom=12 \
		    comment="$(VERSION)  /  (c) Map: Rudy; Map data: OSM contributors; DEM data: Taiwan MOI" \
		    file="$@"
	
$(TILES): $(PBF)
	[ -n "$(MAPID)" ]
	rm -rf $(DATA_DIR)
	mkdir -p $(DATA_DIR)
	export JAVACMD_OPTIONS="$(JAVACMD_OPTIONS)" && cd $(DATA_DIR) && \
	    java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/splitter/splitter.jar \
	        --max-threads=16 \
	    	--geonames-file=$(CITY) \
		--no-trim \
		--precomp-sea=$(SEA_DIR) \
	        --keep-complete=true \
		--mapid=$(MAPID)0001 \
		--max-areas=4096 \
		--max-nodes=800000 \
		--search-limit=1000000000 \
		--output=o5m \
		--output-dir=$(DATA_DIR) \
		$(PBF)
	touch $@
