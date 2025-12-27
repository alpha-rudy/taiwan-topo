#!/usr/bin/env python3

import requests
import sys
import re
import os
import datetime
import time

mirrors = [
    "https://map.happyman.idv.tw/rudy",
    "https://moi.kcwu.csie.org",
    "http://rudy.basecamp.tw",
    "https://d3r5lsn28erp7o.cloudfront.net",
    "https://rudymap.tw"
]

indexes = [
    "taiwan_topo.html",
    "drops/beta.html",
    "gts/index.html"
]

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

daily = [
    "drops/MOI_OSM_Taiwan_TOPO_Rudy.map.zip",
    "drops/index.json",
    "drops/beta.html",
    "drops/MOI_OSM_Taiwan_TOPO_Rudy_style.zip",
    "drops/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip",
    "drops/MOI_OSM_Taiwan_TOPO_Rudy_locus_style.zip",
    "drops/MOI_OSM_extra_style.zip",
    "drops/MOI_OSM_bn_style.zip",
    "drops/MOI_OSM_dn_style.zip",
    "drops/Install_MOI_Taiwan_TOPO_camp3D.exe",
    "drops/Taiwan_moi_zh_camp3D.gmap.zip",
    "drops/hgtmix.zip",
    "drops/hgt90.zip"
]

weekly = [
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
        if check_today and delta.days > 1:
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


for mirror in mirrors:
    print("Checking {}, ...".format(mirror))
    for index in indexes:
        check_version("{}/{}".format(mirror, index))
    for file in daily:
        check_exist("{}/{}".format(mirror, file), check_today=True)
    for file in weekly:
        check_exist("{}/{}".format(mirror, file), check_this_week=True)
    for file in files:
        check_exist("{}/{}".format(mirror, file))
    print("")

for mirror in mirrors:
    print("Speed testing {}, ...".format(mirror))
    check_speed("{}/{}".format(mirror, daily[0]))
    print("")
