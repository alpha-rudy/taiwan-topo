#!/usr/bin/env python3
"""
Generate Makefile suite definitions for a new TOPO map region.

This script creates the three suite .mk files for a new region, similar to:
- kumano_suites (Japan)
- annapurna_suites (Nepal)
- fujisan_suites (Japan)
- kashmir_suites (India)

It generates:
1. Base mapsforge suite definition (.mk)
2. Garmin DEM suite definition with native language (.mk)
3. Garmin DEM suite definition with English (.mk)

Usage:
    python3 tools/generate_suite.py \
        --region <RegionName> \
        --region-lower <region_lower> \
        --dem-name AW3D30 \
        --lang <lang_code> \
        --extract-file <country>-latest \
        --left <lon> --right <lon> --bottom <lat> --top <lat> \
        [--code-page <page>] \
        [--mapid-native <hex>] \
        [--mapid-english <hex>]

Example:
    python3 tools/generate_suite.py \\
        --region Everest \\
        --region-lower everest \\
        --dem-name AW3D30 \\
        --lang ne \\
        --extract-file nepal-latest \\
        --left 86.5 --right 87.2 --bottom 27.7 --top 28.2
"""

import os
import click


# MAPID registry - add new regions here to avoid conflicts
MAPID_REGISTRY = {
    # Kumano (Japan)
    "kumano_native": 0x1018,
    "kumano_english": 0x1008,
    # Annapurna (Nepal)
    "annapurna_native": 0x1018,
    "annapurna_english": 0x1008,
    # Fujisan (Japan)
    "fujisan_native": 0x1028,
    "fujisan_english": 0x1048,
    # Kashmir (India)
    "kashmir_native": 0x1028,
    "kashmir_english": 0x1038,
}


def create_base_suite_mk(region, region_lower, dem_name, lang, code_page, extract_file,
                         left, right, bottom, top):
    """Create the base mapsforge suite .mk file."""
    return f"""# Suite: {region_lower} - {region} mapsforge build
ifeq ($(SUITE),{region_lower})
REGION := {region}
DEM_NAME := {dem_name}
LANG := {lang}
CODE_PAGE := {code_page}
ELEVATION_FILE = ele_{region_lower}_10_100_500.pbf
ELEVATION_MIX_FILE = ele_{region_lower}_10_100_500_mix.pbf
EXTRACT_FILE := {extract_file}
BOUNDING_BOX := true
LEFT := {left}
RIGHT := {right}
BOTTOM := {bottom}
TOP := {top}
NAME_MAPSFORGE := $(DEM_NAME)_OSM_$(REGION)_TOPO_Rudy
NAME_CARTO := $(REGION)_carto
HGT := $(ROOT_DIR)/hgt/{region_lower}_hgtmix.zip
GTS_STYLE = $(HS_STYLE)
TOPO_PAGE := {region_lower}_topo
TARGETS := styles mapsforge_zip poi_zip poi_v2_zip locus_poi_zip gts_all carto_all locus_map
endif

# Suite lists for batch builds
{region_lower.upper()}_SUITES := {region_lower} {region_lower}_bc_dem {region_lower}_bc_dem_en
# Instantiate suite targets for each region
$(eval $(call SUITE_BUILD,{region_lower},{region_lower.upper()}_SUITES,$(ROOT_DIR)/install-{region_lower},{region_lower}))
"""


def create_garmin_dem_suite_mk(region, region_lower, dem_name, lang, code_page, extract_file,
                               left, right, bottom, top, mapid):
    """Create a Garmin DEM basecamp suite .mk file."""
    mapid_hex = f"0x{mapid:04x}"
    return f"""# Suite: {region_lower}_bc_dem - {region} basecamp style with DEM
ifeq ($(SUITE),{region_lower}_bc_dem)
REGION := {region}
DEM_NAME := {dem_name}
LANG := {lang}
CODE_PAGE := {code_page}
ELEVATION_FILE = ele_{region_lower}_10_100_500.pbf
EXTRACT_FILE := {extract_file}
BOUNDING_BOX := true
LEFT := {left}
RIGHT := {right}
BOTTOM := {bottom}
TOP := {top}
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/{region_lower}_hgtmix.zip
MAPID := $(shell printf %d {mapid_hex})
TARGETS := gmapsupp_zip gmap nsis
endif
"""


def create_garmin_dem_english_suite_mk(region, region_lower, dem_name, extract_file,
                                       left, right, bottom, top, mapid):
    """Create a Garmin DEM basecamp English suite .mk file."""
    mapid_hex = f"0x{mapid:04x}"
    return f"""# Suite: {region_lower}_bc_dem_en - {region} basecamp style with DEM (English)
ifeq ($(SUITE),{region_lower}_bc_dem_en)
REGION := {region}
DEM_NAME := {dem_name}
LANG := en
CODE_PAGE := 1252
ELEVATION_FILE = ele_{region_lower}_10_100_500.pbf
EXTRACT_FILE := {extract_file}
BOUNDING_BOX := true
LEFT := {left}
RIGHT := {right}
BOTTOM := {bottom}
TOP := {top}
TYP := basecamp
LR_STYLE := swisspopo
HR_STYLE := basecamp
STYLE_NAME := camp3D
GMAPDEM := $(ROOT_DIR)/hgt/{region_lower}_hgtmix.zip
MAPID := $(shell printf %d {mapid_hex})
TARGETS := gmapsupp_zip gmap nsis
endif
"""


def create_documentation_md(region, region_lower):
    """Create a documentation template .md file."""
    return f"""{region} TOPO Map
{'=' * (len(region) + 10)}

AW3D30.OSM - {region} TOPO v__version__

Suitable for offline use on Garmin, Android, and iOS devices.

## Related Resources
* Official website: https://github.com/alpha-rudy/taiwan-topo
* Discussion group: https://www.facebook.com/groups/taiwan.topo
* Development repository: https://github.com/alpha-rudy/taiwan-topo

## Installation

### Locus Map
* Download the complete package: [auto-install link]
* Or use automatic installation from within the app

### Garmin Devices
* Windows: [Install_AW3D30_{region}_TOPO_*.exe]
* macOS: [{region}_*_camp3D.gmap.zip]

### CartoType
* Map: [{region}_carto_map.cpkg]
* Style: [{region}_carto_style.cpkg]
* DEM: [{region}_carto_dem.cpkg]
* All: [{region}_carto_all.cpkg]

## Map Features

* High-resolution topographic data (AW3D30 DEM)
* OpenStreetMap data
* Contour lines (10m, 100m, 500m intervals)
* POI database included
* Multiple styles and themes

## Version History

* v__version__ - Initial release
"""





@click.command()
@click.option('--region', required=True, help='Region name (e.g., Everest)')
@click.option('--region-lower', required=True, help='Region name lowercase (e.g., everest)')
@click.option('--dem-name', default='AW3D30', help='DEM name (default: AW3D30)')
@click.option('--lang', required=True, help='Language code (e.g., ne, hi, ja)')
@click.option('--extract-file', required=True, help='Geofabrik extract (e.g., nepal-latest)')
@click.option('--left', type=float, required=True, help='Bounding box: West longitude')
@click.option('--right', type=float, required=True, help='Bounding box: East longitude')
@click.option('--bottom', type=float, required=True, help='Bounding box: South latitude')
@click.option('--top', type=float, required=True, help='Bounding box: North latitude')
@click.option('--code-page', type=int, default=65001, help='Character encoding (default: 65001 UTF-8)')
@click.option('--mapid-native', default=None, help='MAPID for native language (hex, e.g., 1058)')
@click.option('--mapid-english', default=None, help='MAPID for English (hex, e.g., 1048)')
@click.option('--dry-run', is_flag=True, default=False, help='Show what would be created without creating files')
def main(region, region_lower, dem_name, lang, extract_file, left, right, bottom, top,
         code_page, mapid_native, mapid_english, dry_run):
    """Generate suite .mk files for a new TOPO map region."""
    
    print(f"\n{'=' * 70}")
    print(f"Generating Suite: {region} ({region_lower})")
    print(f"{'=' * 70}\n")
    
    # Generate default MAPIDs if not provided
    if mapid_native is None:
        # Auto-generate based on existing registry
        next_id = max(MAPID_REGISTRY.values()) + 0x10
        mapid_native = next_id
        print(f"⚠ Auto-generated native MAPID: 0x{mapid_native:04x}")
    else:
        mapid_native = int(mapid_native, 16)
    
    if mapid_english is None:
        mapid_english = mapid_native - 0x10
        print(f"⚠ Auto-generated English MAPID: 0x{mapid_english:04x}")
    else:
        mapid_english = int(mapid_english, 16)
    
    print()
    
    # Create directory
    suite_dir = f"suites/{region_lower}"
    
    if not dry_run:
        os.makedirs(suite_dir, exist_ok=True)
    
    # Generate suite files
    files_to_create = {}
    
    # Base mapsforge suite
    base_mk = create_base_suite_mk(region, region_lower, dem_name, lang, code_page,
                                   extract_file, left, right, bottom, top)
    files_to_create[f"{suite_dir}/{region_lower}.mk"] = base_mk
    
    # Garmin DEM suite (native language)
    garmin_mk = create_garmin_dem_suite_mk(region, region_lower, dem_name, lang, code_page,
                                          extract_file, left, right, bottom, top, mapid_native)
    files_to_create[f"{suite_dir}/{region_lower}_bc_dem.mk"] = garmin_mk
    
    # Garmin DEM suite (English)
    garmin_en_mk = create_garmin_dem_english_suite_mk(region, region_lower, dem_name,
                                                       extract_file, left, right, bottom, top,
                                                       mapid_english)
    files_to_create[f"{suite_dir}/{region_lower}_bc_dem_en.mk"] = garmin_en_mk
    
    # Print preview and create files
    print(f"Files to be created:\n")
    
    for filename, content in sorted(files_to_create.items()):
        lines = content.count('\n')
        print(f"  ✓ {filename} ({lines} lines)")
        if not dry_run:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                f.write(content)
    
    print(f"\n{'=' * 70}")
    
    if dry_run:
        print("✓ Dry run completed - no files were created")
        print("\nTo create files, run without --dry-run:")
        print(f"  python3 tools/generate_suite.py \\")
        print(f"    --region {region} \\")
        print(f"    --region-lower {region_lower} \\")
        print(f"    --lang {lang} \\")
        print(f"    --extract-file {extract_file} \\")
        print(f"    --left {left} --right {right} --bottom {bottom} --top {top}")
    else:
        print(f"✓ Suite created successfully!")
        print(f"\nNext steps:")
        print(f"  1. Add suite include to Makefile:")
        print(f"     include $(wildcard $(ROOT_DIR)/suites/{region_lower}/*.mk)")
        print(f"  2. Add batch build target to Makefile:")
        print(f"     {region_lower.upper()}_SUITES := {region_lower} {region_lower}_bc_dem {region_lower}_bc_dem_en")
        print(f"  3. Prepare data files:")
        print(f"     - hgt/{region_lower}_hgtmix.zip")
        print(f"     - download/osm_elevations/ele_{region_lower}_10_100_500.pbf")
        print(f"     - download/osm_elevations/marker/ele_{region_lower}_10_100_500_mix.pbf")
        print(f"  4. Build the suite:")
        print(f"     make {region_lower}_suites")
    
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
