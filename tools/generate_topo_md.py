#!/usr/bin/env python3
"""
Generate documentation markdown for a new TOPO map region.

This script creates the region documentation markdown file with installation
instructions for various mapping applications (Locus Map, Garmin, etc.).

It generates two files: docs/$REGION/$region_topo.md (the primary doc, whose
prose sections are filled in by hand/AI afterward) and docs/$REGION/$region_topo-en.md
(a pure-English counterpart). The English file's boilerplate is derived
automatically from the Chinese template via a translation dictionary (see
`translate_to_english()`); its Famous Peaks/Trekking Routes/Sights/Historical
Events sections start empty just like the Chinese file's, and are meant to be
filled in with an English translation of whatever is written into the Chinese
doc (see docs/ADDING_NEW_REGION.md).

Usage:
    python3 tools/generate_topo_md.py \
        --region <RegionName> \
        --region-lower <region_lower> \
        --title <region_title> \
        --lang <language_code> \
        [--hgt-files <hgt_files>]

Example:
    python3 tools/generate_topo_md.py \\
        --region Everest \\
        --region-lower everest \\
        --title "Everest Region Climbing Map" \\
        --lang ne \\
        --hgt-files "N28E83, N28E84"
"""

import os
import re
import click


# Blocks removed for regions without contours / HGT (no_elevation). Each pattern
# is matched against the raw template (before .format(), so {region}/{region_lower}
# still appear literally). Patterns anchor at line-start (re.MULTILINE) and consume
# the block's own trailing newlines only (never a leading newline, which would merge
# the block into its neighbour), and are anchored on stable text so unrelated
# sections that share a label (e.g. "三合一", "高程檔") are not touched.
NO_ELEVATION_STRIP_PATTERNS = [
    # 山林日誌: 地形渲染 (HGT) line
    r'^  \* 地形渲染，請貼網址: https://rudymap\.tw/\{region_lower\}_hgtmix\.zip\n',
    # 蛙弟 (wadi): 三合一 (all bundle) and 高程檔 (HGT)
    r'^    \* 三合一\n(?:      > [^\n]*wadi-all://[^\n]*\n){3}',
    r'^    \* 高程檔\n(?:      > [^\n]*wadi-hgt://[^\n]*\n){3}',
    # 綠野遊蹤 (GTS): 三合一 and 高程檔
    r'^    \* 三合一\n(?:      > [^\n]*gts-all://[^\n]*\n){3}',
    r'^    \* 高程檔\n(?:      > [^\n]*gts-hgt://[^\n]*\n){3}',
    # OruxMaps: DEM item
    r'^  \* !\[DEM\]\(images/OruxMaps_dem\.jpeg =36x\)[^\n]*\n(?:    > [^\n]*\n){3}',
    # Locus: DEM item
    r'^    \* !\[DEM\]\(images/Locus_dem\.jpeg =36x\)[^\n]*\n(?:      > [^\n]*\n){3}',
    # Locus: 三合一 (all) item
    r'^  \* 三合一\n    \* !\[Map\]\(images/Locus\.jpeg =36x\) 首次安裝\n(?:      > [^\n]*\n){3}',
    # Cartograph: entire block + its trailing blank line (all packages are .cpkg)
    r'^\* !\[Cartograph\]\(images/Cartograph\.png =36x\).*?\n\n(?=\* !\[Android\])',
    # Mapsforge manual section: 30m HGT item
    r'^  \* !\[DEM\]\(images/Android\.png =36x\)!\[iOS\]\(images/macOS\.png =36x\) 30m HGT\n(?:    > [^\n]*\n){3}',
    # Copyright: JAXA AW3D30 credit and Contour Lines tool credit (each + trailing blank)
    r'^\* JAXA ALOS World 3D - 30m \(AW3D30\) Version 4\.1.*?\n\n(?=\* GMAP Styles and TYP)',
    r'^\* Tool of Contour Lines: gdal and phyghtmap.*?\n\n(?=\* Tools of Maps)',
]


def strip_elevation_blocks(template):
    """Remove all HGT/DEM/contour/CartoType blocks from the raw template."""
    for pattern in NO_ELEVATION_STRIP_PATTERNS:
        template = re.sub(pattern, '', template, flags=re.DOTALL | re.MULTILINE)
    return template


# File-name token rewrites for no-elevation regions: drop the DEM_NAME token
# (AW3D30 / aw3d30) and use the plain "camp" Garmin style instead of "camp3D".
NO_ELEVATION_RENAMES = [
    ('AW3D30_OSM_', 'OSM_'),
    ('AW3D30.OSM', 'OSM'),
    ('Install_AW3D30_', 'Install_'),
    ('_aw3d30_', '_'),
    ('camp3D', 'camp'),
]


def rename_no_elevation(text):
    """Rewrite DEM/style file-name tokens for a no-elevation region."""
    for old, new in NO_ELEVATION_RENAMES:
        text = text.replace(old, new)
    return text


# Boilerplate translation dictionary (Traditional Chinese phrase -> English),
# used to derive the English template from the Chinese one. Keep this in sync
# with the phrasing used across the existing docs/*/*_topo-en.md files (they
# were produced by hand with the same glossary before this generator existed).
# Order doesn't matter here; apply_dict() sorts by length (longest first) so
# compound phrases are translated before their shorter substrings.
EN_TRANSLATIONS = {
    "適合用在 Garmin / Android / iOS 上的離線地圖。": "An offline map for Garmin / Android / iOS.",
    "適合用在 Garmin / Android / iOS 上，拿來登山與尋寶 (hiking/geocaching)！": "For hiking and geocaching on Garmin / Android / iOS!",
    "請注意，以下介紹內容為 AI 產生，若有錯誤請回報到魯地圖社群，我們會儘快更正。謝謝！  ^^": "Note: the descriptions below were AI-generated. Please report any errors to the RudyMap community and we'll fix them as soon as possible. Thanks!  ^^",
    "## 地圖範圍": "## Map Coverage",
    "緯度範圍": "Latitude range",
    "經度範圍": "Longitude range",
    "### 著名的山頭 (Famous Peaks)": "### Famous Peaks",
    "### 著名的健行路線 (Famous Trekking Routes)": "### Famous Trekking Routes",
    "### 著名景點": "### Famous Sights",
    "### 歷史事件": "### Historical Events",
    "## 安裝/下載連結": "## Installation / Download Links",
    "* 相關網頁": "* Related Links",
    "魯地圖分流器 (Cedric Shih)": "RudyMap Mirror Selector (Cedric Shih)",
    "說明網頁:": "Info pages:",
    "使用討論（臉書社團）:": "Discussion (Facebook Group):",
    "開發網站（GitHub）:": "Development site (GitHub):",
    "自動安裝": "Auto Install",
    "請於 APP 內直接安裝地圖": "Install the map directly within the app",
    "安裝示範影片：": "Installation demo video: ",
    "主地圖，請貼網址:": "Main map, paste this URL:",
    "地圖樣式，請貼網址:": "Map style, paste this URL:",
    "地形渲染，請貼網址:": "Terrain relief, paste this URL:",
    "點選下列連結來啟動安裝，也可於 APP 內直接下載來安裝地圖": "Tap one of the links below to trigger installation, or download and install directly within the app",
    "傳統版": "Classic version",
    "三合一": "All-in-one",
    "離線地圖": "Offline map",
    "風格主題": "Style theme",
    "高程檔": "Elevation (DEM) file",
    "安裝時，請隨意點選任一站台就可以 (不用重複點選)": "Click any one of the mirrors below to install (no need to click more than one)",
    "綠野遊蹤自動安裝": "GTS (Green Wild Trails) Auto Install",
    "安卓 11(含) 以後：安裝示範影片：": "Android 11 and later: installation demo video: ",
    "安卓 10(含) 以前：安裝示範影片：": "Android 10 and earlier: installation demo video: ",
    "請點選下載，並手動安裝": "Click to download, then install manually",
    "DEM mix v2025, 請點選下載，並手動安裝": "DEM mix, v2025, click to download then install manually",
    "分開安裝": "Install separately",
    "圖資更新": "Map data update",
    "首次安裝": "First-time install",
    "更新": "Update",
    "手動下載自行安裝": "Manual download, install yourself",
    "手動安裝給 OruxMaps:": "Manual installation guide for OruxMaps:",
    "手動安裝給 Locus Map:": "Manual installation guide for Locus Map:",
    "疊圖專用 Styles": "Overlay-only styles",
    "給深色地圖疊圖 (例：衛星地圖)": "for dark-base map overlays (e.g. satellite imagery)",
    "給淡色地圖疊圖 (例：通用電子地圖)": "for light-base map overlays (e.g. general digital maps)",
    "給高度圖疊圖 (例：Relief Map)": "for elevation/relief map overlays",
    "給 Cartograph Extra 圖層疊圖": "for Cartograph Extra layer overlays",
    "（適合 PC/Mac BaseCamp）": " (for PC/Mac BaseCamp)",
    "Windows 平台:": "Windows platform:",
    "macOS 平台:": "macOS platform:",
    "## 版權宣告": "## Copyright Notice",
    "## 地圖版權與散佈說明": "## Map License and Distribution Notice",
    "本作品內含部份資訊取自「OpenStreetMap」": "This work contains information from “OpenStreetMap” ",
    "，該資料庫以開放資料庫授權條款 (Open Database License, ODbL) 進行提供。": ", made available under the Open Database License (ODbL).",
    "部分範圍的等高線與 HGT DEM 來自於JAXA AW3D30 v4.1。": "Contour lines and HGT DEM for part of this coverage area are derived from JAXA AW3D30 v4.1.",
    "使用檔案：": "Files used: ",
    "OruxMaps/綠野遊蹤/蛙弟/山林日誌": "OruxMaps / GTS / Wadi / HikingJournal",
    "OruxMaps (歐魯妹)": "OruxMaps",
    "山林日誌": "HikingJournal",
    "蛙弟": "Wadi",
    "綠野遊蹤": "GTS",
    "自動分流": "Auto-mirror",
}

# Fullwidth punctuation left over after the dictionary pass (mostly inside
# region-specific prose that a human/AI will overwrite anyway, but cleaned up
# here so the generated boilerplate itself never carries stray fullwidth marks).
EN_FULLWIDTH_PUNCT = {
    "。": ".",
    "，": ", ",
    "：": ": ",
    "「": '"',
    "」": '"',
    "（": " (",
    "）": ")",
    "、": ", ",
}


def translate_to_english(template):
    """Derive the English counterpart of a (still-Chinese, unformatted) template.

    Operates on the raw template text (before .format()), so {region}/
    {region_lower}/etc. placeholders and the empty Famous Peaks/Routes/Sights/
    Historical Events sections pass through untouched.
    """
    for zh, en in sorted(EN_TRANSLATIONS.items(), key=lambda kv: len(kv[0]), reverse=True):
        template = template.replace(zh, en)
    for zh, en in EN_FULLWIDTH_PUNCT.items():
        template = template.replace(zh, en)
    # The "Info pages" mirror links are self-referential; the English doc
    # should point readers at its own English mirror page, not the Chinese one.
    template = template.replace('_topo.html (mirror', '_topo-en.html (mirror')
    return template


# Template for the main documentation structure
TOPO_MD_TEMPLATE = """{title}
{title_underline}

AW3D30.OSM - {region} TOPO v__version__

適合用在 Garmin / Android / iOS 上的離線地圖。

## 地圖範圍

* 緯度範圍: Nxx.xx ~ Nyy.yy
* 經度範圍: Eaa.aa ~ Ebb.bb

請注意，以下介紹內容為 AI 產生，若有錯誤請回報到魯地圖社群，我們會儘快更正。謝謝！  ^^

### 著名的山頭 (Famous Peaks)

### 著名的健行路線 (Famous Trekking Routes)

### 著名景點

### 歷史事件

* 相關網頁
  * 魯地圖分流器 (Cedric Shih)
    * https://rudymap.tw/
  * 說明網頁:
    * https://moi.kcwu.csie.org/{region_lower}_topo.html (mirror kcwu)
    * https://map.happyman.idv.tw/rudy/{region_lower}_topo.html (mirror Happyman)
  * 使用討論（臉書社團）: https://www.facebook.com/groups/taiwan.topo
  * 開發網站（GitHub）: https://github.com/alpha-rudy/taiwan-topo

* ![山林日誌](images/hj.png =36x) 自動安裝
  * 請於 APP 內直接安裝地圖
    > 安裝示範影片：https://youtu.be/HP6BXKdBUvg
  * 主地圖，請貼網址: https://rudymap.tw/AW3D30_OSM_{region}_TOPO_Rudy.map.zip
  * 地圖樣式，請貼網址: https://rudymap.tw/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip
  * 地形渲染，請貼網址: https://rudymap.tw/{region_lower}_hgtmix.zip

* ![蛙弟](images/wadi.png =36x) 自動安裝
  * 點選下列連結來啟動安裝，也可於 APP 內直接下載來安裝地圖
    > 安裝示範影片：https://youtu.be/g8b15RPZ7nA
  * 傳統版
    * 三合一
      > [[自動分流]](wadi-all://rudymap.tw/AW3D30_OSM_{region}_TOPO_Rudy.zip) /
      > [[mirror kcwu]](wadi-all://moi.kcwu.csie.org/AW3D30_OSM_{region}_TOPO_Rudy.zip) /
      > [[mirror Happyman]](wadi-all://map.happyman.idv.tw/rudy/AW3D30_OSM_{region}_TOPO_Rudy.zip)
    * 離線地圖
      > [[自動分流]](wadi-map://rudymap.tw/AW3D30_OSM_{region}_TOPO_Rudy.map.zip) /
      > [[mirror kcwu]](wadi-map://moi.kcwu.csie.org/AW3D30_OSM_{region}_TOPO_Rudy.map.zip) /
      > [[mirror Happyman]](wadi-map://map.happyman.idv.tw/rudy/AW3D30_OSM_{region}_TOPO_Rudy.map.zip)
    * 風格主題 (0.4MB)
      > [[自動分流]](wadi-theme://rudymap.tw/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip) /
      > [[mirror kcwu]](wadi-theme://moi.kcwu.csie.org/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip) /
      > [[mirror Happyman]](wadi-theme://map.happyman.idv.tw/rudy/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip)
    * 高程檔
      > [[自動分流]](wadi-hgt://rudymap.tw/{region_lower}_hgtmix.zip) /
      > [[mirror kcwu]](wadi-hgt://moi.kcwu.csie.org/{region_lower}_hgtmix.zip) /
      > [[mirror Happyman]](wadi-hgt://map.happyman.idv.tw/rudy/{region_lower}_hgtmix.zip)

* ![綠野遊蹤](images/GTS.png =36x) 綠野遊蹤自動安裝
  * 安裝時，請隨意點選任一站台就可以 (不用重複點選)
    > 安裝示範影片：https://youtu.be/JsvP61CErYY
  * 傳統版
    * 三合一
      > [[自動分流]](gts-all://rudymap.tw/AW3D30_OSM_{region}_TOPO_Rudy.zip) /
      > [[mirror kcwu]](gts-all://moi.kcwu.csie.org/AW3D30_OSM_{region}_TOPO_Rudy.zip) /
      > [[mirror Happyman]](gts-all://map.happyman.idv.tw/rudy/AW3D30_OSM_{region}_TOPO_Rudy.zip)
    * 離線地圖
      > [[自動分流]](gts-map://rudymap.tw/AW3D30_OSM_{region}_TOPO_Rudy.map.zip) /
      > [[mirror kcwu]](gts-map://moi.kcwu.csie.org/AW3D30_OSM_{region}_TOPO_Rudy.map.zip) /
      > [[mirror Happyman]](gts-map://map.happyman.idv.tw/rudy/AW3D30_OSM_{region}_TOPO_Rudy.map.zip)
    * 風格主題 (0.4MB)
      > [[自動分流]](gts-mapthemes://rudymap.tw/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip) /
      > [[mirror kcwu]](gts-mapthemes://moi.kcwu.csie.org/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip) /
      > [[mirror Happyman]](gts-mapthemes://map.happyman.idv.tw/rudy/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip)
    * 高程檔
      > [[自動分流]](gts-hgt://rudymap.tw/{region_lower}_hgtmix.zip) /
      > [[mirror kcwu]](gts-hgt://moi.kcwu.csie.org/{region_lower}_hgtmix.zip) /
      > [[mirror Happyman]](gts-hgt://map.happyman.idv.tw/rudy/{region_lower}_hgtmix.zip)

* ![OruxMaps](images/OruxMaps.jpeg =36x) OruxMaps (歐魯妹) 自動安裝
  * 安裝時，請隨意點選任一站台就可以 (不用重複點選)
    > 安卓 11(含) 以後：安裝示範影片：https://youtu.be/8hwJr4jMsE0 <br />
    > 安卓 10(含) 以前：安裝示範影片：https://youtu.be/GbBaePfk4cE
  * ![Map](images/OruxMaps_map.jpeg =36x) Map
    > [[自動分流]](orux-map://rudymap.tw/AW3D30_OSM_{region}_TOPO_Rudy.map.zip) /
    > [[mirror kcwu]](orux-map://moi.kcwu.csie.org/AW3D30_OSM_{region}_TOPO_Rudy.map.zip) /
    > [[mirror Happyman]](orux-map://map.happyman.idv.tw/rudy/AW3D30_OSM_{region}_TOPO_Rudy.map.zip)
  * ![Style](images/OruxMaps_style.jpeg =36x) Style (0.4MB)
    > [[自動分流]](orux-mf-theme://rudymap.tw/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip) /
    > [[mirror kcwu]](orux-mf-theme://moi.kcwu.csie.org/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip) /
    > [[mirror Happyman]](orux-mf-theme://map.happyman.idv.tw/rudy/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip)
  * ![DEM](images/OruxMaps_dem.jpeg =36x) 請點選下載，並手動安裝
    > [[自動分流]](https://rudymap.tw/{region_lower}_hgtmix.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/{region_lower}_hgtmix.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/{region_lower}_hgtmix.zip)

* ![Locus Map](images/Locus.jpeg =36x) Locus Map 自動安裝
  * 安裝時，請隨意點選任一站台就可以 (不用重複點選)
    > 安裝示範影片：https://youtu.be/rb1Hb6dkGkw
  * 分開安裝
    * ![Map](images/Locus_map.jpeg =36x) Map
      > [[自動分流]](locus-actions://https/rudymap.tw/{region_lower}_map-cedric.xml) /
      > [[mirror kcwu]](locus-actions://http/moi.kcwu.csie.org/{region_lower}_map-kcwu.xml) /
      > [[mirror Happyman]](locus-actions://http/map.happyman.idv.tw/rudy/{region_lower}_map-happyman.xml)
    * ![Style](images/Locus_style.jpeg =36x) Style (0.4MB)
      > [[自動分流]](locus-actions://https/rudymap.tw/locus_style-cedric.xml) /
      > [[mirror kcwu]](locus-actions://http/moi.kcwu.csie.org/locus_style-kcwu.xml) /
      > [[mirror Happyman]](locus-actions://http/map.happyman.idv.tw/rudy/locus_style-happyman.xml)
    * ![DEM](images/Locus_dem.jpeg =36x) DEM mix, v2025
      > [[自動分流]](locus-actions://https/rudymap.tw/{region_lower}_dem-cedric.xml) /
      > [[mirror kcwu]](locus-actions://http/moi.kcwu.csie.org/{region_lower}_dem-kcwu.xml) /
      > [[mirror Happyman]](locus-actions://http/map.happyman.idv.tw/rudy/{region_lower}_dem-happyman.xml)
  * 圖資更新
    * ![Map](images/Locus.jpeg =36x) 更新
      > [[自動分流]](locus-actions://https/rudymap.tw/{region_lower}_upgrade-cedric.xml) /
      > [[mirror kcwu]](locus-actions://http/moi.kcwu.csie.org/{region_lower}_upgrade-kcwu.xml) /
      > [[mirror Happyman]](locus-actions://http/map.happyman.idv.tw/rudy/{region_lower}_upgrade-happyman.xml)
  * 三合一
    * ![Map](images/Locus.jpeg =36x) 首次安裝
      > [[自動分流]](locus-actions://https/rudymap.tw/{region_lower}_all-cedric.xml) /
      > [[mirror kcwu]](locus-actions://http/moi.kcwu.csie.org/{region_lower}_all-kcwu.xml) /
      > [[mirror Happyman]](locus-actions://http/map.happyman.idv.tw/rudy/{region_lower}_all-happyman.xml)

* ![Cartograph](images/Cartograph.png =36x) iOS/Android Cartograph Maps 自動安裝
  * 安裝時，請隨意點選任一站台就可以 (不用重複點選)
    > 安裝示範影片：https://youtu.be/FDa2Qb9wxUY
  * 分開安裝
    * ![Map](images/Cartograph_map.png =36x) Map
      > [[自動分流]](cartograph-map://rudymap.tw/{region}_carto_map.cpkg) /
      > [[mirror kcwu]](cartograph-map://moi.kcwu.csie.org/{region}_carto_map.cpkg) /
      > [[mirror Happyman]](cartograph-map://map.happyman.idv.tw/rudy/{region}_carto_map.cpkg)
    * ![Style](images/Cartograph_style.png =36x) Style (0.4MB)
      > [[自動分流]](cartograph-map://rudymap.tw/{region}_carto_style.cpkg) /
      > [[mirror kcwu]](cartograph-map://moi.kcwu.csie.org/{region}_carto_style.cpkg) /
      > [[mirror Happyman]](cartograph-map://map.happyman.idv.tw/rudy/{region}_carto_style.cpkg)
    * ![DEM](images/Cartograph_dem.png =36x) DEM mix v2025, 請點選下載，並手動安裝
      > [[自動分流]](cartograph-map://rudymap.tw/{region}_carto_dem.cpkg) /
      > [[mirror kcwu]](cartograph-map://moi.kcwu.csie.org/{region}_carto_dem.cpkg) /
      > [[mirror Happyman]](cartograph-map://map.happyman.idv.tw/rudy/{region}_carto_dem.cpkg)
  * 圖資更新
    * ![Map](images/Cartograph.png =36x) 更新
      > [[自動分流]](cartograph-map://rudymap.tw/{region}_carto_upgrade.cpkg) /
      > [[mirror kcwu]](cartograph-map://moi.kcwu.csie.org/{region}_carto_upgrade.cpkg) /
      > [[mirror Happyman]](cartograph-map://map.happyman.idv.tw/rudy/{region}_carto_upgrade.cpkg)
  * 三合一
    * ![Map](images/Cartograph.png =36x) 首次安裝
      > [[自動分流]](cartograph-map://rudymap.tw/{region}_carto_all.cpkg) /
      > [[mirror kcwu]](cartograph-map://moi.kcwu.csie.org/{region}_carto_all.cpkg) /
      > [[mirror Happyman]](cartograph-map://map.happyman.idv.tw/rudy/{region}_carto_all.cpkg)

* ![Android](images/Android.png =36x)![iOS](images/macOS.png =36x) Mapsforge 手動下載自行安裝
  * 安裝時，請隨意點選任一站台就可以 (不用重複點選)
    > * 手動安裝給 OruxMaps: https://www.facebook.com/groups/taiwan.topo/permalink/702707949884821
    > * 手動安裝給 Locus Map: https://www.facebook.com/groups/taiwan.topo/permalink/703483796473903
  * ![Map](images/Android.png =36x) ![iOS](images/macOS.png =36x) Map
    > [[自動分流]](https://rudymap.tw/AW3D30_OSM_{region}_TOPO_Rudy.map.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/AW3D30_OSM_{region}_TOPO_Rudy.map.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/AW3D30_OSM_{region}_TOPO_Rudy.map.zip)
  * ![POIv3](images/Android.png =36x) OruxMaps/綠野遊蹤/蛙弟/山林日誌 POIv3
    > [[自動分流]](https://rudymap.tw/AW3D30_OSM_{region}_TOPO_Rudy.poi.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/AW3D30_OSM_{region}_TOPO_Rudy.poi.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/AW3D30_OSM_{region}_TOPO_Rudy.poi.zip)
  * ![POIv2](images/Android.png =36x) Cartograph POIv2
    > [[自動分流]](https://rudymap.tw/AW3D30_OSM_{region}_TOPO_Rudy_v2.poi.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/AW3D30_OSM_{region}_TOPO_Rudy_v2.poi.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/AW3D30_OSM_{region}_TOPO_Rudy_v2.poi.zip)
  * ![LOCUS_POI](images/Android.png =36x) Locus POI
    > [[自動分流]](https://rudymap.tw/AW3D30_OSM_{region}_TOPO_Rudy.db.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/AW3D30_OSM_{region}_TOPO_Rudy.db.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/AW3D30_OSM_{region}_TOPO_Rudy.db.zip)
  * ![Style](images/Android.png =36x) OruxMaps/綠野遊蹤/蛙弟/山林日誌 Style (0.4MB)
    > [[自動分流]](https://rudymap.tw/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip)
  * ![Style](images/Android.png =36x) Locus Style (0.4MB)
    > [[自動分流]](https://rudymap.tw/MOI_OSM_Taiwan_TOPO_Rudy_locus_style.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/MOI_OSM_Taiwan_TOPO_Rudy_locus_style.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/MOI_OSM_Taiwan_TOPO_Rudy_locus_style.zip)
  * ![Android](images/Android.png =36x)![iOS](images/macOS.png =36x) Cartograph Maps Style (0.4MB)
    > [[自動分流]](https://rudymap.tw/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/MOI_OSM_Taiwan_TOPO_Rudy_hs_style.zip)
  * ![DEM](images/Android.png =36x)![iOS](images/macOS.png =36x) 30m HGT
    > [[自動分流]](https://rudymap.tw/{region_lower}_hgtmix.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/{region_lower}_hgtmix.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/{region_lower}_hgtmix.zip)
  * 疊圖專用 Styles
    * BN Style, 給深色地圖疊圖 (例：衛星地圖) (0.4MB)
      > [[自動分流]](https://rudymap.tw/MOI_OSM_bn_style.zip) /
      > [[mirror kcwu]](https://moi.kcwu.csie.org/MOI_OSM_bn_style.zip) /
      > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/MOI_OSM_bn_style.zip)
    * DN Style, 給淡色地圖疊圖 (例：通用電子地圖) (0.4MB)
      > [[自動分流]](https://rudymap.tw/MOI_OSM_dn_style.zip) /
      > [[mirror kcwu]](https://moi.kcwu.csie.org/MOI_OSM_dn_style.zip) /
      > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/MOI_OSM_dn_style.zip)
    * TN Style, 給高度圖疊圖 (例：Relief Map) (0.4MB)
      > [[自動分流]](https://rudymap.tw/MOI_OSM_tn_style.zip) /
      > [[mirror kcwu]](https://moi.kcwu.csie.org/MOI_OSM_tn_style.zip) /
      > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/MOI_OSM_tn_style.zip)
    * Extra Style, 給 Cartograph Extra 圖層疊圖 (0.4MB)
      > [[自動分流]](https://rudymap.tw/MOI_OSM_extra_style.zip) /
      > [[mirror kcwu]](https://moi.kcwu.csie.org/MOI_OSM_extra_style.zip) /
      > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/MOI_OSM_extra_style.zip)

* ![Map](images/Garmin.png =x36) Garmin MOI.OSM.camp3D - {title}（適合 PC/Mac BaseCamp）
  * 安裝時，請隨意點選任一站台就可以 (不用重複點選)
    > * Windows 平台: https://www.facebook.com/groups/taiwan.topo/permalink/726308367524779
    > * macOS 平台: https://www.facebook.com/groups/taiwan.topo/permalink/726303937525222
  * ![Map](images/Garmin_large.jpeg =36x) camp3D
    > [[自動分流]](https://rudymap.tw/gmapsupp_{region}_aw3d30_zh_camp3D.img.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/gmapsupp_{region}_aw3d30_zh_camp3D.img.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/gmapsupp_{region}_aw3d30_zh_camp3D.img.zip)
  * ![Map](images/Windows.png =36x) camp3D
    > [[自動分流]](https://rudymap.tw/Install_AW3D30_{region}_TOPO_camp3D.exe) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/Install_AW3D30_{region}_TOPO_camp3D.exe) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/Install_AW3D30_{region}_TOPO_camp3D.exe)
  * ![Map](images/macOS.png =36x) camp3D
    > [[自動分流]](https://rudymap.tw/{region}_aw3d30_zh_camp3D.gmap.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/{region}_aw3d30_zh_camp3D.gmap.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/{region}_aw3d30_zh_camp3D.gmap.zip)

* ![Map](images/Garmin.png =x36) Garmin English Maps - {title}
  * Clip on one of mirrors to download
    > * Installation demo on Windows: https://www.facebook.com/groups/taiwan.topo/permalink/726308367524779
    > * Installation demo on macOS: https://www.facebook.com/groups/taiwan.topo/permalink/726303937525222
  * ![Map](images/Garmin_large.jpeg =36x) camp3D
    > [[自動分流]](https://rudymap.tw/gmapsupp_{region}_aw3d30_en_camp3D.img.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/gmapsupp_{region}_aw3d30_en_camp3D.img.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/gmapsupp_{region}_aw3d30_en_camp3D.img.zip)
  * ![Map](images/Windows.png =36x) en_camp3D
    > [[自動分流]](https://rudymap.tw/Install_AW3D30_{region}_TOPO_camp3D_en.exe) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/Install_AW3D30_{region}_TOPO_camp3D_en.exe) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/Install_AW3D30_{region}_TOPO_camp3D_en.exe)
  * ![Map](images/macOS.png =36x) en_camp3D
    > [[自動分流]](https://rudymap.tw/{region}_aw3d30_en_camp3D.gmap.zip) /
    > [[mirror kcwu]](https://moi.kcwu.csie.org/{region}_aw3d30_en_camp3D.gmap.zip) /
    > [[mirror Happyman]](https://map.happyman.idv.tw/rudy/{region}_aw3d30_en_camp3D.gmap.zip)

## 版權宣告

* OpenSteetMap
> © OpenStreetMap contributors <br />
> 本作品內含部份資訊取自「OpenStreetMap」[https://wiki.openstreetmap.org/wiki/Downloading_data](https://wiki.openstreetmap.org/wiki/Downloading_data)，該資料庫以開放資料庫授權條款 (Open Database License, ODbL) 進行提供。 <br />
> License: http://www.openstreetmap.org/copyright

* JAXA ALOS World 3D - 30m (AW3D30) Version 4.1
> 部分範圍的等高線與 HGT DEM 來自於JAXA AW3D30 v4.1。 <br /> 
> 使用檔案：{hgt_files}。 <br />
> Link: http://www.eorc.jaxa.jp/ALOS/en/aw3d30/index.htm

* GMAP Styles and TYP
> Garmin GMAP Styles and TYPs are origin from Freizeitkarte. <br />
> Link: http://www.freizeitkarte-osm.de/garmin/en/index.html

* Mapsforge Style
> Symbols/patterns/code is derived and based on OpenAndroMaps Elevate theme by Tobias Kühn. <br />
> Link: http://www.openandromaps.org/en/legend/elevate-mountain-hike-theme <br />
> Detail Link: http://www.openandromaps.org/wp-content/users/tobias/licenses.txt <br />
> Theme style is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike License 3.0 Unported License. <br />
> Link: http://creativecommons.org/licenses/by-nc-sa/3.0/

* Tool of Contour Lines: gdal and phyghtmap
> Contour lines of this map were generated by using tools "gdal" and "phyghtmap". <br />
> gdal Link: http://www.gdal.org <br />
> gdal License: http://svn.osgeo.org/gdal/trunk/gdal/LICENSE.TXT <br />
> phyghtmap Link: http://katze.tfiu.de/projects/phyghtmap/ <br />
> phyghtmap License: http://gnu.org/licenses/gpl.html

* Tools of Maps: osm, mkgmap, and mapsforge
> OSM Maps were built using the tools "osmosis" <br />
> Link: http://wiki.openstreetmap.org/wiki/Osmosis <br />
> GMAP Maps were built using the tools "splitter" and "mkgmap" <br />
> Link: http://www.mkgmap.org.uk/ <br />
> License: http://gnu.org/licenses/gpl.html <br />
> Mapsforge Maps were built using the tools "Mapsforge Map-Writer" <br />
> Link: https://github.com/mapsforge/mapsforge/blob/master/docs/Getting-Started-Map-Writer.md

## 地圖版權與散佈說明

    Copyright (c) 2025-2026 Rudy Chung
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

        * Redistributions of source code must retain the above copyright
        notice, this list of conditions and the following disclaimer.

        * Redistributions in binary form must reproduce the this copyright notice
        (or the HTTP link to this notice), this list of conditions and the
        following disclaimer in the documentation and/or other materials provided
        with the distribution.

        * Redistributions with modification must use a different map name which
        could be easily and clearly to be distinguished with this map.

        * Neither the name of Rudy Chung nor the names of its contributors may be
        used to endorse or promote products derived from this software without 
        specific prior written permission.

    THIS MAP IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL RUDY BE LIABLE FOR ANY
    DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
    ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    MAP, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


@click.command()
@click.option('--region', required=True, help='Region name (e.g., Everest)')
@click.option('--region-lower', required=True, help='Region name lowercase (e.g., everest)')
@click.option('--title', required=True, help='Full title for documentation (e.g., Everest Region Climbing Map)')
@click.option('--lang', required=False, hidden=True, default=None, help='Deprecated: native language code (no longer used for URLs)')
@click.option('--hgt-files', default='N28E83, N28E84', help='HGT DEM files used (e.g., N28E83, N28E84)')
@click.option('--no-elevation', is_flag=True, default=False,
              help='Region without contours/HGT: strip all HGT/DEM/contour/CartoType '
                   'download blocks and credits, and drop the DEM_NAME token / use "camp" style')
@click.option('--dry-run', is_flag=True, default=False, help='Show what would be created without creating files')
def main(region, region_lower, title, lang, hgt_files, no_elevation, dry_run):
    """Generate documentation markdown for a new TOPO map region."""

    print(f"\n{'=' * 70}")
    print(f"Generating Documentation: {region} ({region_lower})")
    print(f"{'=' * 70}\n")

    # Generate title underline
    title_underline = "=" * len(title)

    # Strip elevation-specific blocks and rewrite DEM/style file-name tokens first
    # (operates on the raw template so the {region}/{region_lower} placeholders are
    # still intact), then format.
    if no_elevation:
        template = rename_no_elevation(strip_elevation_blocks(TOPO_MD_TEMPLATE))
    else:
        template = TOPO_MD_TEMPLATE

    # Derive the English template from the (already stripped/renamed) Chinese
    # one before formatting, so both files share the same no-elevation shape.
    template_en = translate_to_english(template)

    fmt_kwargs = dict(
        title=title,
        title_underline=title_underline,
        region=region,
        region_lower=region_lower,
        hgt_files=hgt_files,
    )

    # Format both templates with the same variables
    content = template.format(**fmt_kwargs)
    content_en = template_en.format(**fmt_kwargs)

    # Create directory
    doc_dir = f"docs/{region}"
    filename = f"{doc_dir}/{region_lower}_topo.md"
    filename_en = f"{doc_dir}/{region_lower}_topo-en.md"

    print(f"Files to be created:\n")
    print(f"  ✓ {filename} ({content.count(chr(10))} lines)")
    print(f"  ✓ {filename_en} ({content_en.count(chr(10))} lines)")

    if not dry_run:
        os.makedirs(doc_dir, exist_ok=True)
        with open(filename, 'w') as f:
            f.write(content)
        with open(filename_en, 'w') as f:
            f.write(content_en)

    print(f"\n{'=' * 70}")

    if dry_run:
        print("✓ Dry run completed - no files were created")
        print("\nTo create files, run without --dry-run:")
        print(f"  python3 tools/generate_topo_md.py \\")
        print(f"    --region {region} \\")
        print(f"    --region-lower {region_lower} \\")
        print(f"    --title '{title}' \\")
        print(f"    --hgt-files '{hgt_files}'")
    else:
        print(f"✓ Documentation created successfully!")
        print(f"\nCreated: {filename}")
        print(f"Created: {filename_en}")
        print(f"\nNote: Famous Peaks/Trekking Routes/Sights/Historical Events sections")
        print(f"are left empty in both files — fill in {filename} first, then write an")
        print(f"English translation of that content into {filename_en} (see")
        print(f"docs/ADDING_NEW_REGION.md).")

    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
