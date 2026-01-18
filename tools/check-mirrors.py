#!/usr/bin/env python3

import click
import requests
import sys
import re
import os
import json
import datetime
import time
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIGS_DIR = SCRIPT_DIR / "mirror-configs"

# Mirror servers configuration
# Key is the short name used for CLI options, value is the URL
MIRRORS = {
    "happyman": "https://map.happyman.idv.tw/rudy",
    "kcwu": "https://moi.kcwu.csie.org",
    # "basecamp": "http://rudy.basecamp.tw",
    "cedric": "https://d3r5lsn28erp7o.cloudfront.net",
    "rudymap": "https://rudymap.tw"
}

# For backward compatibility
mirrors = list(MIRRORS.values())

# Available suite names (loaded from config files)
AVAILABLE_SUITES = ["daily", "suites", "fujisan", "kumano", "annapurna", "kashmir"]


def discover_available_suites():
    """Discover available suites from config files."""
    suites = []
    if CONFIGS_DIR.exists():
        for config_file in sorted(CONFIGS_DIR.glob("*.json")):
            suites.append(config_file.stem)
    return suites


def load_suite_config(suite_name):
    """Load suite configuration from JSON file."""
    config_file = CONFIGS_DIR / f"{suite_name}.json"
    if not config_file.exists():
        raise FileNotFoundError(f"Suite config file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        return json.load(f)


def load_all_suite_configs():
    """Load all suite configurations."""
    configs = {}
    for suite_name in AVAILABLE_SUITES:
        try:
            configs[suite_name] = load_suite_config(suite_name)
        except FileNotFoundError:
            pass  # Skip suites without config files
    return configs


def load_suite_configs(suite_names):
    """Load specific suite configurations."""
    configs = {}
    for suite_name in suite_names:
        configs[suite_name] = load_suite_config(suite_name)
    return configs


# Legacy compatibility: load configs for backward compatible access
def _get_legacy_data():
    """Load data for backward compatibility with old variable names."""
    configs = load_all_suite_configs()
    return configs

# Files to check for existence only (no date check) - for backward compatibility
files = [
    "extra/Markchoo.map.zip",
    "extra/Compartment.map.zip",
    "hgtmix.zip",
    "hgt90.zip",
    "legend_V1R1.pdf",
    "locus_map-happyman.xml",
    "locus_style-happyman.xml",
    "locus_dem-happyman.xml",
    "locus_upgrade-happyman.xml",
    "locus_all-happyman.xml",
    "locus_map-happyman.xml",
    "locus_style-kcwu.xml",
    "locus_dem-kcwu.xml",
    "locus_upgrade-kcwu.xml",
    "locus_all-kcwu.xml",
    "locus_map-rex.xml",
    "locus_style-rex.xml",
    "locus_dem-rex.xml",
    "locus_upgrade-rex.xml",
    "locus_all-rex.xml"
]


def print_error(message, err):
    print("  {} ({})".format(message, err), file=sys.stderr)


def print_status(ok, uri):
    print("{} {}".format("v" if ok else "x", uri), file=sys.stdout)


def check_version(uri):
    try:
        response = requests.get(uri, timeout=(3.0, 600.0), allow_redirects=True)
        response.raise_for_status()
        if response.status_code is not requests.codes['ok']:
            print_status(False, uri)
            print_error("Status error", "Status: {}".format(response.status_code))
            return False

        p = re.compile("v\\d\\d\\d\\d\\.\\d\\d\\.\\d\\d", re.MULTILINE)
        m = p.search(response.text)
        if m is None:
            print_status(False, uri)
            print_error("No Version?", "Cannot find version in index file")
            return False

        print_status(True, "{} ({})".format(uri, m.group()))
        return True
    except requests.ConnectionError as err:
        print_status(False, uri)
        print_error("Connection error", err)
        return False
    except requests.Timeout as timeout:
        print_status(False, uri)
        print_error("Connection timeout", timeout)
        return False
    except requests.HTTPError as err:
        print_status(False, uri)
        print_error("Status error", err)
        return False


def check_exist(uri, check_today=False, check_this_week=False):
    try:
        response = requests.head(uri, timeout=(3.0, 600.0), allow_redirects=True)
        response.raise_for_status()
        if response.status_code is not requests.codes['ok']:
            print_status(False, uri)
            print_error("Status error", "Status: {}".format(response.status_code))
            return False

        gmt = datetime.datetime.strptime(response.headers["last-modified"], "%a, %d %b %Y %H:%M:%S %Z")
        local = gmt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
        now = datetime.datetime.now()
        delta = now - gmt
        if check_today and delta.days > 2:
            print_status(False, "{} ({})".format(uri, local.strftime("v%Y.%m.%d")))
            # print("{} - {} = {}".format(now.time(), gmt.time(), delta.days), file=sys.stdout)
        elif check_this_week and delta.days > 7:
            print_status(False, "{} ({})".format(uri, local.strftime("v%Y.%m.%d")))
            # print("{} - {} = {}".format(now.time(), gmt.time(), delta.days), file=sys.stdout)
        else:
            print_status(True, "{} ({})".format(uri, local.strftime("v%Y.%m.%d")))
        return True
    except requests.ConnectionError as err:
        print_status(False, uri)
        print_error("Connection error", err)
        return False
    except requests.Timeout as timeout:
        print_status(False, uri)
        print_error("Connection timeout", timeout)
        return False
    except requests.HTTPError as err:
        print_status(False, uri)
        print_error("Status error", err)
        return False
    except KeyError as err:
        print_status(False, uri)
        print_error("Cannnot find last-modified", err)
        return False


def check_speed(uri):
    os.system("curl -L {} > /dev/null".format(uri))


def get_mirror_names():
    """Return list of mirror short names for help text."""
    return list(MIRRORS.keys())


@click.command()
@click.option('--daily', '-d', is_flag=True, help='Check daily/beta files (released Mon/Wed/Sat, in drops/ folder)')
@click.option('--suites', '-s', is_flag=True, help='Check weekly/suites files (released Thursday, in root folder)')
@click.option('--fujisan', '-f', is_flag=True, help='Check Fujisan files (released with suites)')
@click.option('--kumano', '-k', is_flag=True, help='Check Kumano Kodo files (released with suites)')
@click.option('--annapurna', '-a', is_flag=True, help='Check Annapurna files (released with suites)')
@click.option('--kashmir', '-K', is_flag=True, help='Check Kashmir files (released with suites)')
@click.option('--suite', '-S', multiple=True, help='Check specific suite by name (can be used multiple times)')
@click.option('--list-suites', is_flag=True, help='List all available suites')
@click.option('--speed', is_flag=True, default=False, help='Run speed test (default: off)')
@click.option('--mirror', '-m', type=str, help='Check specific mirror URL only (deprecated, use mirror options below)')
@click.option('--happyman', is_flag=True, help='Check happyman mirror only')
@click.option('--kcwu', is_flag=True, help='Check kcwu mirror only')
@click.option('--cedric', is_flag=True, help='Check cedric mirror only')
@click.option('--rudymap', is_flag=True, help='Check rudymap mirror only')
def main(daily, suites, fujisan, kumano, annapurna, kashmir, suite, list_suites, speed, mirror, happyman, kcwu, cedric, rudymap):
    """Check mirror servers for Taiwan TOPO map files.

    \b
    Two-dimensional selection:
      - Suite dimension: --daily, --suites, --fujisan, --kumano, --annapurna, --kashmir
                         or use --suite <name> for any suite with a config file
      - Mirror dimension: --happyman, --kcwu, --cedric, --rudymap

    \b
    Examples:
      check-mirrors.py                  # Check all (daily + suites) on all mirrors
      check-mirrors.py --daily          # Check daily/beta files on all mirrors
      check-mirrors.py --suites         # Check weekly/suites files on all mirrors
      check-mirrors.py --happyman       # Check all (daily + suites) on happyman only
      check-mirrors.py --daily --happyman  # Check daily files on happyman only
      check-mirrors.py --suites --kcwu --rudymap  # Check suites on kcwu and rudymap
      check-mirrors.py --kumano         # Check Kumano Kodo files on all mirrors
      check-mirrors.py --annapurna      # Check Annapurna files on all mirrors
      check-mirrors.py --kashmir        # Check Kashmir files on all mirrors
      check-mirrors.py --suite nikko_oze  # Check any suite by name
      check-mirrors.py --suite nikko_oze --suite yushan  # Check multiple suites
      check-mirrors.py --list-suites    # List all available suites
      check-mirrors.py --speed          # Run speed test on all mirrors
      check-mirrors.py --speed --happyman  # Run speed test on happyman only
    """
    # Handle --list-suites
    if list_suites:
        available = discover_available_suites()
        print("Available suites:")
        for s in available:
            try:
                config = load_suite_config(s)
                label = config.get('label', s)
                print(f"  {s:20} ({label})")
            except Exception as e:
                print(f"  {s:20} (error: {e})")
        return

    # Suite dimension: Determine which suites to check
    suite_flags = {
        "daily": daily,
        "suites": suites,
        "fujisan": fujisan,
        "kumano": kumano,
        "annapurna": annapurna,
        "kashmir": kashmir
    }
    
    # Build list of suites to check
    selected_suites = [name for name, selected in suite_flags.items() if selected]
    
    # Add suites from --suite option
    if suite:
        available = discover_available_suites()
        for s in suite:
            if s not in available:
                print(f"Error: Suite '{s}' not found. Use --list-suites to see available suites.", file=sys.stderr)
                sys.exit(1)
            if s not in selected_suites:
                selected_suites.append(s)
    
    # If none specified, check daily and suites (default behavior)
    if not selected_suites:
        selected_suites = ["daily", "suites"]

    # Mirror dimension: Determine which mirrors to check
    mirror_flags = {
        "happyman": happyman,
        "kcwu": kcwu,
        "cedric": cedric,
        "rudymap": rudymap
    }
    
    # Build list of mirrors to check
    selected_mirrors = [name for name, selected in mirror_flags.items() if selected]
    
    # If --mirror option is used (deprecated), add it
    if mirror:
        check_mirrors = [mirror]
    elif selected_mirrors:
        # Use selected mirrors
        check_mirrors = [MIRRORS[name] for name in selected_mirrors]
    else:
        # No mirror specified, check all mirrors
        check_mirrors = list(MIRRORS.values())

    # If --speed is specified, only run speed test
    if speed:
        # Load suite configs from JSON files
        suite_configs = load_suite_configs(selected_suites)
        
        # Use the first selected suite, or daily as default
        suite_for_speed = selected_suites[0] if selected_suites else "daily"
        speed_test_file = suite_configs[suite_for_speed]["files"][0]
        
        for m in check_mirrors:
            print("Speed testing {}, ...".format(m))
            check_speed("{}/{}".format(m, speed_test_file))
            print("")
        return

    # Load suite file configurations from JSON files
    suite_configs = load_suite_configs(selected_suites)

    # Determine which indexes to check
    indexes = []
    for suite in selected_suites:
        indexes.extend(suite_configs[suite]["indexes"])

    for m in check_mirrors:
        print("Checking {}, ...".format(m))
        print("  [Index files]")
        for index in indexes:
            check_version("{}/{}".format(m, index))
        
        for suite in selected_suites:
            config = suite_configs[suite]
            print("  [{} files]".format(config["label"]))
            for file in config["files"]:
                check_exist("{}/{}".format(m, file), check_today=config["check_today"], check_this_week=not config["check_today"])
            if config["exist_only"]:
                print("  [Existing files]")
                for file in config["exist_only"]:
                    check_exist("{}/{}".format(m, file))
        print("")


if __name__ == "__main__":
    main()
