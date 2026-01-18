#!/usr/bin/env python3
"""
Generate mirror checking configuration files for map suites.

This script generates JSON configuration files for the check-mirrors.py tool
based on the suite definition files in the suites/ directory.

It auto-discovers available suites by scanning the suites/ directory for
subdirectories containing a .mk file with the required variables.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Get the root directory (parent of tools/)
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent
SUITES_DIR = ROOT_DIR / "suites"
CONFIGS_DIR = SCRIPT_DIR / "mirror-configs"


def discover_suites():
    """Discover available suites by scanning the suites/ directory."""
    suites = []
    if not SUITES_DIR.exists():
        return suites
    
    for suite_dir in sorted(SUITES_DIR.iterdir()):
        if suite_dir.is_dir():
            mk_file = suite_dir / f"{suite_dir.name}.mk"
            if mk_file.exists():
                suites.append(suite_dir.name)
    
    return suites


def parse_makefile(suite_name):
    """Parse the suite makefile to extract configuration values."""
    mk_file = SUITES_DIR / suite_name / f"{suite_name}.mk"
    
    if not mk_file.exists():
        raise FileNotFoundError(f"Suite makefile not found: {mk_file}")
    
    config = {}
    with open(mk_file, 'r') as f:
        content = f.read()
    
    # Extract key variables using regex
    patterns = {
        'REGION': r'REGION\s*:=\s*(\S+)',
        'DEM_NAME': r'DEM_NAME\s*:=\s*(\S+)',
        'LANG': r'LANG\s*:=\s*(\S+)',
        'TOPO_PAGE': r'TOPO_PAGE\s*:=\s*(\S+)',
        'TARGETS': r'TARGETS\s*:=\s*(.+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            config[key] = match.group(1).strip()
    
    return config


def generate_config(suite_name, mk_config, label=None):
    """Generate the checking configuration for a suite."""
    region = mk_config.get('REGION', suite_name.capitalize())
    dem_name = mk_config.get('DEM_NAME', 'AW3D30')
    lang = mk_config.get('LANG', 'en')
    topo_page = mk_config.get('TOPO_PAGE', f'{suite_name}_topo')
    
    # Use provided label or derive from region
    if label is None:
        label = region
    
    # Base name patterns
    base_name = f"{dem_name}_OSM_{region}_TOPO_Rudy"
    carto_name = f"{region}_carto"
    
    # Generate file lists
    files = [
        # Index/HTML file
        f"{topo_page}.html",
        # Mapsforge files
        f"{base_name}.map.zip",
        f"{base_name}.zip",
        f"{base_name}_locus.zip",
        # POI files
        f"{base_name}.poi.zip",
        f"{base_name}_v2.poi.zip",
        f"{base_name}.db.zip",
        # Carto packages
        f"{carto_name}_map.cpkg",
        f"{carto_name}_style.cpkg",
        f"{carto_name}_dem.cpkg",
        f"{carto_name}_upgrade.cpkg",
        f"{carto_name}_all.cpkg",
        # Garmin files - native language
        f"gmapsupp_{region}_{dem_name.lower()}_{lang}_camp3D.img.zip",
        f"Install_{dem_name}_{region}_TOPO_camp3D_{lang}.exe",
        f"{region}_{dem_name.lower()}_{lang}_camp3D.gmap.zip",
    ]
    
    # Add English Garmin files if native language is not English
    if lang != 'en':
        files.extend([
            f"gmapsupp_{region}_{dem_name.lower()}_en_camp3D.img.zip",
            f"Install_{dem_name}_{region}_TOPO_camp3D_en.exe",
            f"{region}_{dem_name.lower()}_en_camp3D.gmap.zip",
        ])
    
    config = {
        "name": suite_name,
        "label": label,
        "indexes": [
            f"{topo_page}.html"
        ],
        "files": files,
        "exist_only": [
            # HGT/DEM file
            f"{suite_name}_hgtmix.zip",
            # Locus XML files (cedric mirror)
            f"{suite_name}_map-cedric.xml",
            f"{suite_name}_dem-cedric.xml",
            f"{suite_name}_upgrade-cedric.xml",
            f"{suite_name}_all-cedric.xml",
        ],
        "check_today": False
    }
    
    return config


def write_config(suite_name, config, output_dir=None, dry_run=False):
    """Write the configuration to a JSON file."""
    if output_dir is None:
        output_dir = CONFIGS_DIR
    else:
        output_dir = Path(output_dir)
    
    output_file = output_dir / f"{suite_name}.json"
    
    if dry_run:
        print(f"Would write to: {output_file}")
        print(json.dumps(config, indent=4))
        print()
        return
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=4)
        f.write('\n')
    
    print(f"Generated: {output_file}")


def main():
    # Discover available suites
    available_suites = discover_suites()
    
    parser = argparse.ArgumentParser(
        description='Generate mirror checking configuration files for map suites.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
This tool generates JSON configuration files for check-mirrors.py based on
the suite definition files in suites/<suite>/<suite>.mk.

Required makefile variables:
  REGION      - Region name (e.g., Fujisan, Kashmir)
  DEM_NAME    - DEM source (e.g., AW3D30, MOI)
  LANG        - Native language code (e.g., ja, ne, hi, zh)
  TOPO_PAGE   - HTML page name (e.g., fujisan_topo)

Examples:
  %(prog)s fujisan              # Generate config for fujisan
  %(prog)s --dry-run annapurna  # Preview without writing
  %(prog)s --label "Kumano Kodo" kumano  # Use custom label
  %(prog)s -o /tmp fujisan      # Output to different directory
  %(prog)s --list               # List available suites

Available suites: {', '.join(available_suites) if available_suites else '(none found)'}
        """
    )
    parser.add_argument(
        'suites',
        nargs='*',
        help='Suite names to generate (required)'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview generated config without writing to file'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available suites'
    )
    parser.add_argument(
        '--label',
        type=str,
        help='Custom label for the suite (default: derived from REGION)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        help=f'Output directory (default: {CONFIGS_DIR})'
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Available suites:")
        for suite in available_suites:
            try:
                mk_config = parse_makefile(suite)
                region = mk_config.get('REGION', '?')
                lang = mk_config.get('LANG', '?')
                dem = mk_config.get('DEM_NAME', '?')
                print(f"  {suite:15} REGION={region}, LANG={lang}, DEM={dem}")
            except Exception as e:
                print(f"  {suite:15} (error: {e})")
        return 0
    
    # Require at least one suite
    if not args.suites:
        parser.print_help()
        print(f"\nError: Please specify at least one suite name.", file=sys.stderr)
        print(f"Available suites: {', '.join(available_suites)}", file=sys.stderr)
        return 1
    
    # Custom label only works with single suite
    if args.label and len(args.suites) > 1:
        print("Error: --label can only be used with a single suite.", file=sys.stderr)
        return 1
    
    # Validate suite names
    for suite in args.suites:
        if suite not in available_suites:
            print(f"Error: '{suite}' is not an available suite.", file=sys.stderr)
            print(f"Available suites: {', '.join(available_suites)}", file=sys.stderr)
            return 1
    
    # Generate configs
    for suite_name in args.suites:
        try:
            mk_config = parse_makefile(suite_name)
            config = generate_config(suite_name, mk_config, label=args.label)
            write_config(suite_name, config, output_dir=args.output_dir, dry_run=args.dry_run)
        except Exception as e:
            print(f"Error generating config for {suite_name}: {e}", file=sys.stderr)
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
