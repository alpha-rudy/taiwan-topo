# base (0x2000) + region x lang x style
# where, ...
# - 1st hex, dem    -> moi(1), srtm(2)
# - 2nd hex, region -> taiwan(0), taipei(1), kyushu(2), Beibeiji(3)
# - 3rd hex, lang   -> en(0), zh(1),
# - 4th hex, style  -> jing(0), outdoor(1), contrast_outdoor(2), bw(3)

# target SUITE, no default
ifeq ($(SUITE),yushan)
REGION := Yushan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = ele_taiwan_100_500_1000_moi_zls.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := YushanNationalPark.poly
DEM_NAME := MOI

else ifeq ($(SUITE),taiwan)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = ele_taiwan_100_500_1000_moi_zls.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taiwan.poly
DEM_NAME := MOI

else ifeq ($(SUITE),beibeiji)
REGION := Beibeiji
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = ele_taiwan_100_500_1000_moi_zls.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Beibeiji.poly
DEM_NAME := MOI

else ifeq ($(SUITE),taipei)
REGION := Taipei
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
ELEVATION_MARKER_FILE = ele_taiwan_100_500_1000_moi_zls.osm.pbf
EXTRACT_FILE := taiwan-latest
POLY_FILE := Taipei.poly
DEM_NAME := MOI

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

endif

# auto variables
VERSION := $(shell date +%Y.%m.%d)
MAPID_LO_HEX := $(shell printf '%x' $(MAPID) | cut -c3-4)
MAPID_HI_HEX := $(shell printf '%x' $(MAPID) | cut -c1-2)

NAME_LONG := $(DEM_NAME).OSM.$(STYLE_NAME) - $(REGION) TOPO v$(VERSION) (by Rudy)
NAME_SHORT := $(DEM_NAME).OSM.$(STYLE_NAME) - $(REGION) TOPO v$(VERSION) (by Rudy)
NAME_WORD := $(DEM_NAME)_$(REGION)_TOPO_$(STYLE_NAME)
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy

# finetune options
JAVACMD_OPTIONS := -Xmx48G -server

# directory variables
ROOT_DIR := $(shell pwd)
TOOLS_DIR := $(ROOT_DIR)/tools
SEA_DIR := $(ROOT_DIR)/sea
BOUNDS_DIR := $(ROOT_DIR)/bounds
CITIES_DIR := $(ROOT_DIR)/cities
POLIES_DIR := $(ROOT_DIR)/polies
WORKS_DIR := $(ROOT_DIR)/work
BUILD_DIR := $(ROOT_DIR)/install
ELEVATIONS_DIR := $(WORKS_DIR)/osm_elevations
EXTRACT_DIR := $(WORKS_DIR)/extracts
DATA_DIR := $(WORKS_DIR)/$(REGION)/data$(MAPID)
MAP_DIR := $(WORKS_DIR)/$(REGION)/$(NAME_WORD)

ELEVATION := $(ELEVATIONS_DIR)/$(ELEVATION_FILE)
ELEVATION_MARKER := $(ELEVATIONS_DIR)/$(ELEVATION_MARKER_FILE)
EXTRACT := $(EXTRACT_DIR)/$(EXTRACT_FILE)
CITY := $(CITIES_DIR)/TW.zip
TILES := $(DATA_DIR)/.done
MAP := $(MAP_DIR)/.done
PBF := $(BUILD_DIR)/$(REGION).osm.pbf
TYP_FILE := $(ROOT_DIR)/TYPs/$(TYP).txt
STYLE_DIR := $(ROOT_DIR)/styles/$(STYLE)
TAG_MAPPING := $(ROOT_DIR)/tag-mapping.xml

DEM_FIX := $(shell echo $(DEM_NAME) | tr A-Z a-z)

GMAPSUPP := $(BUILD_DIR)/gmapsupp_$(REGION)_$(DEM_FIX)_$(LANG)_$(STYLE_NAME).img
GMAPSUPP_ZIP := $(GMAPSUPP).zip
GMAP := $(BUILD_DIR)/$(REGION)_$(DEM_FIX)_$(LANG)_$(STYLE_NAME).gmap.zip
NSIS := $(BUILD_DIR)/Install_$(NAME_WORD).exe
MAPSFORGE := $(BUILD_DIR)/$(NAME_MAPSFORGE).map
MAPSFORGE_ZIP := $(MAPSFORGE).zip
MAPSFORGE_STYLE := $(BUILD_DIR)/$(NAME_MAPSFORGE)_style.zip
MAPSFORGE_PBF := $(BUILD_DIR)/$(REGION)_zls.osm.pbf
LOCUS_STYLE := $(BUILD_DIR)/$(NAME_MAPSFORGE)_locus_style.zip
LICENSE := $(BUILD_DIR)/taiwan_topo.html

ifeq ($(MAPID),)
TARGETS := $(LICENSE) $(MAPSFORGE) $(MAPSFORGE_ZIP) $(MAPSFORGE_STYLE) $(LOCUS_STYLE)
else
TARGETS := $(LICENSE) $(GMAPSUPP) $(GMAPSUPP_ZIP) $(GMAP) $(NSIS)
endif

ifeq ($(shell uname),Darwin)
MD5_CMD := md5 -q $$EXAM_FILE
JMC_CMD := jmc/osx/jmc_cli
else
MD5_CMD := md5sum $$EXAM_FILE | cut -d' ' -f1
JMC_CMD := jmc/linux/jmc_cli
endif

all: $(TARGETS)

clean:
	[ -n "$(TARGETS)" ]
	[ -n "$(MAP_DIR)" ]
	-rm -rf $(TARGETS)
	-rm -rf $(MAP_DIR)

distclean:
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(WORKS_DIR)" ]
	-rm -rf $(BUILD_DIR)
	-rm -rf $(WORKS_DIR)

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
	cat taiwan_topo.md | sed -e "s|__version__|$(VERSION)|g" | \
	    markdown -f +autolink > $(BUILD_DIR)/taiwan_topo.article
	cat github_flavor.html | sed "/__article_body__/ r $(BUILD_DIR)/taiwan_topo.article" > $@

.PHONY: nsis
nsis: $(NSIS)
$(NSIS): $(MAP)
	[ -n "$(MAPID)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cd $(MAP_DIR) && \
		rm -rf $@ && \
		for i in $(shell cd $(MAP_DIR); ls $(MAPID)*.img); do \
			echo "  CopyFiles \"\$$MyTempDir\\$$i\" \"\$$INSTDIR\\$$i\"  "; \
			echo "  Delete \"\$$MyTempDir\\$$i\"  "; \
		done > copy_tiles.txt && \
		for i in $(shell cd $(MAP_DIR); ls $(MAPID)*.img); do \
			echo "  Delete \"\$$INSTDIR\\$$i\"  "; \
		done > delete_tiles.txt && \
		cat $(ROOT_DIR)/makensis.cfg | sed \
			-e "s|__root_dir__|$(ROOT_DIR)|g" \
			-e "s|__name_word__|$(NAME_WORD)|g" \
			-e "s|__version__|$(VERSION)|g" \
			-e "s|__mapid_lo_hex__|$(MAPID_LO_HEX)|g" \
			-e "s|__mapid_hi_hex__|$(MAPID_HI_HEX)|g" \
			-e "s|__mapid__|$(MAPID)|g" > $(NAME_WORD).nsi && \
		sed "/__copy_tiles__/ r copy_tiles.txt" -i $(NAME_WORD).nsi && \
		sed "/__delete_tiles__/ r delete_tiles.txt" -i $(NAME_WORD).nsi && \
		zip -r "$(NAME_WORD)_InstallFiles.zip" $(MAPID)*.img $(MAPID).TYP $(NAME_WORD){.img,_mdr.img,.tdb,.mdx} && \
		cat $(ROOT_DIR)/taiwan_topo.md | sed \
			-e "s|__version__|$(VERSION)|g" | iconv -f UTF-8 -t BIG-5//TRANSLIT -o readme.txt && \
		cp $(ROOT_DIR)/nsis/{Install.bmp,Deinstall.bmp} . && \
		makensis $(NAME_WORD).nsi
	cp "$(MAP_DIR)/Install_$(NAME_WORD).exe" $@

.PHONY: gmap
gmap: $(GMAP)
$(GMAP): $(MAP)
	[ -n "$(MAPID)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cd $(MAP_DIR) && \
	    rm -rf $@ && \
	    cat $(ROOT_DIR)/jmc_cli.cfg | sed \
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
	        --license-file=$(ROOT_DIR)/license.txt \
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

$(MAP): $(TILES) $(TYP_FILE) $(STYLE_DIR)
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
	    cat $(ROOT_DIR)/mkgmap.cfg | sed \
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
	    java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
	    	--max-jobs=8 \
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
	mkdir -p $(ELEVATIONS_DIR)
	cd $(ELEVATIONS_DIR) && \
	    curl -k $(ELEVATIONS_URL)/$(ELEVATION_MARKER_FILE) -o $(ELEVATION_MARKER_FILE) && \
	    curl -k $(ELEVATIONS_URL)/$(ELEVATION_MARKER_FILE).md5 -o $(ELEVATION_MARKER_FILE).md5 && \
	    EXAM_FILE=$@; [ "$$($(MD5_CMD))" == "$$(cat $(ELEVATION_MARKER_FILE).md5 | cut -d' ' -f1)" ] || \
	    	( rm -rf $@ && false )

EXTRACT_URL := http://download.geofabrik.de/asia
$(EXTRACT).osm:
	[ -n "$(REGION)" ]
	mkdir -p $(EXTRACT_DIR)
	cd $(EXTRACT_DIR) && \
	    curl $(EXTRACT_URL)/$(EXTRACT_FILE).osm.bz2 -o $(EXTRACT_FILE).osm.bz2 && \
	    curl $(EXTRACT_URL)/$(EXTRACT_FILE).osm.bz2.md5 -o $(EXTRACT_FILE).osm.bz2.md5 && \
	    EXAM_FILE=$(EXTRACT_FILE).osm.bz2; [ "$$($(MD5_CMD))" == "$$(cat $(EXTRACT_FILE).osm.bz2.md5 | cut -d' ' -f1)" ] && \
	    bzip2 -df $(EXTRACT_FILE).osm.bz2 || \
	        ( rm -rf $(EXTRACT_FILE).osm.bz2 && false )

$(EXTRACT).osm.pbf: $(EXTRACT).osm
	[ -n "$(REGION)" ]
	mkdir -p $(EXTRACT_DIR)
	cd $(EXTRACT_DIR) && \
	    cat $(EXTRACT_FILE).osm | osmconvert - -o=$@

$(EXTRACT)-sed.osm.pbf: $(EXTRACT).osm
	[ -n "$(REGION)" ]
	mkdir -p $(EXTRACT_DIR)
	cd $(EXTRACT_DIR) && \
	    cat $(EXTRACT_FILE).osm | sed -e 's/百岳#.*"/百岳"/g' | osmconvert - -o=$@

# OSMOSIS_OPTS
ifneq (,$(strip $(POLY_FILE)))
    OSMOSIS_OPTS := $(strip $(OSMOSIS_OPTS) --bounding-polygon file="$(POLIES_DIR)/$(POLY_FILE)" completeWays=no completeRelations=no cascadingRelations=no clipIncompleteEntities=true)
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
		--read-pbf $(ELEVATION) \
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
	mkdir -p $(BUILD_DIR)
	cp -a styles/mapsforge_style $(BUILD_DIR)
	cat styles/mapsforge_style/MOI_OSM.xml | \
	    sed -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/mapsforge_style/MOI_OSM.xml
	cd $(BUILD_DIR)/mapsforge_style && zip -r $@ *

.PHONY: locus_style $(LOCUS_STYLE)
locus_style: $(LOCUS_STYLE)
$(LOCUS_STYLE):
	[ -n "$(BUILD_DIR)" ]
	[ -n "$(REGION)" ]
	-rm -rf $@
	-rm -rf $(BUILD_DIR)/MOI_OSM_Taiwan_TOPO_Rudy_style
	mkdir -p $(BUILD_DIR)
	cp -a styles/locus_style $(BUILD_DIR)/MOI_OSM_Taiwan_TOPO_Rudy_style
	cat styles/locus_style/MOI_OSM.xml | \
	    sed -e "s/__version__/$(VERSION)/g" > $(BUILD_DIR)/MOI_OSM_Taiwan_TOPO_Rudy_style/MOI_OSM.xml
	cd $(BUILD_DIR) && zip -r $@ MOI_OSM_Taiwan_TOPO_Rudy_style/

$(MAPSFORGE_ZIP): $(MAPSFORGE)
	[ -d "$(BUILD_DIR)" ]
	[ -f "$(MAPSFORGE)" ]
	-rm -rf $@
	cd $(BUILD_DIR) && zip -r $@ $(shell basename $(MAPSFORGE))

.PHONY: mapsforge
mapsforge: $(MAPSFORGE)
$(MAPSFORGE): $(MAPSFORGE_PBF) $(TAG_MAPPING)
	[ -n "$(REGION)" ]
	mkdir -p $(BUILD_DIR)
	export JAVACMD_OPTIONS="-Xmx48G -server" && \
	    sh $(TOOLS_DIR)/osmosis/bin/osmosis \
		--read-pbf "$(MAPSFORGE_PBF)" \
		--buffer --mapfile-writer \
		    $(MF_WRITER_OPTS) \
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
	    	--max-threads=4 \
	    	--geonames-file=$(CITY) \
		--no-trim \
		--precomp-sea=$(SEA_DIR) \
	        --keep-complete=true \
		--mapid=$(MAPID)0001 \
		--max-areas=4096 \
		--max-nodes=800000 \
		--search-limit=1000000000 \
		--output=xml \
		--output-dir=$(DATA_DIR) \
		$(PBF)
	touch $@
