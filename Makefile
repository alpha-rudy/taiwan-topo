TARGETS := gmapsupp_taiwan_zh_rudy.img taiwan_zh_rudy.gmap

INSTALL_DIR := /Volumes/GARMIN/Garmin

MAPID := 6158
VERSION := 2016.07
TYP := jing
STYLE := jing
CODE_PAGE := 950

NAME_LONG := Taiwan TOPO (Release $(VERSION)) by Rudy
NAME_SHORT := Taiwan TOPO $(VERSION) by Rudy
NAME_WORD := Taiwan_TOPO_Rudy

# finetune options
JAVACMD_OPTIONS := -Xmx4096M

# auto variables
ROOT_DIR := $(shell pwd)
TOOLS_DIR := $(ROOT_DIR)/tools
SEA_DIR := $(ROOT_DIR)/sea
BOUNDS_DIR := $(ROOT_DIR)/bounds
CITIES_DIR := $(ROOT_DIR)/cities
EXTRACTS_DIR := $(ROOT_DIR)/osm_extracts
ELEVATIONS_DIR := $(ROOT_DIR)/osm_elevations
WORK_DIR := $(ROOT_DIR)/work/osm
WORK_LANG_DIR := $(ROOT_DIR)/work/zh

EXTRACT := $(EXTRACTS_DIR)/taiwan-latest.osm.pbf
ELEVATION := $(ELEVATIONS_DIR)/ele_taiwan_10_50_100_view1,srtm1,view3,srtm3.osm.pbf
CITY := $(CITIES_DIR)/TW.zip
WORK := $(WORK_DIR)/.done
WORK_LANG := $(WORK_LANG_DIR)/.done

all: $(TARGETS)

clean:
	-rm -rf $(TARGETS)
	-rm -rf $(WORK_LANG_DIR)

distclean: clean
	-rm -rf $(WORK_DIR)

install: all
	cp gmapsupp_taiwan_zh_rudy.img $(INSTALL_DIR)/

taiwan_zh_rudy.gmap: $(WORK_LANG)
	cd $(WORK_LANG_DIR) && \
	    rm -rf $@ && \
	    cat $(ROOT_DIR)/jmc_cli.cfg | sed \
	    	-e "s|__work_lang_dir__|$(WORK_LANG_DIR)|g" \
		-e "s|__name_word__|$(NAME_WORD)|g" \
		-e "s|__mapid__|$(MAPID)|g" > jmc_cli.cfg && \
	    $(TOOLS_DIR)/jmc/osx/jmc_cli -v -config="$(WORK_LANG_DIR)/jmc_cli.cfg"
	cp -a "$(WORK_LANG_DIR)/$(NAME_SHORT).gmap" $@

gmapsupp_taiwan_zh_rudy.img: $(WORK_LANG)
	cd $(WORK_LANG_DIR) && \
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
	cp $(WORK_LANG_DIR)/gmapsupp.img $@

$(WORK_LANG): $(WORK)
	rm -rf $(WORK_LANG_DIR)
	mkdir -p $(WORK_LANG_DIR)
	cd $(WORK_LANG_DIR) && \
	    cat $(ROOT_DIR)/TYPs/$(TYP).txt | sed \
	    	-e "s|FID=.*|FID=$(MAPID)|g" \
		-e "s|CodePage=.*|CodePage=$(CODE_PAGE)|g" > $(TYP).txt && \
	    java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
	    	--product-id=1 \
		--family-id=$(MAPID) \
		$(TYP).txt && \
	    cp $(TYP).typ $(MAPID).TYP && \
	    mkdir $(WORK_LANG_DIR)/style && \
	    cp -a $(ROOT_DIR)/styles/$(STYLE) $(WORK_LANG_DIR)/style/$(STYLE) && \
	    cp $(ROOT_DIR)/styles/style-translations $(WORK_LANG_DIR)/ && \
	    cat $(ROOT_DIR)/mkgmap.cfg | sed \
		-e "s|__root_dir__|$(ROOT_DIR)|g" \
		-e "s|__work_lang_dir__|$(WORK_LANG_DIR)|g" \
		-e "s|__version__|$(VERSION)|g" \
		-e "s|__build__|$(VERSION)|g" \
		-e "s|__style__|$(STYLE)|g" \
		-e "s|__code_page__|$(CODE_PAGE)|g" \
		-e "s|__name_long__|$(NAME_LONG)|g" \
		-e "s|__name_short__|$(NAME_SHORT)|g" \
		-e "s|__name_word__|$(NAME_WORD)|g" \
		-e "s|__mapid__|$(MAPID)|g" > mkgmap.cfg && \
	    cat $(WORK_DIR)/template.args | sed \
	    	-e "s|description: \(.*\)|description: \\1 $(VERSION)|g" \
	    	-e "s|input-file: \(.*\)|input-file: $(WORK_DIR)/\\1|g" >> mkgmap.cfg && \
	    java $(JAVACMD_OPTIONS) -jar $(TOOLS_DIR)/mkgmap/mkgmap.jar \
	    	--max-jobs=2 \
	    	-c mkgmap.cfg \
		--check-styles
	touch $(WORK_LANG)

$(WORK): $(EXTRACT) $(ELEVATION)
	rm -rf $(WORK_DIR)
	mkdir -p $(WORK_DIR)
	export JAVACMD_OPTIONS=$(JAVACMD_OPTIONS) && cd $(WORK_DIR) && \
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
		--max-nodes=800000 \
		--output=xml \
		--output-dir=$(WORK_DIR) \
		taiwan.osm.pbf
	touch $(WORK)

notyet:

