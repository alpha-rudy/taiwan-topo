#!/usr/bin/env python3
"""
Generate CartoType mapdetails.json files for carto packages.

This script generates 5 mapdetails.json files for each region suite:
- all.json: Complete package (map + style + elevation + POI)
- map.json: Map package (map + POI)
- style.json: Style package only
- dem.json: Elevation data package only
- upgrade.json: Upgrade package (map + style + elevation + POI)

Sizes are automatically estimated from the build-<REGION> directory.
Optional: can specify custom sizes via command-line options.

Usage:
    python3 generate_carto_mapdetails.py --region <region> --dem-name <dem_name> \
        --map-lat <lat> --map-lon <lon> \
        [--build-dir <path>] \
        [--dem-name-lower <dem_lower>] \
        [--auto-estimate] \
        [--map-size <size>] [--all-size <size>] [--dem-size <size>] [--style-size <size>]

Example (auto-estimate from build directory):
    python3 generate_carto_mapdetails.py --region Kumano --dem-name AW3D30 \
        --map-lat 33.84 --map-lon 135.77 --auto-estimate

Example (manual sizes):
    python3 generate_carto_mapdetails.py --region Everest --dem-name AW3D30 \
        --map-lat 28.59 --map-lon 83.82 \
        --map-size 1050 --all-size 1150 --dem-size 95
"""

import os
import json
import click


def estimate_sizes_from_build(build_dir, dem_name, region):
    """
    Estimate extracted_size_mb values from build directory.
    
    Returns a dict with estimated sizes for:
    - map_size: .map + .poi files
    - dem_size: HGT files total
    - style_size: Style zip file (typically 6MB)
    - all_size: Sum of all components
    """
    map_name = f"{dem_name}_OSM_{region}_TOPO_Rudy"
    
    # Try to find the main files
    map_file = os.path.join(build_dir, f"{map_name}.map")
    poi_file = os.path.join(build_dir, f"{map_name}.poi")
    style_file = os.path.join(build_dir, "MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip")
    
    def get_file_size_mb(filepath):
        """Get uncompressed size in MB"""
        try:
            size_bytes = os.path.getsize(filepath)
            return size_bytes / (1024 * 1024)
        except FileNotFoundError:
            return 0
    
    # Calculate sizes
    map_size_mb = get_file_size_mb(map_file)
    poi_size_mb = get_file_size_mb(poi_file)
    style_size_mb = get_file_size_mb(style_file)
    
    # Sum HGT files
    hgt_total_mb = 0
    try:
        for filename in os.listdir(build_dir):
            if filename.endswith('.hgt'):
                filepath = os.path.join(build_dir, filename)
                hgt_total_mb += get_file_size_mb(filepath)
    except FileNotFoundError:
        pass
    
    # Calculate package sizes
    map_only_size = int(map_size_mb + poi_size_mb)
    dem_only_size = int(hgt_total_mb)
    style_only_size = int(style_size_mb) if style_size_mb > 0 else 6
    all_size = int(map_size_mb + poi_size_mb + style_size_mb + hgt_total_mb)
    
    return {
        'map_size': map_only_size,
        'dem_size': dem_only_size,
        'style_size': style_only_size,
        'all_size': all_size
    }


def create_all_json(dem_name, region_name, map_lat, map_lon, all_size):
    """Create all.json - Complete package."""
    return {
        "version": 2,
        "extracted_size_mb": all_size,
        "elevationdata": ["*.hgt"],
        "maps": [
            {
                "name": f"{dem_name}_OSM_{region_name}_TOPO_Rudy",
                "file": f"{dem_name}_OSM_{region_name}_TOPO_Rudy.map",
                "type": "map",
                "load_in_layer": 0,
                "uniqueId": f"{dem_name}_OSM_{region_name}_TOPO_Rudy"
            }
        ],
        "styles": [
            {
                "file": "MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip",
                "load_in_layer": 0,
                "uniqueId": "MOI_OSM_Taiwan_TOPO_Rudy_hs_style"
            }
        ],
        "overlays": [
            {
                "file": f"{dem_name}_OSM_{region_name}_TOPO_Rudy.poi",
                "load": False,
                "uniqueId": f"{dem_name}_OSM_{region_name}_TOPO_Rudy"
            }
        ],
        "commands": [
            {
                "command": "mapposition",
                "lat": map_lat,
                "lon": map_lon,
                "zoom": 13
            }
        ]
    }


def create_map_json(dem_name, region_name, map_lat, map_lon, map_size):
    """Create map.json - Map package (map + POI)."""
    return {
        "version": 2,
        "extracted_size_mb": map_size,
        "maps": [
            {
                "name": f"{dem_name}_OSM_{region_name}_TOPO_Rudy",
                "file": f"{dem_name}_OSM_{region_name}_TOPO_Rudy.map",
                "type": "map",
                "load_in_layer": 0,
                "uniqueId": f"{dem_name}_OSM_{region_name}_TOPO_Rudy"
            }
        ],
        "overlays": [
            {
                "file": f"{dem_name}_OSM_{region_name}_TOPO_Rudy.poi",
                "load": False,
                "uniqueId": f"{dem_name}_OSM_{region_name}_TOPO_Rudy"
            }
        ],
        "commands": [
            {
                "command": "mapposition",
                "lat": map_lat,
                "lon": map_lon,
                "zoom": 13
            }
        ]
    }


def create_style_json():
    """Create style.json - Style package only."""
    return {
        "version": 2,
        "extracted_size_mb": 6,
        "styles": [
            {
                "file": "MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip",
                "load_in_layer": 0,
                "uniqueId": "MOI_OSM_Taiwan_TOPO_Rudy_hs_style"
            }
        ]
    }


def create_dem_json(dem_size):
    """Create dem.json - Elevation data package only."""
    return {
        "version": 2,
        "extracted_size_mb": dem_size,
        "elevationdata": ["*.hgt"]
    }


def create_upgrade_json(dem_name, region_name, map_lat, map_lon, all_size):
    """Create upgrade.json - Upgrade package (map + style + elevation + POI)."""
    return {
        "version": 2,
        "extracted_size_mb": all_size,
        "maps": [
            {
                "name": f"{dem_name}_OSM_{region_name}_TOPO_Rudy",
                "file": f"{dem_name}_OSM_{region_name}_TOPO_Rudy.map",
                "type": "map",
                "load_in_layer": 0,
                "uniqueId": f"{dem_name}_OSM_{region_name}_TOPO_Rudy"
            }
        ],
        "styles": [
            {
                "file": "MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip",
                "load_in_layer": 0,
                "uniqueId": "MOI_OSM_Taiwan_TOPO_Rudy_hs_style"
            }
        ],
        "overlays": [
            {
                "file": f"{dem_name}_OSM_{region_name}_TOPO_Rudy.poi",
                "load": False,
                "uniqueId": f"{dem_name}_OSM_{region_name}_TOPO_Rudy"
            }
        ],
        "commands": [
            {
                "command": "mapposition",
                "lat": map_lat,
                "lon": map_lon,
                "zoom": 13
            }
        ]
    }


@click.command()
@click.option('--region', required=True, help='Region name (e.g., Everest, Kumano)')
@click.option('--dem-name', required=True, help='DEM name (e.g., AW3D30)')
@click.option('--map-lat', type=float, required=True, help='Map center latitude')
@click.option('--map-lon', type=float, required=True, help='Map center longitude')
@click.option('--build-dir', default=None, help='Build directory path (auto-generated if not provided)')
@click.option('--dem-name-lower', default=None, help='DEM name lowercase (auto-generated if not provided)')
@click.option('--auto-estimate', is_flag=True, default=False, help='Auto-estimate sizes from build directory')
@click.option('--map-size', type=int, default=None, help='Map package size in MB (auto-estimated if not provided)')
@click.option('--all-size', type=int, default=None, help='All package size in MB (auto-estimated if not provided)')
@click.option('--dem-size', type=int, default=None, help='DEM package size in MB (auto-estimated if not provided)')
@click.option('--style-size', type=int, default=None, help='Style package size in MB (default: 6)')
def main(region, dem_name, map_lat, map_lon, build_dir, dem_name_lower, auto_estimate, 
         map_size, all_size, dem_size, style_size):
    """
    Generate CartoType mapdetails.json files for a region suite.
    
    Creates 5 JSON files in auto-install/carto/<Region>/:
    - all.json: Complete package
    - map.json: Map package
    - style.json: Style package
    - dem.json: Elevation package
    - upgrade.json: Upgrade package
    
    Sizes are automatically estimated from build directory if --auto-estimate is used,
    or can be specified manually with --map-size, --all-size, --dem-size options.
    """
    if dem_name_lower is None:
        dem_name_lower = dem_name.lower()
    
    # Determine build directory
    if build_dir is None:
        build_dir = f"build-{dem_name_lower}"
    
    output_dir = f"auto-install/carto/{region}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Generating CartoType mapdetails.json for region: {region}")
    print(f"  DEM: {dem_name}, Center: ({map_lat}, {map_lon})")
    print(f"  Output directory: {output_dir}")
    
    # Auto-estimate sizes if requested or if manual sizes not provided
    if auto_estimate or (map_size is None or all_size is None or dem_size is None):
        if os.path.exists(build_dir):
            print(f"  Build directory: {build_dir}")
            print(f"  Auto-estimating sizes from build directory...\n")
            
            estimated = estimate_sizes_from_build(build_dir, dem_name, region)
            
            # Use estimated values if not manually specified
            if map_size is None:
                map_size = estimated['map_size']
            if dem_size is None:
                dem_size = estimated['dem_size']
            if style_size is None:
                style_size = estimated['style_size']
            if all_size is None:
                all_size = estimated['all_size']
            
            print(f"  Estimated sizes:")
            print(f"    - Map (map + POI): {map_size}MB")
            print(f"    - DEM (elevation): {dem_size}MB")
            print(f"    - Style: {style_size}MB")
            print(f"    - All (complete): {all_size}MB\n")
        else:
            print(f"  Build directory not found: {build_dir}")
            print(f"  Using default sizes...\n")
            # Use sensible defaults
            if map_size is None:
                map_size = 1050
            if dem_size is None:
                dem_size = 95
            if style_size is None:
                style_size = 6
            if all_size is None:
                all_size = 1150
    else:
        print(f"  Using specified sizes:")
        print(f"    - Map: {map_size}MB")
        print(f"    - DEM: {dem_size}MB")
        print(f"    - Style: {style_size}MB")
        print(f"    - All: {all_size}MB\n")
    
    # Create all JSON files
    files_data = {
        "all.json": create_all_json(dem_name, region, map_lat, map_lon, all_size),
        "map.json": create_map_json(dem_name, region, map_lat, map_lon, map_size),
        "style.json": create_style_json(),
        "dem.json": create_dem_json(dem_size),
        "upgrade.json": create_upgrade_json(dem_name, region, map_lat, map_lon, all_size),
    }
    
    # Write each JSON file
    for filename, data in files_data.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent='\t')
        print(f"  Generated {filepath}")
    
    print(f"\n✓ Successfully generated 5 mapdetails.json files for {region}")


if __name__ == "__main__":
    main()
