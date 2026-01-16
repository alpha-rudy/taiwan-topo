# macros.mk - Reusable build macros for taiwan-topo
#
# This file contains parameterized macros for common build patterns:
# - Style builds (STYLE_SIMPLE, STYLE_WITH_DOCS, STYLE_LOCUS, STYLE_TRANSFORM)
# - Map generation (MAP_BUILD)
# - ZIP packaging (ZIP_PACKAGE)
# - POI database generation (POI_BUILD)

#==============================================================================
# Style Build Macros
#==============================================================================
# Helper for passing commas in macro arguments
COMMA := ,

# These macros define reusable patterns for building style ZIP files.
# Usage: $(eval $(call STYLE_SIMPLE,target_name,zip_file,src_dir,build_subdir,xml_name))
# Usage: $(eval $(call STYLE_WITH_DOCS,target_name,zip_file,src_dir,build_subdir,xml_name,pdf_name,png_name))
# Usage: $(eval $(call STYLE_LOCUS,target_name,zip_file,src_dir,build_subdir,xml_name,pdf_name,png_name))

# STYLE_SIMPLE: Basic style without documentation files
# $1 = target name (e.g., bn_style)
# $2 = zip file variable (e.g., BN_STYLE)
# $3 = source directory (e.g., styles/mapsforge_bn)
# $4 = build subdirectory name (e.g., mapsforge_bn)
# $5 = XML file name (e.g., MOI_OSM_BN.xml)
define STYLE_SIMPLE
$1_VAR := $$(BUILD_DIR)/$2.zip

.PHONY: $1 $$($1_VAR)
$1: $$($1_VAR)
$$($1_VAR):
	date +'DS: %H:%M:%S $$(shell basename $$@)'
	[ -n "$$(BUILD_DIR)" ]
	-rm -f $$@
	-rm -rf $$(BUILD_DIR)/$4
	mkdir -p $$(BUILD_DIR)
	cp -a $3 $$(BUILD_DIR)/$4
	cat $3/$5 | \
		$$(SED_CMD) -e "s/__version__/$$(VERSION)/g" > $$(BUILD_DIR)/$4/$5
	cd $$(BUILD_DIR)/$4 && $$(ZIP_CMD) $$@ *
endef

# STYLE_WITH_DOCS: Style with PDF and PNG documentation
# $1 = target name (e.g., mapsforge_style)
# $2 = zip file variable (e.g., MOI_OSM_Taiwan_TOPO_Rudy_style)
# $3 = source directory (e.g., styles/mapsforge_style)
# $4 = build subdirectory name (e.g., mapsforge_style)
# $5 = XML file name (e.g., MOI_OSM.xml)
# $6 = PDF output name (e.g., MOI_OSM.pdf)
# $7 = PNG output name (e.g., MOI_OSM.png)
define STYLE_WITH_DOCS
$1_VAR := $$(BUILD_DIR)/$2.zip

.PHONY: $1 $$($1_VAR)
$1: $$($1_VAR)
$$($1_VAR):
	date +'DS: %H:%M:%S $$(shell basename $$@)'
	[ -n "$$(BUILD_DIR)" ]
	-rm -f $$@
	-rm -rf $$(BUILD_DIR)/$4
	mkdir -p $$(BUILD_DIR)
	cp -a $3 $$(BUILD_DIR)/$4
	cat $3/$5 | \
		$$(SED_CMD) -e "s/__version__/$$(VERSION)/g" > $$(BUILD_DIR)/$4/$5
	cp docs/legend_V1R3.pdf $$(BUILD_DIR)/$4/$6
	cp docs/MOI_OSM.png $$(BUILD_DIR)/$4/$7
	cd $$(BUILD_DIR)/$4 && $$(ZIP_CMD) $$@ *
endef

# STYLE_LOCUS: Locus-style packaging (zip contains folder/)
# $1 = target name (e.g., locus_style)
# $2 = zip file variable (e.g., MOI_OSM_Taiwan_TOPO_Rudy_locus_style)
# $3 = source directory (e.g., styles/locus_style)
# $4 = build subdirectory name / install name (e.g., MOI_OSM_Taiwan_TOPO_Rudy_style)
# $5 = XML file name (e.g., MOI_OSM.xml)
# $6 = PDF output name (e.g., MOI_OSM.pdf)
# $7 = PNG output name (e.g., MOI_OSM.png)
define STYLE_LOCUS
$1_VAR := $$(BUILD_DIR)/$2.zip

.PHONY: $1 $$($1_VAR)
$1: $$($1_VAR)
$$($1_VAR):
	date +'DS: %H:%M:%S $$(shell basename $$@)'
	[ -n "$$(BUILD_DIR)" ]
	-rm -f $$@
	-rm -rf $$(BUILD_DIR)/$4
	mkdir -p $$(BUILD_DIR)
	cp -a $3 $$(BUILD_DIR)/$4
	cat $3/$5 | \
		$$(SED_CMD) -e "s/__version__/$$(VERSION)/g" > $$(BUILD_DIR)/$4/$5
	cp docs/legend_V1R3.pdf $$(BUILD_DIR)/$4/$6
	cp docs/MOI_OSM.png $$(BUILD_DIR)/$4/$7
	cd $$(BUILD_DIR) && $$(ZIP_CMD) $$@ $4/
endef

# STYLE_TRANSFORM: Style with custom sed transformations and resource renaming
# $1 = target name (e.g., hs_style)
# $2 = zip file variable (e.g., MOI_OSM_Taiwan_TOPO_Rudy_hs_style)
# $3 = build subdirectory name (e.g., mapsforge_hs)
# $4 = resource rename suffix (e.g., moiosmhs_res)
# $5 = output XML name (e.g., MOI_OSM.xml)
# $6 = additional sed commands (e.g., empty or -e "s,<!-- hillshading -->,<hillshading />,g")
# $7 = PDF output name (optional, e.g., MOI_OSM.pdf)
# $8 = PNG output name (optional, e.g., MOI_OSM.png)
define STYLE_TRANSFORM
$1_VAR := $$(BUILD_DIR)/$2.zip

.PHONY: $1 $$($1_VAR)
$1: $$($1_VAR)
$$($1_VAR):
	date +'DS: %H:%M:%S $$(shell basename $$@)'
	[ -n "$$(BUILD_DIR)" ]
	-rm -f $$@
	-rm -rf $$(BUILD_DIR)/$3
	mkdir -p $$(BUILD_DIR)/$3
	cp -a styles/mapsforge_style/License.txt $$(BUILD_DIR)/$3
	cp -a styles/mapsforge_style/moiosm_res $$(BUILD_DIR)/$3/$4
	cat styles/mapsforge_style/MOI_OSM.xml | \
		$$(SED_CMD) \
			-e "s/__version__/$$(VERSION)/g" \
			-e "s/file:moiosm_res/file:$4/g" \
			-e "s,file:/moiosm_res,file:/$4,g" \
			$6 \
		> $$(BUILD_DIR)/$3/$5
	$(if $7,cp docs/legend_V1R3.pdf $$(BUILD_DIR)/$3/$7)
	$(if $8,cp docs/MOI_OSM.png $$(BUILD_DIR)/$3/$8)
	cd $$(BUILD_DIR)/$3 && $$(ZIP_CMD) $$@ *
endef


#==============================================================================
# Map Build Macros
#==============================================================================
# MAP_BUILD: Parameterized macro for Garmin map generation
# This macro consolidates the near-identical map_hidem, map_lodem, map_nodem_hr,
# map_nodem_lr targets into a single reusable template.
#
# Parameters:
# $1 = target name (e.g., map_hidem)
# $2 = done file variable (e.g., MAP_HIDEM)
# $3 = output directory variable (e.g., MAP_HIDEM_DIR)
# $4 = style directory variable (e.g., HR_STYLE_DIR)
# $5 = style name variable (e.g., HR_STYLE)
# $6 = DEM config file (e.g., gmapdem_camp.cfg, gmapdem.cfg, or empty for no DEM)
# $7 = extra dependencies (e.g., $(GMAPDEM) or empty)
#
define MAP_BUILD
.PHONY: $1
$1: $2
$2: $$(TILES) $$(TYP_FILE) $4 $7
	date +'DS: %H:%M:%S $$(shell basename $$@)'
	[ -n "$$(MAPID)" ]
	rm -rf $3
	mkdir -p $3
	cd $3 && \
		cat $$(TYP_FILE) | $$(SED_CMD) \
			-e "s|ä|a|g" \
			-e "s|é|e|g" \
			-e "s|ß|b|g" \
			-e "s|ü|u|g" \
			-e "s|ö|o|g" \
			-e "s|FID=.*|FID=$$(MAPID)|g" \
			-e "s|CodePage=.*|CodePage=$$(CODE_PAGE)|g" > $$(TYP).txt && \
		java $$(JAVACMD_OPTIONS) -jar $$(MKGMAP_JAR) \
			--code-page=$$(CODE_PAGE) \
			--product-id=1 \
			--family-id=$$(MAPID) \
			$$(TYP).txt
	cd $3 && \
		cp $$(TYP).typ $$(MAPID).TYP && \
		mkdir $3/style && \
		cp -a $4 $3/style/$5 && \
		cp $$(ROOT_DIR)/styles/style-translations $3/ && \
		cat $$(ROOT_DIR)/mkgmaps/mkgmap.cfg | $$(SED_CMD) \
			-e "s|__root_dir__|$$(ROOT_DIR)|g" \
			-e "s|__map_dir__|$3|g" \
			-e "s|__version__|$$(VERSION)|g" \
			-e "s|__style__|$5|g" \
			-e "s|__name_tag_list__|$$(NTL)|g" \
			-e "s|__code_page__|$$(CODE_PAGE)|g" \
			-e "s|__name_long__|$$(NAME_LONG)|g" \
			-e "s|__name_short__|$$(NAME_SHORT)|g" \
			-e "s|__name_word__|$$(NAME_WORD)|g" \
			-e "s|__mapid__|$$(MAPID)|g" > mkgmap.cfg && \
		cat $$(TILES_DIR)/template.args | $$(SED_CMD) \
			-e "s|input-file: \(.*\)|input-file: $$(TILES_DIR)/\\1|g" >> mkgmap.cfg && \
		$(if $6,ln -s $$(GMAPDEM) ./moi-hgt.zip && $$(SED_CMD) "/__dem_section__/ r $$(ROOT_DIR)/mkgmaps/$6" -i mkgmap.cfg &&) \
		java $$(JAVACMD_OPTIONS) -jar $$(MKGMAP_JAR) \
			--code-page=$$(CODE_PAGE) \
			--max-jobs=$$(MKGMAP_JOBS) \
			-c mkgmap.cfg \
			--check-styles
	touch $2
endef


#==============================================================================
# ZIP Package Macros
#==============================================================================
# ZIP_PACKAGE: Generic macro for creating ZIP archives from build artifacts
#
# Parameters:
# $1 = target name (e.g., poi_zip)
# $2 = zip file path (e.g., $(POI_ZIP))
# $3 = dependencies (e.g., $(POI))
# $4 = files to zip - space-separated basenames (e.g., $(POI) or $(MAPSFORGE) $(POI))
#
define ZIP_PACKAGE
.PHONY: $1
$1: $2
$2: $3
	date +'DS: %H:%M:%S $$(shell basename $$@)'
	[ -d "$$(BUILD_DIR)" ]
	-rm -rf $$@
	set -e; cd $$(BUILD_DIR) && $$(ZIP_CMD) $$@ $(foreach f,$4,$$(shell basename $f))
endef


#==============================================================================
# POI Build Macros
#==============================================================================
# POI_BUILD: Parameterized macro for POI database generation using osmosis poi-writer
#
# Parameters:
# $1 = target name (e.g., poi)
# $2 = output file (e.g., $(POI))
# $3 = input file (e.g., $(POI_EXTRACT).osm.pbf)
# $4 = dependencies (e.g., $(POI_EXTRACT).osm.pbf $(POI_MAPPING))
# $5 = mapping file (e.g., $(POI_MAPPING))
# $6 = osmosis command (e.g., $(OSMOSIS_CMD) or $(OSMOSIS_POI_V2_CMD))
# $7 = extra read options (e.g., $(OSMOSIS_BOUNDING) or empty)
# $8 = java environment prefix (e.g., empty or JAVA_HOME=... PATH=...)
#
define POI_BUILD
.PHONY: $1
$1: $2
$2: $4
	date +'DS: %H:%M:%S $$(shell basename $$@)'
	mkdir -p $$(BUILD_DIR)
	-rm -rf $$@
	export JAVACMD_OPTIONS="-server" && \
		$8 sh $6 \
			--rb file="$3" \
			$7 \
			--poi-writer \
				all-tags=true \
				geo-tags=true \
				names=false \
				ways=true \
				tag-conf-file="$5" \
				comment="$$(VERSION)  /  (c) Map data: OSM contributors" \
				file="$$@"
endef

#==============================================================================
# Suite Build Macro
#==============================================================================
# Macro to generate suite targets that run multiple suites in sequence with error handling
# Parameters:
#   1: region name (e.g., fujisan, kumano)
#   2: suite list variable name (e.g., FUJISAN_SUITES)
#   3: install directory path
#   4: suite name for install target (usually same as region, e.g., fujisan)
define SUITE_BUILD
.PHONY: $(1)_suites
$(1)_suites:
	set -e; $$(foreach suite,$$($(2)),$(MAKE_CMD) BUILD_DIR=$$(ROOT_DIR)/build-$(1) SUITE=$$(suite) all;)
	$$(MAKE_CMD) BUILD_DIR=$$(ROOT_DIR)/build-$(1) INSTALL_DIR=$(3) SUITE=$(4) install
endef
