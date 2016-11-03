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
EXTRACT_FILE := taiwan-latest.osm.pbf
POLY_FILE := YushanNationalPark.poly
DEM_NAME := MOI

else ifeq ($(SUITE),taiwan)
REGION := Taiwan
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest.osm.pbf
POLY_FILE := Taiwan.poly
DEM_NAME := MOI

else ifeq ($(SUITE),beibeiji)
REGION := Beibeiji
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest.osm.pbf
POLY_FILE := Beibeiji.poly
DEM_NAME := MOI

else ifeq ($(SUITE),taipei)
REGION := Taipei
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest.osm.pbf
POLY_FILE := Taipei.poly
DEM_NAME := MOI

else ifeq ($(SUITE),beibeiji_bw)
REGION := Beibeiji
LANG := zh
CODE_PAGE := 950
ELEVATION_FILE = ele_taiwan_10_100_500_moi.osm.pbf
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := taiwan-latest.osm.pbf
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
EXTRACT_FILE := japan-latest.osm.pbf
POLY_FILE := Kyushu.poly
TYP := bw
STYLE := swisspopo
STYLE_NAME := bw
DEM_NAME := SRTM3
MAPID := $(shell printf %d 0x2313)

else 
    $(error Error: SUITE not specified. Please specify SUITE=[taiwan|taipei|beibeiji]_[jing|outdoor|outdoorc])
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
JAVACMD_OPTIONS := -Xmx4G

# directory variables
ROOT_DIR := $(shell pwd)
TOOLS_DIR := $(ROOT_DIR)/tools
SEA_DIR := $(ROOT_DIR)/sea
BOUNDS_DIR := $(ROOT_DIR)/bounds
CITIES_DIR := $(ROOT_DIR)/cities
POLIES_DIR := $(ROOT_DIR)/polies
ELEVATIONS_DIR := $(ROOT_DIR)/osm_elevations
EXTRACT_DIR := $(ROOT_DIR)/work/extracts
DATA_DIR := $(ROOT_DIR)/work/$(REGION)/data$(MAPID)
MAP_DIR := $(ROOT_DIR)/work/$(REGION)/$(NAME_WORD)
BUILD_DIR := $(ROOT_DIR)/install

ELEVATION := $(ELEVATIONS_DIR)/$(ELEVATION_FILE)
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
GMAP := $(BUILD_DIR)/$(REGION)_$(DEM_FIX)_$(LANG)_$(STYLE_NAME).gmap.zip
NSIS := $(BUILD_DIR)/Install_$(NAME_WORD).exe
MAPSFORGE := $(BUILD_DIR)/$(NAME_MAPSFORGE).map
MAPSFORGE_STYLE := $(BUILD_DIR)/$(NAME_MAPSFORGE)_style.zip
LICENSE := $(BUILD_DIR)/taiwan_topo.html

ifeq ($(MAPID),)
TARGETS := $(LICENSE) $(MAPSFORGE) $(MAPSFORGE_STYLE)
else
TARGETS := $(LICENSE) $(GMAPSUPP) $(GMAP) $(NSIS)
endif

ifeq ($(shell uname),Darwin)
MD5_CMD := md5 -q $(EXTRACT)
JMC_CMD := jmc/osx/jmc_cli
else
MD5_CMD := md5sum $(EXTRACT) | cut -d' ' -f1
JMC_CMD := jmc/linux/jmc_cli
endif

all: $(TARGETS)

clean:
	-rm -rf $(TARGETS)
	-rm -rf $(MAP_DIR)

distclean: clean
	-rm -rf $(DATA_DIR)
	-rm -rf $(PBF)
	-rm -rf $(EXTRACT)

.PHONY: install
install: $(LICENSE) $(GMAPSUPP)
	[ -n "$(INSTALL_DIR)" ]
	[ -d "$(INSTALL_DIR)" ]
	cp -r $(GMAPSUPP) $(INSTALL_DIR)
	cp $(LICENSE) $(INSTALL_DIR)/taiwan_topo.html

drop: all
	[ -n "$(INSTALL_DIR)" ]
	[ -d "$(INSTALL_DIR)" ]
	cp -r $(TARGETS) $(INSTALL_DIR)

.PHONY: license $(LICENSE)
license: $(LICENSE)
$(LICENSE):
	[ -n "$(VERSION)" ]
	mkdir -p $(BUILD_DIR)
	cat taiwan_topo.html | sed \
	    -e "s|__version__|$(VERSION)|g" > $(BUILD_DIR)/taiwan_topo.html

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
		cat $(ROOT_DIR)/taiwan_topo.txt | sed \
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

ifeq ($(LANG),zh) 
NTL := name,name:zh,name:en
MAPSFORGE_NTL := zh,en
else ifeq ($(LANG),en)
NTL := name:en,name:zh,name
MAPSFORGE_NTL := en
else
    $(error Error: LANG not specified. something wrong at SUITE handlation)
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
	    	--max-jobs=4 \
	    	-c mkgmap.cfg \
		--check-styles
	touch $(MAP)

$(EXTRACT):
	[ -n "$(REGION)" ]
	mkdir -p $(EXTRACT_DIR)
	cd $(EXTRACT_DIR) && \
	    curl http://download.geofabrik.de/asia/$(EXTRACT_FILE) -o $(EXTRACT_FILE) && \
	    curl http://download.geofabrik.de/asia/$(EXTRACT_FILE).md5 -o $(EXTRACT_FILE).md5 && \
	    [ "$$($(MD5_CMD))" == "$$(cat $(EXTRACT_FILE).md5 | cut -d' ' -f1)" ] || \
	    	( rm -rf $@ && false )

# OSMOSIS_OPTS
ifneq (,$(strip $(POLY_FILE)))
    OSMOSIS_OPTS := $(strip $(OSMOSIS_OPTS) --bounding-polygon file="$(POLIES_DIR)/$(POLY_FILE)" completeWays=no completeRelations=no cascadingRelations=no clipIncompleteEntities=true)
endif

$(PBF): $(EXTRACT) $(ELEVATION)
	[ -n "$(REGION)" ]
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	export JAVACMD_OPTIONS=$(JAVACMD_OPTIONS) && \
	    sh $(TOOLS_DIR)/osmosis/bin/osmosis \
		--read-pbf $(EXTRACT) \
		--read-pbf $(ELEVATION) \
		--merge \
		$(OSMOSIS_OPTS) \
		--write-pbf $(PBF) \
		omitmetadata=true
.PHONY: mapsforge_style
mapsforge_style: $(MAPSFORGE_STYLE)
$(MAPSFORGE_STYLE): styles/MOI_OSM_style/MOI_OSM.xml
	-rm -rf $@
	mkdir -p $(BUILD_DIR)
	cd styles/MOI_OSM_style && \
	   zip -r $@ *

.PHONY: mapsforge
mapsforge: $(MAPSFORGE)
$(MAPSFORGE): $(PBF) $(TAG_MAPPING)
	[ -n "$(REGION)" ]
	mkdir -p $(BUILD_DIR)
	export JAVACMD_OPTIONS=-Xmx64G && \
	    sh $(TOOLS_DIR)/osmosis/bin/osmosis \
		--read-pbf "$(PBF)" \
		--mapfile-writer \
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
	export JAVACMD_OPTIONS=$(JAVACMD_OPTIONS) && cd $(DATA_DIR) && \
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
