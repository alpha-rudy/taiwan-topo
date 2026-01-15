#!/usr/bin/env python3

import click
import requests
import sys
import re
import os
import datetime
import time

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

# Index files for version checking
indexes_daily = [
    "drops/beta.html"
]

indexes_suites = [
    "taiwan_topo.html",
    "gts/index.html"
]

indexes_kumano = [
    "kumano_topo.html"
]

indexes_annapurna = [
    "annapurna_topo.html"
]

indexes_kashmir = [
    "kashmir_topo.html"
]

indexes_all = indexes_daily + indexes_suites

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

# Daily files (beta version) - released Mon/Wed/Sat, in drops/ folder
# Reference: docs/Taiwan/beta.md
daily_files = [
    "drops/MOI_OSM_Taiwan_TOPO_Rudy.map.zip",
    "drops/index.json",
    "drops/beta.html",
    "drops/MOI_OSM_Taiwan_TOPO_Rudy_style.zip",
    "drops/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip",
    "drops/MOI_OSM_Taiwan_TOPO_Rudy_locus_style.zip",
    "drops/MOI_OSM_extra_style.zip",
    "drops/MOI_OSM_bn_style.zip",
    "drops/MOI_OSM_dn_style.zip",
    "drops/MOI_OSM_tn_style.zip",
    "drops/Install_MOI_Taiwan_TOPO_camp3D.exe",
    "drops/Taiwan_moi_zh_camp3D.gmap.zip",
    "drops/MOI_OSM_Taiwan_TOPO_Rudy.poi.zip",
    "drops/MOI_OSM_Taiwan_TOPO_Rudy_v2.poi.zip",
    "drops/MOI_OSM_Taiwan_TOPO_Rudy.db.zip",
    "drops/MOI_OSM_twmap_style.zip"
]

# Weekly/Suites files (stable version) - released Thursday, in root folder
# Reference: docs/Taiwan/taiwan_topo.md
suites_files = [
    "index.json",
    "taiwan_topo.html",
    "gts/index.html",
    "carto_all.cpkg",
    "carto_upgrade.cpkg",
    "carto_dem.cpkg",
    "carto_style.cpkg",
    "carto_map.cpkg",
    "MOI_OSM_Taiwan_TOPO_Rudy.map.zip",
    "MOI_OSM_Taiwan_TOPO_Rudy.zip",
    "MOI_OSM_Taiwan_TOPO_Rudy_locus.zip",
    "MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip",
    "MOI_OSM_Taiwan_TOPO_Lite.zip",
    "MOI_OSM_Taiwan_TOPO_Lite.map.zip",
    "MOI_OSM_Taiwan_TOPO_Lite_style.zip",
    "MOI_OSM_Taiwan_TOPO_Rudy.poi.zip",
    "MOI_OSM_Taiwan_TOPO_Rudy_style.zip",
    "MOI_OSM_twmap_style.zip",
    "MOI_OSM_Taiwan_TOPO_Rudy_locus_style.zip",
    "MOI_OSM_extra_style.zip",
    "MOI_OSM_bn_style.zip",
    "MOI_OSM_dn_style.zip",
    "gmapsupp_Taiwan_moi_zh_bw.img.zip",
    "gmapsupp_Taiwan_moi_zh_odc.img.zip",
    "Install_MOI_Taiwan_TOPO_odc3D.exe",
    "Taiwan_moi_en_camp3D.gmap.zip",
    "Install_MOI_Taiwan_TOPO_camp3D_en.exe",
    "gmapsupp_Taiwan_moi_en_bw.img.zip",
    "Taiwan_moi_zh_camp3D.gmap.zip",
    "Install_MOI_Taiwan_TOPO_camp3D.exe",
    "gmapsupp_Taiwan_moi_zh_camp3D.img.zip",
    "Taiwan_moi_zh_camp.gmap.zip",
    "Install_MOI_Taiwan_TOPO_camp.exe",
    "gmapsupp_Taiwan_moi_zh_odc3D.img.zip",
    "gmapsupp_Taiwan_moi_zh_bw3D.img.zip",
    "MOI_OSM_tn_style.zip",
    "Taiwan_moi_zh_odc3D.gmap.zip"
]

# Keep 'weekly' as alias for backward compatibility
weekly = suites_files

# Kumano Kodo files - released with suites
# Reference: docs/Kumano/kumano_topo.md
kumano_files = [
    "kumano_topo.html",
    "AW3D30_OSM_Kumano_TOPO_Rudy.map.zip",
    "AW3D30_OSM_Kumano_TOPO_Rudy.zip",
    "AW3D30_OSM_Kumano_TOPO_Rudy_locus.zip",
    "AW3D30_OSM_Kumano_TOPO_Rudy.poi.zip",
    "AW3D30_OSM_Kumano_TOPO_Rudy_v2.poi.zip",
    "AW3D30_OSM_Kumano_TOPO_Rudy.db.zip",
    "Kumano_carto_map.cpkg",
    "Kumano_carto_style.cpkg",
    "Kumano_carto_dem.cpkg",
    "Kumano_carto_upgrade.cpkg",
    "Kumano_carto_all.cpkg",
    "gmapsupp_Kumano_aw3d30_ja_camp3D.img.zip",
    "Install_AW3D30_Kumano_TOPO_camp3D_ja.exe",
    "Kumano_aw3d30_ja_camp3D.gmap.zip",
    "gmapsupp_Kumano_aw3d30_en_camp3D.img.zip",
    "Install_AW3D30_Kumano_TOPO_camp3D_en.exe",
    "Kumano_aw3d30_en_camp3D.gmap.zip"
]

# Files to check for existence only (no date check) in Kumano
kumano_exist_only = [
    "kumano_hgtmix.zip",
    "kumano_map-cedric.xml",
    "kumano_dem-cedric.xml",
    "kumano_upgrade-cedric.xml",
    "kumano_all-cedric.xml"
]

# Annapurna files - released with suites
# Reference: docs/Annapurna/annapurna_topo.md
annapurna_files = [
    "annapurna_topo.html",
    "AW3D30_OSM_Annapurna_TOPO_Rudy.map.zip",
    "AW3D30_OSM_Annapurna_TOPO_Rudy.zip",
    "AW3D30_OSM_Annapurna_TOPO_Rudy_locus.zip",
    "AW3D30_OSM_Annapurna_TOPO_Rudy.poi.zip",
    "AW3D30_OSM_Annapurna_TOPO_Rudy_v2.poi.zip",
    "AW3D30_OSM_Annapurna_TOPO_Rudy.db.zip",
    "Annapurna_carto_map.cpkg",
    "Annapurna_carto_style.cpkg",
    "Annapurna_carto_dem.cpkg",
    "Annapurna_carto_upgrade.cpkg",
    "Annapurna_carto_all.cpkg",
    "gmapsupp_Annapurna_aw3d30_ne_camp3D.img.zip",
    "Install_AW3D30_Annapurna_TOPO_camp3D_ne.exe",
    "Annapurna_aw3d30_ne_camp3D.gmap.zip",
    "gmapsupp_Annapurna_aw3d30_en_camp3D.img.zip",
    "Install_AW3D30_Annapurna_TOPO_camp3D_en.exe",
    "Annapurna_aw3d30_en_camp3D.gmap.zip",
    "gmapsupp_Annapurna_aw3d30_ne_camp3D.img.zip",
    "Install_AW3D30_Annapurna_TOPO_camp3D_ne.exe",
    "Annapurna_aw3d30_ne_camp3D.gmap.zip"
]

# Files to check for existence only (no date check) in Annapurna
annapurna_exist_only = [
    "annapurna_hgtmix.zip",
    "annapurna_map-cedric.xml",
    "annapurna_dem-cedric.xml",
    "annapurna_upgrade-cedric.xml",
    "annapurna_all-cedric.xml"
]


# Kashmir files - released with suites
# Reference: docs/Kashmir/kashmir_topo.md
kashmir_files = [
    "kashmir_topo.html",
    "AW3D30_OSM_Kashmir_TOPO_Rudy.map.zip",
    "AW3D30_OSM_Kashmir_TOPO_Rudy.zip",
    "AW3D30_OSM_Kashmir_TOPO_Rudy_locus.zip",
    "AW3D30_OSM_Kashmir_TOPO_Rudy.poi.zip",
    "AW3D30_OSM_Kashmir_TOPO_Rudy_v2.poi.zip",
    "AW3D30_OSM_Kashmir_TOPO_Rudy.db.zip",
    "Kashmir_carto_map.cpkg",
    "Kashmir_carto_style.cpkg",
    "Kashmir_carto_dem.cpkg",
    "Kashmir_carto_upgrade.cpkg",
    "Kashmir_carto_all.cpkg",
    "gmapsupp_Kashmir_aw3d30_hi_camp3D.img.zip",
    "Install_AW3D30_Kashmir_TOPO_camp3D_hi.exe",
    "Kashmir_aw3d30_hi_camp3D.gmap.zip",
    "gmapsupp_Kashmir_aw3d30_en_camp3D.img.zip",
    "Install_AW3D30_Kashmir_TOPO_camp3D_en.exe",
    "Kashmir_aw3d30_en_camp3D.gmap.zip"
]

# Files to check for existence only (no date check) in Kashmir
kashmir_exist_only = [
    "kashmir_hgtmix.zip",
    "kashmir_map-cedric.xml",
    "kashmir_dem-cedric.xml",
    "kashmir_upgrade-cedric.xml",
    "kashmir_all-cedric.xml"
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
        if check_today and delta.days > 3:
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
@click.option('--kumano', '-k', is_flag=True, help='Check Kumano Kodo files (released with suites)')
@click.option('--annapurna', '-a', is_flag=True, help='Check Annapurna files (released with suites)')
@click.option('--kashmir', '-K', is_flag=True, help='Check Kashmir files (released with suites)')
@click.option('--speed', is_flag=True, default=False, help='Run speed test (default: off)')
@click.option('--mirror', '-m', type=str, help='Check specific mirror URL only (deprecated, use mirror options below)')
@click.option('--happyman', is_flag=True, help='Check happyman mirror only')
@click.option('--kcwu', is_flag=True, help='Check kcwu mirror only')
@click.option('--cedric', is_flag=True, help='Check cedric mirror only')
@click.option('--rudymap', is_flag=True, help='Check rudymap mirror only')
def main(daily, suites, kumano, annapurna, kashmir, speed, mirror, happyman, kcwu, cedric, rudymap):
    """Check mirror servers for Taiwan TOPO map files.

    \b
    Two-dimensional selection:
      - Suite dimension: --daily, --suites, --kumano, --annapurna, --kashmir
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
      check-mirrors.py --speed          # Run speed test on all mirrors
      check-mirrors.py --speed --happyman  # Run speed test on happyman only
    """
    # Suite dimension: Determine which suites to check
    suite_flags = {
        "daily": daily,
        "suites": suites,
        "kumano": kumano,
        "annapurna": annapurna,
        "kashmir": kashmir
    }
    
    # Build list of suites to check
    selected_suites = [name for name, selected in suite_flags.items() if selected]
    
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
        # Map suite names to their file lists
        suite_files = {
            "daily": daily_files,
            "suites": suites_files,
            "kumano": kumano_files,
            "annapurna": annapurna_files,
            "kashmir": kashmir_files
        }
        
        # Use the first selected suite, or daily as default
        suite_for_speed = selected_suites[0] if selected_suites else "daily"
        speed_test_file = suite_files[suite_for_speed][0]
        
        for m in check_mirrors:
            print("Speed testing {}, ...".format(m))
            check_speed("{}/{}".format(m, speed_test_file))
            print("")
        return

    # Suite file configurations
    suite_configs = {
        "daily": {
            "indexes": indexes_daily,
            "files": daily_files,
            "exist_only": [],
            "check_today": True,
            "label": "Daily/Beta"
        },
        "suites": {
            "indexes": indexes_suites,
            "files": suites_files,
            "exist_only": files,
            "check_today": False,
            "label": "Suites/Weekly"
        },
        "kumano": {
            "indexes": indexes_kumano,
            "files": kumano_files,
            "exist_only": kumano_exist_only,
            "check_today": False,
            "label": "Kumano Kodo"
        },
        "annapurna": {
            "indexes": indexes_annapurna,
            "files": annapurna_files,
            "exist_only": annapurna_exist_only,
            "check_today": False,
            "label": "Annapurna"
        },
        "kashmir": {
            "indexes": indexes_kashmir,
            "files": kashmir_files,
            "exist_only": kashmir_exist_only,
            "check_today": False,
            "label": "Kashmir"
        }
    }

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
