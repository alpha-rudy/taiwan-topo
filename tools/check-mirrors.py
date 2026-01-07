#!/usr/bin/env python3

import click
import requests
import sys
import re
import os
import datetime
import time

mirrors = [
    "https://map.happyman.idv.tw/rudy",
    "https://moi.kcwu.csie.org",
    # "http://rudy.basecamp.tw",
    "https://d3r5lsn28erp7o.cloudfront.net",
    "https://rudymap.tw"
]

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
    "kumano_hgtmix.zip"
]

# Annapurna files - released with suites
# Reference: docs/Annapurna/annapurna_topo.md
annapurna_files = [
    "annapurna_topo.html",
    "AW3D30_OSM_Annapurna_TOPO_Rudy.map.zip",
    "AW3D30_OSM_Annapurna_TOPO_Rudy.zip",
    "AW3D30_OSM_Annapurna_TOPO_Rudy.poi.zip",
    "AW3D30_OSM_Annapurna_TOPO_Rudy_v2.poi.zip",
    "AW3D30_OSM_Annapurna_TOPO_Rudy.db.zip",
    "Annapurna_carto_map.cpkg",
    "Annapurna_carto_style.cpkg",
    "Annapurna_carto_dem.cpkg",
    "Annapurna_carto_upgrade.cpkg",
    "Annapurna_carto_all.cpkg",
    "gmapsupp_Annapurna_aw3d30_en_camp3D.img.zip",
    "Install_AW3D30_Annapurna_TOPO_camp3D_en.exe",
    "Annapurna_aw3d30_en_camp3D.gmap.zip",
    "gmapsupp_Annapurna_aw3d30_ne_camp3D.img.zip",
    "Install_AW3D30_Annapurna_TOPO_camp3D_ne.exe",
    "Annapurna_aw3d30_ne_camp3D.gmap.zip"
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


@click.command()
@click.option('--daily', '-d', is_flag=True, help='Check daily/beta files (released Mon/Wed/Sat, in drops/ folder)')
@click.option('--suites', '-s', is_flag=True, help='Check weekly/suites files (released Thursday, in root folder)')
@click.option('--kumano', '-k', is_flag=True, help='Check Kumano Kodo files (released with suites)')
@click.option('--annapurna', '-a', is_flag=True, help='Check Annapurna files (released with suites)')
@click.option('--speed', is_flag=True, default=False, help='Run speed test (default: off)')
@click.option('--mirror', '-m', type=str, help='Check specific mirror URL only')
def main(daily, suites, kumano, annapurna, speed, mirror):
    """Check mirror servers for Taiwan TOPO map files.

    \b
    Examples:
      check-mirrors.py                  # Check all (daily + suites)
      check-mirrors.py --daily          # Check daily/beta files only (drops/ folder)
      check-mirrors.py --suites         # Check weekly/suites files only (root folder)
      check-mirrors.py --kumano         # Check Kumano Kodo files only
      check-mirrors.py --annapurna      # Check Annapurna files only
      check-mirrors.py --daily --suites # Check both daily and suites
    check-mirrors.py --speed          # Run speed test
    """
    # If neither daily nor suites nor kumano nor annapurna is specified, check daily and suites (default behavior)
    check_daily = daily
    check_suites = suites
    check_kumano = kumano
    check_annapurna = annapurna
    if not check_daily and not check_suites and not check_kumano and not check_annapurna:
        check_daily = True
        check_suites = True

    # Determine which mirrors to check
    check_mirrors = mirrors
    if mirror:
        check_mirrors = [mirror]

    # Determine which indexes to check
    indexes = []
    if check_daily:
        indexes.extend(indexes_daily)
    if check_suites:
        indexes.extend(indexes_suites)
    if check_kumano:
        indexes.extend(indexes_kumano)
    if check_annapurna:
        indexes.extend(indexes_annapurna)

    for m in check_mirrors:
        print("Checking {}, ...".format(m))
        for index in indexes:
            check_version("{}/{}".format(m, index))
        if check_daily:
            print("  [Daily/Beta files]")
            for file in daily_files:
                check_exist("{}/{}".format(m, file), check_today=True)
        if check_suites:
            print("  [Suites/Weekly files]")
            for file in suites_files:
                check_exist("{}/{}".format(m, file), check_this_week=True)
            for file in files:
                check_exist("{}/{}".format(m, file))
        if check_kumano:
            print("  [Kumano Kodo files]")
            for file in kumano_files:
                check_exist("{}/{}".format(m, file), check_this_week=True)
            for file in kumano_exist_only:
                check_exist("{}/{}".format(m, file))
        if check_annapurna:
            print("  [Annapurna files]")
            for file in annapurna_files:
                check_exist("{}/{}".format(m, file), check_this_week=True)
        print("")

    if speed:
        if check_daily:
            speed_test_file = daily_files[0]
        elif check_suites:
            speed_test_file = suites_files[0]
        elif check_kumano:
            speed_test_file = kumano_files[0]
        else:
            speed_test_file = annapurna_files[0]
        for m in check_mirrors:
            print("Speed testing {}, ...".format(m))
            check_speed("{}/{}".format(m, speed_test_file))
            print("")


if __name__ == "__main__":
    main()
