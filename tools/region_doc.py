"""Assemble TOPO region documentation from structured TOML metadata + prose guides.

Zero external dependencies (Python 3.11+ stdlib ``tomllib``).

This module serves two purposes:
1. Build the canonical Markdown for any overseas region defined by
   ``docs/<Region>/region.toml`` + ``guide.md`` (or ``guide-en.md``) together
   with site-wide metadata in ``docs/shared/site.toml``.
2. Expand ``<!-- include: <name> -->`` directives inside hand-authored Markdown
   pages (``docs/Taiwan/taiwan_topo*.md`` and ``docs/Taiwan/beta.md``) so that
   mirrors, license text, common credits, and the overseas region index all
   come from a single source of truth.
"""

from __future__ import annotations

import math
import re
import tomllib
import zipfile
from pathlib import Path
from typing import Any

_INCLUDE_RE = re.compile(r"^[ \t]*<!--\s*include:\s*([a-z0-9_:-]+)\s*-->[ \t]*$", re.MULTILINE)


# ---------------------------------------------------------------------------
# UI / boilerplate i18n dictionary (keyed cleanly, no substring .replace())
# ---------------------------------------------------------------------------

_UI: dict[str, dict[str, str]] = {
    "zh": {
        "subtitle": "適合用在 Garmin / Android / iOS 上的離線地圖。",
        "taiwan_home_label": "台灣主頁",
        "taiwan_home_href": "./taiwan_topo.html",
        "legend_label": "圖例",
        "tiles_label": "線上圖磚",
        "app_label": "手機專頁",
        "fb_label": "臉書社團",
        "sec_mobile": "手機 App 自動安裝",
        "quick_guide_title": "新手選版指南",
        "quick_guide_phone": "若您正用手機瀏覽，也可直接前往手機離線 APP 專用頁：",
        "quick_guide_elev": "首次安裝建議直接選擇「三合一」（含離線地圖、風格主題與高程檔）；日後更新圖資只需更新「離線地圖／更新」即可。",
        "quick_guide_no_elev": "首次安裝請同時安裝「離線地圖」與「風格主題」（本區為城市平面圖，無高程檔）；日後更新圖資只需更新「離線地圖／更新」即可。",
        "auto_mirror": "自動分流",
        "hj_title": "![山林日誌](images/hj.png =36x) 山林日誌（iOS）",
        "hj_note": "請於 APP 內直接安裝地圖",
        "video_prefix": "安裝示範影片：",
        "hj_map": "主地圖，請貼網址:",
        "hj_style": "地圖樣式，請貼網址:",
        "hj_dem": "地形渲染，請貼網址:",
        "wadi_title": "![蛙弟](images/wadi.png =36x) 蛙弟（iOS / Android）",
        "wadi_note": "點選下列連結來啟動安裝，也可於 APP 內直接下載來安裝地圖",
        "classic": "傳統版",
        "all_in_one": "三合一",
        "offline_map": "離線地圖",
        "style_theme": "風格主題",
        "dem_file": "高程檔",
        "gts_title": "![綠野遊蹤](images/GTS.png =36x) 綠野遊蹤（Android）",
        "tap_install": "安裝時，點選下方連結即可",
        "orux_title": "![OruxMaps](images/OruxMaps.jpeg =36x) OruxMaps 歐魯妹（Android）",
        "orux_v11": "安卓 11(含) 以後：安裝示範影片：",
        "orux_v10": "安卓 10(含) 以前：安裝示範影片：",
        "orux_dem_label": "請點選下載，並手動安裝",
        "locus_title": "![Locus Map](images/Locus.jpeg =36x) Locus Map（Android）",
        "all_in_one_rec": "三合一（推薦首次安裝）",
        "first_install": "首次安裝",
        "map_update": "圖資更新",
        "update": "更新",
        "install_sep": "分開安裝",
        "carto_title": "![Cartograph](images/Cartograph.png =36x) Cartograph Maps（iOS / Android）",
        "carto_dem_label": "DEM, aw3d30-4.1, 請點選下載，並手動安裝",
        "sec_garmin": "![Garmin](images/Garmin.png =x36) Garmin 離線地圖",
        "garmin_guide_title": "選檔說明與安裝教學",
        "garmin_formats": "**檔案格式**：`.img.zip` 供 Garmin 手持機／手錶直接解壓放進裝置；`.exe` 供 Windows BaseCamp 安裝；`.gmap.zip` 供 macOS BaseCamp 安裝。",
        "garmin_win": "Windows 安裝示範：",
        "garmin_mac": "macOS 安裝示範：",
        "basecamp_note": "（適合 PC/Mac BaseCamp）",
        "sec_manual": "![Android](images/Android.png =36x)![iOS](images/macOS.png =36x) Mapsforge 手動下載自行安裝",
        "manual_guide_title": "手動安裝教學",
        "manual_orux": "手動安裝給 OruxMaps：",
        "manual_locus": "手動安裝給 Locus Map：",
        "sub_map_dem": "主地圖與高程檔 (Map & DEM)",
        "sub_map_only": "主地圖 (Map)",
        "sub_poi": "離線搜尋地標 (POI)",
        "sub_style": "標準風格主題 (Style)",
        "sub_overlay": "疊圖專用風格 (Overlay Styles)",
        "apps_combo": "OruxMaps/綠野遊蹤/蛙弟/山林日誌",
        "overlay_bn": "BN Style, 給深色地圖疊圖 (例：衛星地圖)",
        "overlay_dn": "DN Style, 給淡色地圖疊圖 (例：通用電子地圖)",
        "overlay_tn": "TN Style, 給高度圖疊圖 (例：Relief Map)",
        "overlay_extra": "Extra Style, 給 Cartograph Extra 圖層疊圖",
        "sec_pmtiles": "PMTiles 向量圖磚",
        "pmtiles_intro_title": "適用支援 MapLibre / PMTiles 的離線地圖 App 與網頁檢視器",
        "pmtiles_intro_elev": "隨地圖同步產出向量圖磚、全區共用風格檔（含原版與紙本風格）與 Terrarium 高程圖磚。",
        "pmtiles_intro_no_elev": "隨地圖同步產出向量圖磚與全區共用風格檔（含原版與紙本風格；本區為城市平面圖，無高程圖磚）。",
        "pmtiles_vec": "向量圖磚",
        "pmtiles_style": "PMTiles 共用風格主題包（含 style.json、paper.json、圖示與英數字型）",
        "pmtiles_dem": "DEM 高程圖磚",
        "sec_guide_region": "地圖範圍與地區介紹",
        "sec_guide_city": "地圖範圍與城市介紹",
        "lat_label": "緯度範圍",
        "lon_label": "經度範圍",
        "ai_notice": "請注意，以下介紹內容為 AI 產生，若有錯誤請回報到魯地圖社群，我們會儘快更正。謝謝！  ^^",
        "sec_resources": "相關資源與鏡像站",
        "res_home": "魯地圖主頁（含全區清單）：[魯地圖 Taiwan TOPO](./taiwan_topo.html)",
        "res_legend": "地圖圖例（自動同步產生）：[互動檢索網頁](./legend.html) · [詳細版 PDF](./legend_detail.pdf) · [2 頁速查表 PDF](./legend_compact.pdf) · [1 頁速查表 PDF](./legend_onepage.pdf)",
        "res_tiles": "線上圖磚服務：",
        "res_fb": "使用討論（臉書社團）：",
        "res_github": "開發網站（GitHub）：",
        "mirrors_heading": "魯地圖鏡像站",
        "sec_copyright": "版權宣告",
        "aw3d30_desc": "部分範圍的等高線與 HGT DEM 來自於JAXA AW3D30 v4.1。",
        "aw3d30_files": "使用檔案：{files}。",
        "sec_license": "地圖版權與散佈說明",
        "index_coverage": "地圖範圍：",
    },
    "en": {
        "subtitle": "An offline map for Garmin / Android / iOS.",
        "taiwan_home_label": "Taiwan Main Page",
        "taiwan_home_href": "./taiwan_topo-en.html",
        "legend_label": "Legend",
        "tiles_label": "Online Tiles",
        "app_label": "Mobile App Page",
        "fb_label": "Facebook Group",
        "sec_mobile": "Mobile App Auto Install",
        "quick_guide_title": "Quick selection guide",
        "quick_guide_phone": "Browsing on a phone? You can also use the dedicated mobile app install page: ",
        "quick_guide_elev": "For a first-time setup, pick **All-in-one** (includes offline map, style theme, and elevation DEM). For later updates, you only need to update the map.",
        "quick_guide_no_elev": "For a first-time setup, install both the **Offline map** and the **Style theme** (this urban map has no elevation/DEM file). For later updates, you only need to update the map.",
        "auto_mirror": "Auto-mirror",
        "hj_title": "![HikingJournal](images/hj.png =36x) HikingJournal (iOS)",
        "hj_note": "Install the map directly within the app",
        "video_prefix": "Installation demo video: ",
        "hj_map": "Main map, paste this URL:",
        "hj_style": "Map style, paste this URL:",
        "hj_dem": "Terrain relief, paste this URL:",
        "wadi_title": "![Wadi](images/wadi.png =36x) Wadi (iOS / Android)",
        "wadi_note": "Tap one of the links below to trigger installation, or download and install directly within the app",
        "classic": "Classic version",
        "all_in_one": "All-in-one",
        "offline_map": "Offline map",
        "style_theme": "Style theme",
        "dem_file": "Elevation (DEM) file",
        "gts_title": "![GTS](images/GTS.png =36x) GTS — Green Wild Trails (Android)",
        "tap_install": "Click the link below to install",
        "orux_title": "![OruxMaps](images/OruxMaps.jpeg =36x) OruxMaps (Android)",
        "orux_v11": "Android 11 and later: installation demo video: ",
        "orux_v10": "Android 10 and earlier: installation demo video: ",
        "orux_dem_label": "Click to download, then install manually",
        "locus_title": "![Locus Map](images/Locus.jpeg =36x) Locus Map (Android)",
        "all_in_one_rec": "All-in-one (recommended for first-time setup)",
        "first_install": "First-time install",
        "map_update": "Map data update",
        "update": "Update",
        "install_sep": "Install separately",
        "carto_title": "![Cartograph](images/Cartograph.png =36x) Cartograph Maps (iOS / Android)",
        "carto_dem_label": "DEM, aw3d30-4.1, click to download then install manually",
        "sec_garmin": "![Garmin](images/Garmin.png =x36) Garmin Offline Maps",
        "garmin_guide_title": "File guide & installation demos",
        "garmin_formats": "**Formats**: `.img.zip` for direct install on Garmin handhelds/watches; `.exe` for Windows BaseCamp; `.gmap.zip` for macOS BaseCamp.",
        "garmin_win": "Installation demo on Windows: ",
        "garmin_mac": "Installation demo on macOS: ",
        "basecamp_note": " (for PC/Mac BaseCamp)",
        "sec_manual": "![Android](images/Android.png =36x)![iOS](images/macOS.png =36x) Mapsforge Manual Download",
        "manual_guide_title": "Installation guides",
        "manual_orux": "Manual installation guide for OruxMaps: ",
        "manual_locus": "Manual installation guide for Locus Map: ",
        "sub_map_dem": "Map & Elevation (Map & DEM)",
        "sub_map_only": "Offline Map (Map)",
        "sub_poi": "Offline Search POI",
        "sub_style": "Standard Style Themes",
        "sub_overlay": "Overlay-only Styles",
        "apps_combo": "OruxMaps / GTS / Wadi / HikingJournal",
        "overlay_bn": "BN Style, for dark-base map overlays (e.g. satellite imagery)",
        "overlay_dn": "DN Style, for light-base map overlays (e.g. general digital maps)",
        "overlay_tn": "TN Style, for elevation/relief map overlays",
        "overlay_extra": "Extra Style, for Cartograph Extra layer overlays",
        "sec_pmtiles": "PMTiles Vector Tiles",
        "pmtiles_intro_title": "For MapLibre / PMTiles-compatible offline apps and web viewers",
        "pmtiles_intro_elev": "Published alongside the Mapsforge release, including vector tiles, the shared style bundle (classic + paper styles), and Terrarium DEM tiles.",
        "pmtiles_intro_no_elev": "Published alongside the Mapsforge release, including vector tiles and the shared style bundle (classic + paper styles; this urban map has no DEM tiles).",
        "pmtiles_vec": "Vector Tiles",
        "pmtiles_style": "Shared PMTiles Style Bundle (style.json, paper.json, sprites & Latin glyphs)",
        "pmtiles_dem": "DEM Elevation Tiles",
        "sec_guide_region": "Map Coverage & Region Guide",
        "sec_guide_city": "Map Coverage & City Guide",
        "lat_label": "Latitude range",
        "lon_label": "Longitude range",
        "ai_notice": "Note: the descriptions below were AI-generated. Please report any errors to the RudyMap community and we'll fix them as soon as possible. Thanks!  ^^",
        "sec_resources": "Related Resources & Mirrors",
        "res_home": "Taiwan main page (all regions): [RudyMap Taiwan TOPO](./taiwan_topo-en.html)",
        "res_legend": "Map Legend (auto-generated): [Interactive Web Legend](./legend.html) · [Detailed PDF](./legend_detail.pdf) · [2-Page Compact PDF](./legend_compact.pdf) · [1-Page Cheat Sheet PDF](./legend_onepage.pdf)",
        "res_tiles": "Online tile service: ",
        "res_fb": "Discussion (Facebook Group): ",
        "res_github": "Development site (GitHub): ",
        "mirrors_heading": "RudyMap Mirrors",
        "sec_copyright": "Copyright Notice",
        "aw3d30_desc": "Contour lines and HGT DEM for part of this coverage area are derived from JAXA AW3D30 v4.1.",
        "aw3d30_files": "Files used: {files}.",
        "sec_license": "Map License and Distribution Notice",
        "index_coverage": "Map coverage:",
    },
}


def _lang_key(lang: str) -> str:
    return "en" if lang.lower().startswith("en") else "zh"


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        return tomllib.load(f)


def load_site_config(docs_dir: Path) -> dict[str, Any]:
    return load_toml(docs_dir / "shared" / "site.toml")


def _format_coord_range(low_raw: str, high_raw: str, pos_hem: str, neg_hem: str) -> str:
    """Format a pair of decimal degrees from a suite .mk into ``N34.30 ~ N35.95``."""

    def _dec_places(s: str) -> int:
        return len(s.split(".", 1)[1]) if "." in s else 0

    prec = max(_dec_places(low_raw), _dec_places(high_raw))

    def _fmt(s: str) -> str:
        val = float(s)
        hem = neg_hem if val < 0 else pos_hem
        return f"{hem}{abs(val):.{prec}f}"

    return f"{_fmt(low_raw)} ~ {_fmt(high_raw)}"


def _hgt_tiles_from_zip(zip_path: Path) -> list[str]:
    """Read actual ``.hgt`` tile names from a real HGT zip (skips Git LFS pointers)."""
    if not zip_path.exists() or not zipfile.is_zipfile(zip_path):
        return []
    with zipfile.ZipFile(zip_path) as zf:
        return sorted({Path(name).stem.upper() for name in zf.namelist() if name.lower().endswith(".hgt")})


def _hgt_tiles_from_bbox(bottom: float, top: float, left: float, right: float) -> list[str]:
    """Infer 1x1 degree HGT tile names covering ``[bottom, top] x [left, right]``."""
    lat_lo = math.floor(bottom)
    lat_hi = math.ceil(top) - 1 if top == int(top) and top > bottom else math.floor(top)
    lon_lo = math.floor(left)
    lon_hi = math.ceil(right) - 1 if right == int(right) and right > left else math.floor(right)
    tiles: list[str] = []
    for lat in range(lat_lo, lat_hi + 1):
        lat_tag = f"{'S' if lat < 0 else 'N'}{abs(lat):02d}"
        for lon in range(lon_lo, lon_hi + 1):
            lon_tag = f"{'W' if lon < 0 else 'E'}{abs(lon):03d}"
            tiles.append(f"{lat_tag}{lon_tag}")
    return tiles


def parse_suite_mk(repo_root: Path, suite: str) -> dict[str, Any]:
    """Read build facts (REGION, bounds, HGT, TARGETS) from ``suites/<suite>/<suite>.mk``."""
    mk_path = repo_root / "suites" / suite / f"{suite}.mk"
    if not mk_path.exists():
        return {}

    content = mk_path.read_text(encoding="utf-8")
    mk_vars: dict[str, str] = {}
    for m in re.finditer(r"^([A-Z_]+)\s*:?=\s*(.+?)\s*$", content, re.MULTILINE):
        mk_vars[m.group(1)] = m.group(2)

    facts: dict[str, Any] = {}
    if "REGION" in mk_vars:
        facts["region"] = mk_vars["REGION"]
    facts["elevation"] = "HGT" in mk_vars or "ELEVATION_FILE" in mk_vars
    if "BOTTOM" in mk_vars and "TOP" in mk_vars:
        facts["lat"] = _format_coord_range(mk_vars["BOTTOM"], mk_vars["TOP"], "N", "S")
    if "LEFT" in mk_vars and "RIGHT" in mk_vars:
        facts["lon"] = _format_coord_range(mk_vars["LEFT"], mk_vars["RIGHT"], "E", "W")
    if facts["elevation"]:
        hgt_raw = mk_vars.get("HGT", "")
        hgt_zip = (
            Path(hgt_raw.replace("$(ROOT_DIR)", str(repo_root)))
            if hgt_raw
            else repo_root / "hgt" / f"{suite}_hgtmix.zip"
        )
        tiles = _hgt_tiles_from_zip(hgt_zip)
        if not tiles and all(k in mk_vars for k in ("BOTTOM", "TOP", "LEFT", "RIGHT")):
            tiles = _hgt_tiles_from_bbox(
                float(mk_vars["BOTTOM"]),
                float(mk_vars["TOP"]),
                float(mk_vars["LEFT"]),
                float(mk_vars["RIGHT"]),
            )
        if tiles:
            facts["hgt_files"] = ", ".join(tiles)
    if "TARGETS" in mk_vars:
        targets = set(mk_vars["TARGETS"].split())
        facts["has_gts"] = "gts_all" in targets
        facts["has_carto"] = "carto_all" in targets
        facts["has_pmtiles"] = "pmtiles" in targets
        facts["has_dem_pmtiles"] = "dem" in targets
    return facts


def load_region_config(region_toml: Path, docs_dir: Path | None = None) -> dict[str, Any]:
    """Load ``region.toml`` merged with build facts from ``suites/<suite>/<suite>.mk``.

    ``suites/<suite>/<suite>.mk`` is the single source of truth for build facts
    (``region``, ``elevation``, ``lat``, ``lon``, and ``TARGETS``); explicit keys
    in ``region.toml`` override them if ever needed.
    """
    raw = load_toml(region_toml)
    root = docs_dir.resolve().parent if docs_dir is not None else region_toml.resolve().parent.parent.parent
    suite = raw.get("suite")
    mk_facts = parse_suite_mk(root, suite) if suite else {}
    merged = {**mk_facts, **raw}
    merged.setdefault("region", region_toml.parent.name)
    return merged


def _sz(sizes: dict[str, str], key: str, default: str = "") -> str:
    val = sizes.get(key, default)
    return f" ({val})" if val else ""


# ---------------------------------------------------------------------------
# Shared block renderers (used by both region assembly and <!-- include -->)
# ---------------------------------------------------------------------------


def render_mirrors_block(site_cfg: dict[str, Any], lang: str) -> str:
    lk = _lang_key(lang)
    ui = _UI[lk]
    lb = site_cfg["load_balancer"]
    urls = site_cfg["urls"]
    lb_name = lb[f"name_{lk}"]
    app_note = lb[f"app_note_{lk}"]

    lines = [
        f"* {lb_name}",
        f"  * {lb['host']}",
        f"  * {urls['app']} {app_note}",
        f"* {ui['mirrors_heading']}",
    ]
    for m in site_cfg["mirrors"]:
        lines.append(f"  * {m['name']}: {m['host']}")
    return "\n".join(lines)


def render_license_block(site_cfg: dict[str, Any], years: str | None = None) -> str:
    lic = site_cfg["license"]
    y = years or lic["years_overseas"]
    raw_lines = [f"Copyright (c) {y} {lic['holder']}"] + lic["body"].strip().splitlines()
    return "\n".join(f"    {line}" if line else "" for line in raw_lines)


def render_common_credits(site_cfg: dict[str, Any], include_contour: bool = True) -> str:
    credits = site_cfg["credits"]
    parts = [
        credits["gmap_styles"].strip(),
        credits["mapsforge_style"].strip(),
    ]
    if include_contour:
        parts.append(credits["contour_tools"].strip())
    parts.append(credits["map_tools"].strip())
    return "\n\n".join(parts)


def render_taiwan_credits(site_cfg: dict[str, Any], lang: str) -> str:
    lk = _lang_key(lang)
    credits = site_cfg["credits"]
    parts = [
        credits[f"osm_{lk}"].strip(),
        credits[f"taiwan_extra_{lk}"].strip(),
        render_common_credits(site_cfg, include_contour=True),
    ]
    return "\n\n".join(parts)


def render_overseas_regions_index(docs_dir: Path, site_cfg: dict[str, Any], lang: str) -> str:
    """Build the grouped overseas regions Markdown list from all docs/*/region.toml."""
    lk = _lang_key(lang)
    ui = _UI[lk]
    base_url = site_cfg["urls"]["base"]
    suffix = "_topo-en.html" if lk == "en" else "_topo.html"

    by_group: dict[str, list[dict[str, Any]]] = {}
    for toml_path in sorted(docs_dir.glob("*/region.toml")):
        cfg = load_region_config(toml_path, docs_dir=docs_dir)
        gid = cfg.get("group", "other")
        by_group.setdefault(gid, []).append(cfg)

    sections: list[str] = []
    for grp in site_cfg["region_groups"]:
        gid = grp["id"]
        entries = by_group.pop(gid, [])
        if not entries:
            continue
        entries.sort(key=lambda c: (c.get("order", 999), c["suite"]))
        lines = [f"### {grp[lk]}", ""]
        for cfg in entries:
            lang_cfg = cfg.get(lk, {})
            label = lang_cfg.get("index_label") or cfg["region"]
            suite = cfg["suite"]
            lines.append(f"* {label}")
            lines.append(f"  * {base_url}/{suite}{suffix}")
            lines.append(f"  * {ui['index_coverage']}")
            lines.append(f"    * {ui['lat_label']}: {cfg['lat']}")
            lines.append(f"    * {ui['lon_label']}: {cfg['lon']}")
        sections.append("\n".join(lines))

    # Any group not listed in site.toml region_groups (defensive fallback)
    for gid, entries in sorted(by_group.items()):
        entries.sort(key=lambda c: (c.get("order", 999), c["suite"]))
        lines = [f"### {gid}", ""]
        for cfg in entries:
            lang_cfg = cfg.get(lk, {})
            label = lang_cfg.get("index_label") or cfg["region"]
            suite = cfg["suite"]
            lines.append(f"* {label}")
            lines.append(f"  * {base_url}/{suite}{suffix}")
            lines.append(f"  * {ui['index_coverage']}")
            lines.append(f"    * {ui['lat_label']}: {cfg['lat']}")
            lines.append(f"    * {ui['lon_label']}: {cfg['lon']}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def expand_includes(md_text: str, docs_dir: Path, lang: str) -> str:
    """Expand ``<!-- include: ... -->`` directives in a Markdown document."""
    site_path = docs_dir / "shared" / "site.toml"
    if "<!--" not in md_text or not site_path.exists():
        return md_text

    site_cfg = load_site_config(docs_dir)

    def _replace(match: re.Match[str]) -> str:
        directive = match.group(1)
        if directive == "overseas_regions":
            return render_overseas_regions_index(docs_dir, site_cfg, lang)
        if directive == "mirrors":
            return render_mirrors_block(site_cfg, lang)
        if directive == "common_credits":
            return render_common_credits(site_cfg, include_contour=True)
        if directive == "taiwan_credits":
            return render_taiwan_credits(site_cfg, lang)
        if directive == "license":
            return render_license_block(site_cfg)
        if directive.startswith("license:"):
            years = directive.split(":", 1)[1]
            return render_license_block(site_cfg, years=years)
        raise ValueError(f"Unknown include directive: {directive!r}")

    return _INCLUDE_RE.sub(_replace, md_text)


# ---------------------------------------------------------------------------
# Overseas region Markdown assembler
# ---------------------------------------------------------------------------


def build_region_markdown(
    region_cfg: dict[str, Any],
    site_cfg: dict[str, Any],
    guide_md: str,
    lang: str,
) -> str:
    """Assemble the complete Markdown document for an overseas region."""
    lk = _lang_key(lang)
    ui = _UI[lk]
    urls = site_cfg["urls"]
    vids = site_cfg["videos"]
    styles = site_cfg["styles"]
    style_sz = f" ({styles['size']})" if styles.get("size") else ""

    region: str = region_cfg["region"]
    suite: str = region_cfg["suite"]
    elev: bool = bool(region_cfg.get("elevation", True))
    has_carto: bool = bool(region_cfg.get("has_carto", elev))
    has_pmtiles: bool = bool(region_cfg.get("has_pmtiles", True))
    has_dem_pmtiles: bool = bool(region_cfg.get("has_dem_pmtiles", elev))
    guide_kind: str = region_cfg.get("guide_kind", "region" if elev else "city")
    ai_notice: bool = bool(region_cfg.get("ai_notice", False))
    lat: str = region_cfg["lat"]
    lon: str = region_cfg["lon"]
    hgt_files: str = region_cfg.get("hgt_files", "")
    sizes: dict[str, str] = region_cfg.get("sizes", {})

    lang_cfg: dict[str, Any] = region_cfg.get(lk, {})
    title: str = lang_cfg["title"]
    garmin_name: str = lang_cfg.get("garmin_name") or region_cfg.get("garmin_name") or f"{region} Region"

    # Derived filenames & tokens (100% deterministic from region, suite, elevation)
    host = "rudymap.tw"
    base = urls["base"]
    mf_pfx = f"AW3D30_OSM_{region}_TOPO_Rudy" if elev else f"OSM_{region}_TOPO_Rudy"
    g_dem = "_aw3d30" if elev else ""
    g_inst_dem = "AW3D30_" if elev else ""
    g_style = "camp3D" if elev else "camp"
    ver_prefix = "AW3D30.OSM" if elev else "OSM"
    am = ui["auto_mirror"]

    underline = "=" * max(len(title), 20)
    parts: list[str] = [
        f"{title}\n{underline}",
        f"{ver_prefix} - {region} TOPO v__version__",
        ui["subtitle"],
        (
            f"[{ui['taiwan_home_label']}]({ui['taiwan_home_href']}) · "
            f"[{ui['legend_label']}](./legend.html) · "
            f"[{ui['tiles_label']}]({urls['tiles']}) · "
            f"[{ui['app_label']}]({urls['app']}) · "
            f"[{ui['fb_label']}]({urls['fb_group']}) · "
            f"[GitHub]({urls['github']})"
        ),
    ]

    # --- Mobile App Auto Install ---
    quick_body = ui["quick_guide_elev"] if elev else ui["quick_guide_no_elev"]
    parts.append(
        f"## {ui['sec_mobile']}\n\n"
        f"* {ui['quick_guide_title']}\n"
        f"  > {ui['quick_guide_phone']}{urls['app']} <br />\n"
        f"  > {quick_body}"
    )

    # HikingJournal
    hj_lines = [
        f"### {ui['hj_title']}",
        "",
        f"* {ui['hj_note']}",
        f"  > {ui['video_prefix']}{vids['hj']}",
        f"* {ui['hj_map']} {base}/{mf_pfx}.map.zip",
        f"* {ui['hj_style']} {base}/{styles['hs']}",
    ]
    if elev:
        hj_lines.append(f"* {ui['hj_dem']} {base}/{suite}_hgtmix.zip")
    parts.append("\n".join(hj_lines))

    # Wadi
    wadi_lines = [
        f"### {ui['wadi_title']}",
        "",
        f"* {ui['wadi_note']}",
        f"  > {ui['video_prefix']}{vids['wadi']}",
        f"* {ui['classic']}",
    ]
    if elev:
        wadi_lines += [
            f"  * {ui['all_in_one']}{_sz(sizes, 'all')}",
            f"    > [[{am}]](wadi-all://{host}/{mf_pfx}.zip)",
        ]
    wadi_lines += [
        f"  * {ui['offline_map']}{_sz(sizes, 'map')}",
        f"    > [[{am}]](wadi-map://{host}/{mf_pfx}.map.zip)",
        f"  * {ui['style_theme']}{style_sz}",
        f"    > [[{am}]](wadi-theme://{host}/{styles['hs']})",
    ]
    if elev:
        wadi_lines += [
            f"  * {ui['dem_file']}{_sz(sizes, 'dem')}",
            f"    > [[{am}]](wadi-hgt://{host}/{suite}_hgtmix.zip)",
        ]
    parts.append("\n".join(wadi_lines))

    # GTS
    gts_lines = [
        f"### {ui['gts_title']}",
        "",
        f"* {ui['tap_install']}",
        f"  > {ui['video_prefix']}{vids['gts']}",
        f"* {ui['classic']}",
    ]
    if elev:
        gts_lines += [
            f"  * {ui['all_in_one']}{_sz(sizes, 'all')}",
            f"    > [[{am}]](gts-all://{host}/{mf_pfx}.zip)",
        ]
    gts_lines += [
        f"  * {ui['offline_map']}{_sz(sizes, 'map')}",
        f"    > [[{am}]](gts-map://{host}/{mf_pfx}.map.zip)",
        f"  * {ui['style_theme']}{style_sz}",
        f"    > [[{am}]](gts-mapthemes://{host}/{styles['hs']})",
    ]
    if elev:
        gts_lines += [
            f"  * {ui['dem_file']}{_sz(sizes, 'dem')}",
            f"    > [[{am}]](gts-hgt://{host}/{suite}_hgtmix.zip)",
        ]
    parts.append("\n".join(gts_lines))

    # OruxMaps
    orux_lines = [
        f"### {ui['orux_title']}",
        "",
        f"* {ui['tap_install']}",
        f"  > {ui['orux_v11']}{vids['orux_11']} <br />",
        f"  > {ui['orux_v10']}{vids['orux_10']}",
        f"* ![Map](images/OruxMaps_map.jpeg =36x) Map{_sz(sizes, 'map')}",
        f"  > [[{am}]](orux-map://{host}/{mf_pfx}.map.zip)",
        f"* ![Style](images/OruxMaps_style.jpeg =36x) Style{style_sz}",
        f"  > [[{am}]](orux-mf-theme://{host}/{styles['hs']})",
    ]
    if elev:
        orux_lines += [
            f"* ![DEM](images/OruxMaps_dem.jpeg =36x) {ui['orux_dem_label']}{_sz(sizes, 'dem')}",
            f"  > [[{am}]]({base}/{suite}_hgtmix.zip)",
        ]
    parts.append("\n".join(orux_lines))

    # Locus Map
    locus_lines = [
        f"### {ui['locus_title']}",
        "",
        f"* {ui['tap_install']}",
        f"  > {ui['video_prefix']}{vids['locus']}",
    ]
    if elev:
        locus_lines += [
            f"* {ui['all_in_one_rec']}",
            f"  * ![Map](images/Locus.jpeg =36x) {ui['first_install']}{_sz(sizes, 'locus_all', sizes.get('all', ''))}",
            f"    > [[{am}]](locus-actions://https/{host}/{suite}_all-cedric.xml)",
        ]
    locus_lines += [
        f"* {ui['map_update']}",
        f"  * ![Map](images/Locus.jpeg =36x) {ui['update']}{_sz(sizes, 'locus_upgrade')}",
        f"    > [[{am}]](locus-actions://https/{host}/{suite}_upgrade-cedric.xml)",
        f"* {ui['install_sep']}",
        f"  * ![Map](images/Locus_map.jpeg =36x) Map{_sz(sizes, 'map')}",
        f"    > [[{am}]](locus-actions://https/{host}/{suite}_map-cedric.xml)",
        f"  * ![Style](images/Locus_style.jpeg =36x) Style{style_sz}",
        f"    > [[{am}]](locus-actions://https/{host}/{styles['locus_xml']})",
    ]
    if elev:
        locus_lines += [
            f"  * ![DEM](images/Locus_dem.jpeg =36x) DEM, aw3d30-4.1{_sz(sizes, 'dem')}",
            f"    > [[{am}]](locus-actions://https/{host}/{suite}_dem-cedric.xml)",
        ]
    parts.append("\n".join(locus_lines))

    # Cartograph Maps (when carto_all is built)
    if has_carto:
        carto_lines = [
            f"### {ui['carto_title']}",
            "",
            f"* {ui['tap_install']}",
            f"  > {ui['video_prefix']}{vids['cartograph']}",
            f"* {ui['all_in_one_rec']}",
            f"  * ![Map](images/Cartograph.png =36x) {ui['first_install']}{_sz(sizes, 'carto_all')}",
            f"    > [[{am}]](cartograph-map://{host}/{region}_carto_all.cpkg)",
            f"* {ui['map_update']}",
            f"  * ![Map](images/Cartograph.png =36x) {ui['update']}{_sz(sizes, 'carto_upgrade')}",
            f"    > [[{am}]](cartograph-map://{host}/{region}_carto_upgrade.cpkg)",
            f"* {ui['install_sep']}",
            f"  * ![Map](images/Cartograph_map.png =36x) Map{_sz(sizes, 'map')}",
            f"    > [[{am}]](cartograph-map://{host}/{region}_carto_map.cpkg)",
            f"  * ![Style](images/Cartograph_style.png =36x) Style{style_sz}",
            f"    > [[{am}]](cartograph-map://{host}/{region}_carto_style.cpkg)",
            f"  * ![DEM](images/Cartograph_dem.png =36x) {ui['carto_dem_label']}{_sz(sizes, 'carto_dem')}",
            f"    > [[{am}]](cartograph-map://{host}/{region}_carto_dem.cpkg)",
        ]
        parts.append("\n".join(carto_lines))

    # --- Garmin Offline Maps ---
    parts.append(
        f"## {ui['sec_garmin']}\n\n"
        f"* {ui['garmin_guide_title']}\n"
        f"  > * {ui['garmin_formats']}\n"
        f"  > * {ui['garmin_win']}{vids['garmin_win']}\n"
        f"  > * {ui['garmin_mac']}{vids['garmin_mac']}\n\n"
        f"### Garmin MOI.OSM.{g_style} - {garmin_name}{ui['basecamp_note']}\n\n"
        f"* ![Map](images/Garmin_large.jpeg =36x) {g_style}{_sz(sizes, 'garmin_img')}\n"
        f"  > [[{am}]]({base}/gmapsupp_{region}{g_dem}_zh_{g_style}.img.zip)\n"
        f"* ![Map](images/Windows.png =36x) {g_style}{_sz(sizes, 'garmin_win')}\n"
        f"  > [[{am}]]({base}/Install_{g_inst_dem}{region}_TOPO_{g_style}.exe)\n"
        f"* ![Map](images/macOS.png =36x) {g_style}{_sz(sizes, 'garmin_mac')}\n"
        f"  > [[{am}]]({base}/{region}{g_dem}_zh_{g_style}.gmap.zip)\n\n"
        f"### Garmin English Maps - {garmin_name}\n\n"
        f"* ![Map](images/Garmin_large.jpeg =36x) {g_style}{_sz(sizes, 'garmin_img')}\n"
        f"  > [[{am}]]({base}/gmapsupp_{region}{g_dem}_en_{g_style}.img.zip)\n"
        f"* ![Map](images/Windows.png =36x) en_{g_style}{_sz(sizes, 'garmin_win')}\n"
        f"  > [[{am}]]({base}/Install_{g_inst_dem}{region}_TOPO_{g_style}_en.exe)\n"
        f"* ![Map](images/macOS.png =36x) en_{g_style}{_sz(sizes, 'garmin_mac')}\n"
        f"  > [[{am}]]({base}/{region}{g_dem}_en_{g_style}.gmap.zip)"
    )

    # --- Mapsforge Manual Download ---
    map_sub = ui["sub_map_dem"] if elev else ui["sub_map_only"]
    manual_lines = [
        f"## {ui['sec_manual']}",
        "",
        f"* {ui['manual_guide_title']}",
        f"  > * {ui['manual_orux']}{vids['manual_orux']}",
        f"  > * {ui['manual_locus']}{vids['manual_locus']}",
        "",
        f"### {map_sub}",
        "",
        f"* ![Map](images/Android.png =36x) ![iOS](images/macOS.png =36x) Map{_sz(sizes, 'manual_map', sizes.get('map', ''))}",
        f"  > [[{am}]]({base}/{mf_pfx}.map.zip)",
    ]
    if elev:
        manual_lines += [
            "* ![DEM](images/Android.png =36x)![iOS](images/macOS.png =36x) 30m HGT",
            f"  > [[{am}]]({base}/{suite}_hgtmix.zip)",
        ]
    manual_lines += [
        "",
        f"### {ui['sub_poi']}",
        "",
        f"* ![POIv3](images/Android.png =36x) {ui['apps_combo']} POIv3{_sz(sizes, 'poiv3')}",
        f"  > [[{am}]]({base}/{mf_pfx}.poi.zip)",
        f"* ![POIv2](images/Android.png =36x) Cartograph POIv2{_sz(sizes, 'poiv2')}",
        f"  > [[{am}]]({base}/{mf_pfx}_v2.poi.zip)",
        f"* ![LOCUS_POI](images/Android.png =36x) Locus POI{_sz(sizes, 'locus_poi')}",
        f"  > [[{am}]]({base}/{mf_pfx}.db.zip)",
        "",
        f"### {ui['sub_style']}",
        "",
        f"* ![Style](images/Android.png =36x) {ui['apps_combo']} Style{style_sz}",
        f"  > [[{am}]]({base}/{styles['hs']})",
        f"* ![Style](images/Android.png =36x) Locus Style{style_sz}",
        f"  > [[{am}]]({base}/{styles['locus']})",
        f"* ![Android](images/Android.png =36x)![iOS](images/macOS.png =36x) Cartograph Maps Style{style_sz}",
        f"  > [[{am}]]({base}/{styles['hs']})",
        "",
        f"### {ui['sub_overlay']}",
        "",
        f"* {ui['overlay_bn']}{style_sz}",
        f"  > [[{am}]]({base}/{styles['bn']})",
        f"* {ui['overlay_dn']}{style_sz}",
        f"  > [[{am}]]({base}/{styles['dn']})",
        f"* {ui['overlay_tn']}{style_sz}",
        f"  > [[{am}]]({base}/{styles['tn']})",
        f"* {ui['overlay_extra']}{style_sz}",
        f"  > [[{am}]]({base}/{styles['extra']})",
    ]
    parts.append("\n".join(manual_lines))

    # --- PMTiles Vector Tiles ---
    if has_pmtiles:
        pmtiles_intro = ui["pmtiles_intro_elev"] if has_dem_pmtiles else ui["pmtiles_intro_no_elev"]
        pmtiles_lines = [
            f"## {ui['sec_pmtiles']}",
            "",
            f"* {ui['pmtiles_intro_title']}",
            f"  > {pmtiles_intro}",
            f"* {ui['pmtiles_vec']} ({mf_pfx}.pmtiles)",
            f"  > [[{am}]]({base}/{mf_pfx}.pmtiles)",
            f"* {ui['pmtiles_style']}",
            f"  > [[{am}]]({base}/{styles['pmtiles']})",
        ]
        if has_dem_pmtiles:
            dem_pmtiles = f"{region.lower()}_dem.pmtiles"
            pmtiles_lines += [
                f"* {ui['pmtiles_dem']} ({dem_pmtiles})",
                f"  > [[{am}]]({base}/{dem_pmtiles})",
            ]
        parts.append("\n".join(pmtiles_lines))

    # --- Map Coverage & Region/City Guide ---
    guide_heading = ui["sec_guide_city"] if guide_kind == "city" else ui["sec_guide_region"]
    guide_parts = [
        f"## {guide_heading}",
        f"* {ui['lat_label']}: {lat}\n* {ui['lon_label']}: {lon}",
    ]
    if ai_notice:
        guide_parts.append(ui["ai_notice"])
    guide_clean = guide_md.strip()
    if guide_clean:
        guide_parts.append(guide_clean)
    parts.append("\n\n".join(guide_parts))

    # --- Related Resources & Mirrors ---
    parts.append(
        f"## {ui['sec_resources']}\n\n"
        f"* {ui['res_home']}\n"
        f"* {ui['res_legend']}\n"
        f"* {ui['res_tiles']}{urls['tiles']}\n"
        f"* {ui['res_fb']}{urls['fb_group']}\n"
        f"* {ui['res_github']}{urls['github']}\n"
        f"{render_mirrors_block(site_cfg, lang)}"
    )

    # --- Copyright Notice ---
    credits = site_cfg["credits"]
    cp_parts = [credits[f"osm_{lk}"].strip()]
    if elev:
        aw_lines = [
            "* JAXA ALOS World 3D - 30m (AW3D30) Version 4.1",
            f"> {ui['aw3d30_desc']} <br />",
        ]
        if hgt_files:
            aw_lines.append(f"> {ui['aw3d30_files'].format(files=hgt_files)} <br />")
        aw_lines.append("> Link: http://www.eorc.jaxa.jp/ALOS/en/aw3d30/index.htm")
        cp_parts.append("\n".join(aw_lines))
    cp_parts.append(render_common_credits(site_cfg, include_contour=elev))
    parts.append(f"## {ui['sec_copyright']}\n\n" + "\n\n".join(cp_parts))

    # --- Map License ---
    lic_years = region_cfg.get("license_years") or site_cfg["license"]["years_overseas"]
    parts.append(f"## {ui['sec_license']}\n\n{render_license_block(site_cfg, years=lic_years)}")

    return "\n\n".join(parts) + "\n"
