# base (0x2000) + region x lang x style
# where, ...
# - region -> taiwan(0), taipei
# - lang   -> en(0), zh(1),
# - style  -> jing(0), small(1), contrast_outdor (2)

# target
ifeq ($(SUITE),jing)
TYP := jing
STYLE := jing
MAPID := $(shell printf %d 0x2010)
else ifeq ($(SUITE),odr)
TYP := outdoor
STYLE := fzk
MAPID := $(shell printf %d 0x2011)
else ifeq ($(SUITE),odc)
TYP := outdoorc
STYLE := swisspopo
MAPID := $(shell printf %d 0x2012)
else 
    $(error Error: SUITE not specified. Please specify SUITE=[jing|outdoor|outdoorc])
endif

LANG := zh
CODE_PAGE := 950

# auto variables
VERSION := $(shell date +%Y.%m)

NAME_LONG := SRTM3.OSM.$(SUITE) - Taiwan TOPO v$(VERSION) (by Rudy)
NAME_SHORT := SRTM3.OSM.$(SUITE) - Taiwan TOPO v$(VERSION) (by Rudy)
NAME_WORD := Taiwan_TOPO_$(SUITE)

# finetune options
JAVACMD_OPTIONS := -Xmx4096M

# directory variables
ROOT_DIR := $(shell pwd)
TOOLS_DIR := $(ROOT_DIR)/tools
SEA_DIR := $(ROOT_DIR)/sea
BOUNDS_DIR := $(ROOT_DIR)/bounds
CITIES_DIR := $(ROOT_DIR)/cities
ELEVATIONS_DIR := $(ROOT_DIR)/osm_elevations
EXTRACT_DIR := $(ROOT_DIR)/work/extracts
DATA_DIR := $(ROOT_DIR)/work/taiwan/data$(MAPID)
MAP_DIR := $(ROOT_DIR)/work/taiwan/$(NAME_WORD)
INSTALL_DIR := $(ROOT_DIR)/install

EXTRACT := $(EXTRACT_DIR)/taiwan-latest.osm.pbf
ELEVATION := $(ELEVATIONS_DIR)/ele_taiwan_10_50_100_view1,srtm1,view3,srtm3.osm.pbf
CITY := $(CITIES_DIR)/TW.zip
DATA := $(DATA_DIR)/.done
MAP := $(MAP_DIR)/.done
GMAP := $(INSTALL_DIR)/taiwan_$(LANG)_$(SUITE).gmap
GMAPSUPP := $(INSTALL_DIR)/gmapsupp_taiwan_$(LANG)_$(SUITE).img

TARGETS := $(GMAPSUPP) $(GMAP)

ifeq ($(shell uname),Darwin)
MD5_CMD := md5 -q taiwan-latest.osm.pbf
JMC_CMD := jmc/osx/jmc_cli
else
MD5_CMD := md5sum taiwan-latest.osm.pbf | cut -d' ' -f1
JMC_CMD := jmc/linux/jmc_cli
endif

all: $(TARGETS)

clean:
	-rm -rf $(TARGETS)
	-rm -rf $(MAP_DIR)

distclean: clean
	-rm -rf $(DATA_DIR)
	-rm -rf $(EXTRACT)

$(GMAP): $(MAP)
	-rm -rf $@
	mkdir -p $(INSTALL_DIR)
	cd $(MAP_DIR) && \
	    rm -rf $@ && \
	    cat $(ROOT_DIR)/jmc_cli.cfg | sed \
	    	-e "s|__map_dir__|$(MAP_DIR)|g" \
		-e "s|__name_word__|$(NAME_WORD)|g" \
		-e "s|__mapid__|$(MAPID)|g" > jmc_cli.cfg && \
	    $(TOOLS_DIR)/$(JMC_CMD) -v -config="$(MAP_DIR)/jmc_cli.cfg"
	cp -a "$(MAP_DIR)/$(NAME_SHORT).gmap" $@

$(GMAPSUPP): $(MAP)
	-rm -rf $@
	mkdir -p $(INSTALL_DIR)
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

$(MAP): $(DATA)
	rm -rf $(MAP_DIR)
	mkdir -p $(MAP_DIR)
	cd $(MAP_DIR) && \
	    cat $(ROOT_DIR)/TYPs/$(TYP).txt | sed \
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
	    cp -a $(ROOT_DIR)/styles/$(STYLE) $(MAP_DIR)/style/$(STYLE) && \
	    cp $(ROOT_DIR)/styles/style-translations $(MAP_DIR)/ && \
	    cat $(ROOT_DIR)/mkgmap.cfg | sed \
		-e "s|__root_dir__|$(ROOT_DIR)|g" \
		-e "s|__map_dir__|$(MAP_DIR)|g" \
		-e "s|__version__|$(VERSION)|g" \
		-e "s|__style__|$(STYLE)|g" \
		-e "s|__code_page__|$(CODE_PAGE)|g" \
		-e "s|__name_long__|$(NAME_LONG)|g" \
		-e "s|__name_short__|$(NAME_SHORT)|g" \
		-e "s|__name_word__|$(NAME_WORD)|g" \
		-e "s|__mapid__|$(MAPID)|g" > mkgmap.cfg && \
	    cat $(DATA_DIR)/template.args | sed \
	    	-e "s|description: \(.*\)|description: \\1 $(VERSION)|g" \
	    	-e "s|input-file: \(.*\)|input-file: $(DATA_DIR)/\\1|g" >> mkgmap.cfg && \
	    java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
	    	--max-jobs=2 \
	    	-c mkgmap.cfg \
		--check-styles
	touch $(MAP)

$(EXTRACT):
	mkdir -p $(EXTRACT_DIR)
	cd $(EXTRACT_DIR) && \
	    curl http://download.geofabrik.de/asia/taiwan-latest.osm.pbf -o taiwan-latest.osm.pbf && \
	    curl http://download.geofabrik.de/asia/taiwan-latest.osm.pbf.md5 -o taiwan-latest.osm.pbf.md5 && \
	    [ "$$($(MD5_CMD))" == "$$(cat taiwan-latest.osm.pbf.md5 | cut -d' ' -f1)" ] || \
	    	( rm -rf $@ && false )

$(DATA): $(EXTRACT) $(ELEVATION)
	rm -rf $(DATA_DIR)
	mkdir -p $(DATA_DIR)
	export JAVACMD_OPTIONS=$(JAVACMD_OPTIONS) && cd $(DATA_DIR) && \
	    sh $(TOOLS_DIR)/osmosis/bin/osmosis \
		--read-pbf $(EXTRACT) \
		--read-pbf $(ELEVATION) \
		--merge \
		--write-pbf taiwan.osm.pbf \
		omitmetadata=true && \
	    java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/splitter/splitter.jar \
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
		taiwan.osm.pbf
	touch $(DATA)
