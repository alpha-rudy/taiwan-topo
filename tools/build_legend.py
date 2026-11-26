#!/usr/bin/env python3
"""Auto-generate interactive web legend and detail/compact PDF legends from MOI_OSM.xml.

All visual swatches (lines, areas/patterns, point icons, circles, labels),
searchable color buckets, line/fill shapes, zoom ranges, and overlay layer
requirements are extracted directly from styles/mapsforge_style/MOI_OSM.xml
and styles/mapsforge_style/moiosm_res/ so the legend stays in sync with the map.
"""

from __future__ import annotations

import argparse
import base64
import colorsys
import concurrent.futures
import gzip
import html
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Import sibling helper tools/pmtiles_theme.py
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
import pmtiles_theme as pt
import template_assets

# ---------------------------------------------------------------------------
# Color & shape taxonomies (used for web search filters)
# ---------------------------------------------------------------------------

COLOR_META: list[tuple[str, str, str]] = [
    ("red", "紅", "#d63031"),
    ("orange", "橘／棕", "#d37a2b"),
    ("yellow", "黃", "#eab308"),
    ("green", "綠", "#2d8a4e"),
    ("blue", "藍", "#2574c7"),
    ("purple", "紫", "#8b46b8"),
    ("gray", "黑／灰", "#4b5563"),
]

SHAPE_META: list[tuple[str, str]] = [
    ("solid", "實線"),
    ("dashed", "虛線"),
    ("dotted", "點線／階梯"),
    ("cased", "雙線外框"),
    ("symbol_line", "鋸齒／帶符號線"),
    ("pattern", "紋理填滿"),
    ("solid_fill", "純色色塊"),
    ("triangle", "三角形"),
    ("circle", "圓形"),
    ("square", "方形／菱形"),
    ("house", "房屋／涼亭"),
    ("cross", "十字／叉號"),
    ("water", "水滴／波紋"),
    ("tree", "樹木／植物"),
    ("tower", "鐵塔／天線"),
    ("transport", "交通工具"),
    ("person", "人物"),
    ("flag", "指標／旗幟"),
    ("letter", "文字／符號"),
]

GEOM_LABELS: dict[str, str] = {
    "point": "點／圖示",
    "line": "線條",
    "area": "面／區域",
}


@dataclass
class OverlayInfo:
    cat: str
    name_zh: str
    enabled_default: bool


@dataclass
class LegendEntry:
    id: str
    category: str
    name: str
    desc: str
    compact: bool
    dense: bool
    geom: str
    e: str
    closed: str
    tags: dict[str, str]
    zoom: int
    extra_cats: list[str]
    sample_label: str
    catalog_shapes: list[str]
    aliases: list[str]
    example: dict[str, Any] | None
    # Derived automatically from MOI_OSM.xml:
    svg_detail: str = ""
    svg_compact: str = ""
    colors: list[str] = field(default_factory=list)
    shapes: list[str] = field(default_factory=list)
    zoom_min: int = 0
    overlays: list[OverlayInfo] = field(default_factory=list)
    matched_srcs: set[str] = field(default_factory=set)
    matched_count: int = 0
    taiwan_count: int | None = None


# ---------------------------------------------------------------------------
# Theme parsing & exact Mapsforge rule evaluation
# ---------------------------------------------------------------------------


def parse_stylemenu_overlays(root: ET.Element, style_id: str = "elmt-hiking") -> dict[str, OverlayInfo]:
    """Build cat -> OverlayInfo (zh name + default enabled) for the given stylemenu style."""
    menu = root.find("stylemenu")
    if menu is None:
        return {}
    layers = {lay.get("id", ""): lay for lay in menu.findall("layer")}
    style = layers.get(style_id)
    if style is None:
        return {}

    result: dict[str, OverlayInfo] = {}
    for ov in style.findall("overlay"):
        lid = ov.get("id", "")
        lay = layers.get(lid)
        if lay is None:
            continue
        enabled = lay.get("enabled") == "true"
        zh_names = [n.get("value", "") for n in lay.findall("name") if n.get("lang") == "zh"]
        en_names = [n.get("value", "") for n in lay.findall("name") if n.get("lang") == "en"]
        label = (zh_names or en_names or [lid])[0]
        for cat_el in lay.findall("cat"):
            cid = cat_el.get("id", "")
            if cid and cid not in result:
                result[cid] = OverlayInfo(cat=cid, name_zh=label, enabled_default=enabled)
    return result


def _test_matches(k_expr: str, v_expr: str, tags: dict[str, str]) -> bool:
    keys = k_expr.split("|")
    vals = v_expr.split("|")
    for v in vals:
        if v == "~":
            if all(k not in tags for k in keys):
                return True
        elif v == "*":
            if any(k in tags for k in keys):
                return True
        else:
            if any(tags.get(k) == v for k in keys):
                return True
    return False


def match_rows(
    rows: list[dict[str, Any]],
    active_cats: set[str],
    e: str,
    closed: str,
    tags: dict[str, str],
    zoom: int,
    extra_cats: list[str],
    all_overlay_cats: set[str] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Return (matched instructions at `zoom`, minimum zoom where feature draws).

    Tries default-enabled `active_cats | extra_cats` first. If no visual drawing
    instruction matches and `all_overlay_cats` is provided, automatically retries
    with all `<stylemenu>` toggleable overlays so off-by-default layers are detected
    straight from MOI_OSM.xml without needing manual `extra_cats` maintenance.
    """

    def _eval(allowed: set[str]) -> tuple[list[dict[str, Any]], int]:
        matched_at_zoom: list[dict[str, Any]] = []
        min_z = 99
        for r in rows:
            if r["e"] != "any" and r["e"] != e:
                continue
            if r["closed"] != "any" and r["closed"] != closed:
                continue
            if any(c not in allowed for c in r["cats"]):
                continue
            if not all(_test_matches(k, v, tags) for k, v in r["tests"]):
                continue
            if r["instr"] not in ("caption", "pathText"):
                min_z = min(min_z, int(r["zmin"]))
            if r["zmin"] <= zoom <= r["zmax"]:
                matched_at_zoom.append(r)
        return matched_at_zoom, (zoom if min_z == 99 else min_z)

    base_allowed = active_cats | set(extra_cats)
    matched_at_zoom, min_zoom = _eval(base_allowed)
    has_visual = any(r["instr"] not in ("caption", "pathText") for r in matched_at_zoom)
    if not has_visual and all_overlay_cats:
        matched_at_zoom, min_zoom = _eval(base_allowed | all_overlay_cats)
    return matched_at_zoom, min_zoom


# ---------------------------------------------------------------------------
# Color parsing & human color classification
# ---------------------------------------------------------------------------


def parse_mf_color(raw: str) -> tuple[str, float]:
    """Convert Mapsforge #RRGGBB or #AARRGGBB into ('#RRGGBB', alpha)."""
    c = raw.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) == 6:
        return f"#{c.upper()}", 1.0
    if len(c) == 8:
        alpha = int(c[0:2], 16) / 255.0
        return f"#{c[2:].upper()}", round(alpha, 3)
    return "#333333", 1.0


def classify_hex_color(hex_rgb: str) -> str | None:
    """Classify '#RRGGBB' into one of the human color filter buckets (or None for near-white)."""
    c = hex_rgb.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        return None
    r, g, b = (int(c[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hue = h * 360.0

    # Ignore near-white background/halo colors (keep pastel ice-cyan like #E0FFFF)
    if v > 0.93 and s < 0.08:
        return None
    # Dark/mid low-saturation tones (e.g. #799079 power line, rgb(51,60,51) power tower) read as gray,
    # while bright pastels (v >= 0.75, s >= 0.09 like #D2EAD8 / #BCCFB5 / #E0FFFF) read as chromatic.
    if v < 0.18 or (v < 0.75 and s < 0.18) or s < 0.09:
        return "gray"
    if hue < 15 or hue >= 338:
        return "red"
    if hue < 44:
        return "orange"
    if hue < 68:
        return "yellow"
    if hue < 168:
        return "green"
    if hue < 255:
        return "blue"
    if hue < 338:
        return "purple"
    return "red"


_CSS_NAMED_COLORS: dict[str, str] = {
    "black": "#000000",
    "white": "#FFFFFF",
    "red": "#FF0000",
    "green": "#008000",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "orange": "#FFA500",
    "purple": "#800080",
    "gray": "#808080",
    "grey": "#808080",
    "brown": "#A52A2A",
    "maroon": "#800000",
    "navy": "#000080",
    "teal": "#008080",
    "olive": "#808000",
    "lime": "#00FF00",
    "cyan": "#00FFFF",
    "aqua": "#00FFFF",
    "magenta": "#FF00FF",
    "fuchsia": "#FF00FF",
    "silver": "#C0C0C0",
    "pink": "#FFC0CB",
    "gold": "#FFD700",
    "darkred": "#8B0000",
    "darkgreen": "#006400",
    "darkblue": "#00008B",
    "darkgray": "#A9A9A9",
    "darkgrey": "#A9A9A9",
    "lightgray": "#D3D3D3",
    "lightgrey": "#D3D3D3",
    "dimgray": "#696969",
    "dimgrey": "#696969",
}
_RGBA_COLOR_RE = re.compile(
    r"^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)$",
    re.IGNORECASE,
)
_SVG_SHAPE_TAGS = frozenset({"path", "rect", "circle", "ellipse", "polygon", "polyline", "line", "text"})
_SVG_SKIP_TAGS = frozenset({"metadata", "title", "desc", "clippath", "mask", "style", "script"})
_BUCKET_REP_HEX: dict[str, str] = {
    "red": "#E03C32",
    "orange": "#D37A2B",
    "yellow": "#FAE24C",
    "green": "#2D8A4E",
    "blue": "#2574C7",
    "purple": "#8B46B8",
    "gray": "#333333",
}


def _parse_css_color(val: str | None) -> str | None:
    if not val:
        return None
    v = val.strip().lower()
    if v in ("none", "transparent", "inherit", "currentcolor") or v.startswith("url("):
        return None
    if v in _CSS_NAMED_COLORS:
        return _CSS_NAMED_COLORS[v]
    if v.startswith("#"):
        rgb, alpha = parse_mf_color(v)
        return rgb if alpha >= 0.25 else None
    m = _RGBA_COLOR_RE.match(v)
    if m:
        alpha = float(m.group(4)) if m.group(4) is not None else 1.0
        if alpha < 0.25:
            return None
        r, g, b = (min(255, round(float(m.group(i)))) for i in (1, 2, 3))
        return f"#{r:02X}{g:02X}{b:02X}"
    return None


def _parse_svg_style_dict(style_str: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in style_str.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def _parse_float_px(raw: str | None, default: float = 0.0) -> float:
    if not raw:
        return default
    m = re.match(r"\s*([0-9.]+)", raw)
    return float(m.group(1)) if m else default


def _sample_png_colors(png_bytes: bytes) -> list[str]:
    """Sample dominant non-white, opaque color buckets from raw PNG bytes (pure stdlib)."""
    if png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        return []
    pos = 8
    w = h = bd = ct = 0
    plte = b""
    trns = b""
    idat = bytearray()
    while pos + 8 <= len(png_bytes):
        ln, ctype = struct.unpack(">I4s", png_bytes[pos : pos + 8])
        data = png_bytes[pos + 8 : pos + 8 + ln]
        pos += 12 + ln
        if ctype == b"IHDR" and len(data) >= 10:
            w, h, bd, ct = struct.unpack(">IIBB", data[:10])
        elif ctype == b"PLTE":
            plte = data
        elif ctype == b"tRNS":
            trns = data
        elif ctype == b"IDAT":
            idat.extend(data)
        elif ctype == b"IEND":
            break
    if bd != 8 or ct not in (2, 3, 6) or w <= 0 or h <= 0:
        return []
    bpp = {2: 3, 3: 1, 6: 4}[ct]
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error:
        return []
    stride = w * bpp
    if len(raw) < h * (stride + 1):
        return []
    prev = bytearray(stride)
    counts: dict[str, int] = {}
    step_y = max(1, h // 48)
    step_x = max(1, w // 48)
    off = 0
    for y in range(h):
        ftype = raw[off]
        off += 1
        row = bytearray(raw[off : off + stride])
        off += stride
        if ftype == 1:
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i - bpp]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pr) & 0xFF
        prev = row
        if y % step_y != 0:
            continue
        for x in range(0, w, step_x):
            idx = x * bpp
            if ct == 6:
                r, g, b, a = row[idx], row[idx + 1], row[idx + 2], row[idx + 3]
                if a < 128:
                    continue
            elif ct == 2:
                r, g, b = row[idx], row[idx + 1], row[idx + 2]
            else:
                pi = row[idx]
                if pi < len(trns) and trns[pi] < 128:
                    continue
                if pi * 3 + 2 >= len(plte):
                    continue
                r, g, b = plte[pi * 3], plte[pi * 3 + 1], plte[pi * 3 + 2]
            bkt = classify_hex_color(f"#{r:02X}{g:02X}{b:02X}")
            if bkt:
                counts[bkt] = counts.get(bkt, 0) + 1
    tot = sum(counts.values())
    if not tot:
        return []
    out: list[str] = []
    for k, cnt in sorted(counts.items(), key=lambda kv: -kv[1]):
        if cnt / tot >= 0.08:
            out.extend([_BUCKET_REP_HEX[k]] * max(1, round(cnt * 5 / tot)))
    return out


def extract_colors_from_svg_file(svg_path: Path) -> list[str]:
    """Extract visible '#RRGGBB' colors from fill/stroke of an SVG (or PNG) resource."""
    if not svg_path.is_file():
        return []
    suffix = svg_path.suffix.lower()
    if suffix == ".png":
        return _sample_png_colors(svg_path.read_bytes())
    if suffix != ".svg":
        return []
    try:
        root = ET.fromstring(svg_path.read_text(encoding="utf-8", errors="ignore"))
    except ET.ParseError:
        return []

    vb = root.get("viewBox", "")
    vb_parts = [float(x) for x in re.findall(r"[0-9.]+", vb)]
    canvas_w = vb_parts[2] if len(vb_parts) >= 4 else _parse_float_px(root.get("width"), 580.0)
    hairline_limit = max(2.0, canvas_w * 0.03)

    found: list[str] = []

    def walk(
        el: ET.Element,
        inh_fill: str | None,
        inh_stroke: str | None,
        inh_op: float,
        inh_fop: float,
        inh_sop: float,
        in_defs: bool,
    ) -> None:
        tag = el.tag.rsplit("}", 1)[-1].lower()
        if tag in _SVG_SKIP_TAGS:
            return
        st = _parse_svg_style_dict(el.get("style", ""))
        if st.get("display") == "none" or el.get("display") == "none":
            return
        if st.get("visibility") == "hidden" or el.get("visibility") == "hidden":
            return

        op = inh_op * _parse_float_px(st.get("opacity", el.get("opacity")), 1.0)
        fop = _parse_float_px(st.get("fill-opacity", el.get("fill-opacity")), inh_fop)
        sop = _parse_float_px(st.get("stroke-opacity", el.get("stroke-opacity")), inh_sop)
        raw_fill = st.get("fill", el.get("fill"))
        raw_stroke = st.get("stroke", el.get("stroke"))
        cur_fill = inh_fill if raw_fill is None else raw_fill
        cur_stroke = inh_stroke if raw_stroke is None else raw_stroke

        if tag == "image":
            href = el.get("{http://www.w3.org/1999/xlink}href") or el.get("href") or ""
            if href.startswith("data:image/png;base64,"):
                try:
                    found.extend(_sample_png_colors(base64.b64decode(href.split(",", 1)[1])))
                except ValueError:
                    pass
            return

        if tag == "defs":
            for ch in el:
                walk(ch, cur_fill, cur_stroke, op, fop, sop, True)
            return

        if not in_defs and tag in _SVG_SHAPE_TAGS and op >= 0.25:
            stroke_rgb = _parse_css_color(cur_stroke) if (cur_stroke is not None and sop * op >= 0.25) else None
            stroke_is_halo = stroke_rgb is not None and classify_hex_color(stroke_rgb) is None
            sw = _parse_float_px(st.get("stroke-width", el.get("stroke-width")), 0.0)

            # Skip implicit black fill on Affinity background white-halo stroke paths
            eff_fill: str | None
            if cur_fill is not None:
                eff_fill = cur_fill
            elif tag == "line" or stroke_is_halo:
                eff_fill = "none"
            else:
                eff_fill = "#000000"

            fill_rgb = _parse_css_color(eff_fill) if fop * op >= 0.25 else None
            fill_visible = fill_rgb is not None and classify_hex_color(fill_rgb) is not None
            if fill_rgb:
                found.append(fill_rgb)

            # Ignore hair-thin dark outline strokes around an already-filled colored shape
            if stroke_rgb and (not fill_visible or sw >= hairline_limit or sw == 0.0):
                found.append(stroke_rgb)

        for ch in el:
            walk(ch, cur_fill, cur_stroke, op, fop, sop, in_defs)

    walk(root, None, None, 1.0, 1.0, 1.0, False)
    return found


def detect_colors_and_shapes(
    matched: list[dict[str, Any]],
    geom: str,
    res_dir: Path,
    catalog_shapes: list[str],
) -> tuple[list[str], list[str]]:
    """Infer searchable color buckets and shape/line-style tags from matched instructions."""
    color_counts: dict[str, int] = {}
    shapes: list[str] = []

    def add_color(hex_raw: str, weight: int = 1) -> None:
        rgb, alpha = parse_mf_color(hex_raw)
        if alpha < 0.2:
            return
        bucket = classify_hex_color(rgb)
        if bucket:
            color_counts[bucket] = color_counts.get(bucket, 0) + weight

    line_instrs = [r for r in matched if r["instr"] == "line"]
    area_instrs = [r for r in matched if r["instr"] == "area"]
    sym_instrs = [r for r in matched if r["instr"] in ("symbol", "lineSymbol")]
    circle_instrs = [r for r in matched if r["instr"] == "circle"]

    for r in line_instrs:
        if "stroke" in r["attrs"]:
            add_color(r["attrs"]["stroke"], weight=3)
        if "src" in r["attrs"]:
            p = res_dir / r["attrs"]["src"].split("/")[-1]
            for c in extract_colors_from_svg_file(p):
                add_color(c, weight=2)
    for r in area_instrs:
        if "fill" in r["attrs"]:
            add_color(r["attrs"]["fill"], weight=3)
        if "src" in r["attrs"]:
            p = res_dir / r["attrs"]["src"].split("/")[-1]
            for c in extract_colors_from_svg_file(p):
                add_color(c, weight=2)
    for r in circle_instrs:
        if "fill" in r["attrs"]:
            add_color(r["attrs"]["fill"], weight=3)
        if "stroke" in r["attrs"]:
            add_color(r["attrs"]["stroke"], weight=2)
    for r in sym_instrs:
        src_name = r["attrs"].get("src", "").split("/")[-1]
        if src_name:
            p = res_dir / src_name
            for c in extract_colors_from_svg_file(p):
                add_color(c, weight=2)

    # Sort colors by weight descending, keep top 3; fallback to 'gray' for very pale fills
    sorted_colors = [c for c, _ in sorted(color_counts.items(), key=lambda kv: -kv[1])][:3]
    if not sorted_colors and (line_instrs or area_instrs or sym_instrs or circle_instrs):
        sorted_colors = ["gray"]

    # Geometry & line/area shapes
    if geom == "line":
        has_dash = False
        has_dot = False
        has_solid = False
        has_src_line = False
        opaque_solid_widths: list[float] = []
        opaque_all_widths: list[float] = []
        for r in line_instrs:
            if "src" in r["attrs"]:
                has_src_line = True
                continue
            _, alpha = parse_mf_color(r["attrs"].get("stroke", "#333333"))
            da = r["attrs"].get("stroke-dasharray", "").strip()
            sw = float(r["attrs"].get("stroke-width", "1.0") or 1.0)
            if da:
                nums = [float(x) for x in re.findall(r"[\d.]+", da)]
                # Sparse perpendicular cross-ticks (e.g. aerialway 1.5,200) are not dashed lines
                if len(nums) == 2 and nums[0] > 0 and nums[1] / nums[0] >= 20:
                    continue
                if nums and max(nums) <= 2.5:
                    has_dot = True
                else:
                    has_dash = True
                if alpha >= 0.85:
                    opaque_all_widths.append(sw)
            else:
                has_solid = True
                if alpha >= 0.85:
                    opaque_all_widths.append(sw)
                    opaque_solid_widths.append(sw)
        if any(r["instr"] == "lineSymbol" for r in matched) or has_src_line:
            shapes.append("symbol_line")
        if has_dot:
            shapes.append("dotted")
        if has_dash:
            shapes.append("dashed")
        # True cased line: at least 2 opaque lines with a solid outer casing wider than inner line
        if len(opaque_all_widths) >= 2 and opaque_solid_widths and max(opaque_solid_widths) > min(opaque_all_widths):
            shapes.append("cased")
        if has_solid and not has_dash and not has_dot:
            shapes.append("solid")
    elif geom == "area":
        if any("src" in r["attrs"] for r in area_instrs):
            shapes.append("pattern")
        if any("fill" in r["attrs"] for r in area_instrs):
            shapes.append("solid_fill")
        if line_instrs:
            shapes.append("dashed" if any("stroke-dasharray" in r["attrs"] for r in line_instrs) else "solid")
    else:
        if circle_instrs and "circle" not in catalog_shapes:
            shapes.append("circle")

    for sh in catalog_shapes:
        if sh not in shapes:
            shapes.append(sh)

    return sorted_colors, shapes


# ---------------------------------------------------------------------------
# Focused simplified SVG synthesizer (V1R3-inspired, pure vector)
# ---------------------------------------------------------------------------


_SVG_OPEN_RE = re.compile(r"<svg\b[^>]*>", re.IGNORECASE | re.DOTALL)
_SVG_DIM_W_RE = re.compile(r'\bwidth\s*=\s*["\']\s*([0-9.]+)(?:px)?\s*["\']', re.IGNORECASE)
_SVG_DIM_H_RE = re.compile(r'\bheight\s*=\s*["\']\s*([0-9.]+)(?:px)?\s*["\']', re.IGNORECASE)


def _file_data_uri(path: Path) -> str:
    if not path.is_file():
        return ""
    raw = path.read_bytes()
    if path.suffix.lower() == ".svg":
        # Many moiosm_res SVGs specify width/height (e.g. 580x580) without viewBox,
        # which causes <image width="18" height="18"> to clip instead of scaling.
        text = raw.decode("utf-8", errors="ignore")
        m_open = _SVG_OPEN_RE.search(text)
        if m_open and "viewbox" not in m_open.group(0).lower():
            tag = m_open.group(0)
            mw = _SVG_DIM_W_RE.search(tag)
            mh = _SVG_DIM_H_RE.search(tag)
            if mw and mh:
                vb = f' viewBox="0 0 {mw.group(1)} {mh.group(1)}"'
                new_tag = tag[:-1] + vb + ">"
                text = text[: m_open.start()] + new_tag + text[m_open.end() :]
                raw = text.encode("utf-8")
        mime = "image/svg+xml"
    else:
        mime = "image/png"
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _bezier_point_angle(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float, float]:
    """Return (x, y, angle_deg) on a cubic Bezier curve at parameter t."""
    u = 1.0 - t
    x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
    y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
    dx = 3 * u**2 * (p1[0] - p0[0]) + 6 * u * t * (p2[0] - p1[0]) + 3 * t**2 * (p3[0] - p2[0])
    dy = 3 * u**2 * (p1[1] - p0[1]) + 6 * u * t * (p2[1] - p1[1]) + 3 * t**2 * (p3[1] - p2[1])
    return x, y, math.degrees(math.atan2(dy, dx))


def _scale_line_width(raw_w: str, compact: bool) -> float:
    try:
        w = float(raw_w)
    except ValueError:
        w = 0.8
    # Keep wide bands (e.g. 6.0 vs 3.0) and fine strokes (e.g. 0.9 vs 0.45, 0.3 vs 0.15)
    # strictly proportional so hierarchy differences remain unmistakable.
    if w >= 2.0:
        px = min(20.0, w * 3.0)
    else:
        px = max(1.0, w * 5.2)
    return round(px * (0.72 if compact else 1.0), 2)


def _scale_dasharray(raw_da: str, compact: bool, scale_all: bool = False) -> str:
    nums = [float(x) for x in re.findall(r"[\d.]+", raw_da)]
    if not nums:
        return ""
    if scale_all:
        # Mapsforge `scale="all"` dashes (e.g. borders 3.75,1.25 + 0,1.5625,0.625,2.8125,0,5)
        mult = 4.2
    else:
        # Keep tiny dashes (e.g., steps 1,1 or cliff 1.5,1.5) visibly crisp
        mult = 2.2 if max(nums) <= 2.5 else 1.45
    if compact:
        mult *= 0.72
    # Preserve exact 0 phase offsets (do NOT clamp 0 to 1.2, which creates spurious dashes!)
    return ",".join("0" if v == 0.0 else f"{max(1.2, v * mult):.1f}" for v in nums)


def synthesize_svg(
    entry: LegendEntry,
    matched: list[dict[str, Any]],
    res_dir: Path,
    compact: bool = False,
) -> str:
    """Synthesize a clean, focused inline SVG illustrating this legend entry."""
    prefix = f"c-{entry.id}" if compact else f"d-{entry.id}"

    if entry.geom == "line":
        return _synthesize_line_svg(entry, matched, res_dir, prefix, compact)
    if entry.geom == "area":
        return _synthesize_area_svg(entry, matched, res_dir, prefix, compact)
    return _synthesize_point_svg(entry, matched, res_dir, compact)


def _synthesize_line_svg(
    entry: LegendEntry,
    matched: list[dict[str, Any]],
    res_dir: Path,
    prefix: str,
    compact: bool,
) -> str:
    w, h = (116, 36) if compact else (136, 74)
    if compact:
        p0, p1, p2, p3 = (8.0, 24.0), (38.0, 6.0), (78.0, 30.0), (108.0, 12.0)
    else:
        p0, p1, p2, p3 = (10.0, 52.0), (46.0, 8.0), (90.0, 66.0), (126.0, 22.0)
    path_d = f"M {p0[0]:.1f} {p0[1]:.1f} C {p1[0]:.1f} {p1[1]:.1f}, {p2[0]:.1f} {p2[1]:.1f}, {p3[0]:.1f} {p3[1]:.1f}"

    defs: list[str] = [f'<path id="{prefix}-curve" d="{path_d}"/>']
    body: list[str] = [
        f'<rect width="{w}" height="{h}" rx="{6 if compact else 8}" fill="#f7f6f1"/>'
    ]

    for idx, r in enumerate(matched):
        if r["instr"] == "line":
            attrs = r["attrs"]
            sw = _scale_line_width(attrs.get("stroke-width", "0.8"), compact)
            da_raw = attrs.get("stroke-dasharray", "")
            da = _scale_dasharray(
                da_raw,
                compact,
                scale_all=(attrs.get("scale") == "all"),
            )
            da_offset_attr = ""
            if da:
                da_nums = [float(x) for x in da.split(",")]
                # Long-gap periodic cross-ticks (e.g. aerialway `1.5,200`) would fall
                # outside the short legend curve unless compressed to show 2 crisp ticks.
                if len(da_nums) == 2 and da_nums[0] > 0 and da_nums[1] > (55.0 if compact else 75.0):
                    gap = 52.0 if compact else 64.0
                    da = f"{da_nums[0]:.1f},{gap:.1f}"
                    da_offset_attr = f' stroke-dashoffset="{-(gap / 2.0 + 1.0):.1f}"'
            cap = attrs.get("stroke-linecap", "butt")
            if cap not in ("butt", "round", "square"):
                cap = "butt"
            da_attr = f' stroke-dasharray="{da}"{da_offset_attr}' if da else ""

            if "stroke" in attrs:
                rgb, alpha = parse_mf_color(attrs["stroke"])
                op_attr = f' stroke-opacity="{alpha}"' if alpha < 1.0 else ""
                body.append(
                    f'<use href="#{prefix}-curve" fill="none" stroke="{rgb}"{op_attr} '
                    f'stroke-width="{sw}" stroke-linecap="{cap}" stroke-linejoin="round"{da_attr}/>'
                )
            elif "src" in attrs:
                src_path = res_dir / attrs["src"].split("/")[-1]
                uri = _file_data_uri(src_path)
                if uri:
                    pat_id = f"{prefix}-lpat-{idx}"
                    psize = 12 if compact else 18
                    defs.append(
                        f'<pattern id="{pat_id}" width="{psize}" height="{psize}" patternUnits="userSpaceOnUse">'
                        f'<image href="{uri}" width="{psize}" height="{psize}"/></pattern>'
                    )
                    body.append(
                        f'<use href="#{prefix}-curve" fill="none" stroke="url(#{pat_id})" '
                        f'stroke-width="{max(sw, 6.0 if compact else 10.0)}"/>'
                    )

        elif r["instr"] == "lineSymbol":
            src_name = r["attrs"].get("src", "").split("/")[-1]
            uri = _file_data_uri(res_dir / src_name)
            if uri:
                try:
                    rep_gap = float(r["attrs"].get("repeat-gap", "0"))
                except ValueError:
                    rep_gap = 0.0
                if rep_gap >= 100.0:
                    sym_size = 13 if compact else 18
                    t_positions: tuple[float, ...] = (0.50,)
                else:
                    sym_size = 10 if compact else 14
                    t_positions = (0.16, 0.33, 0.50, 0.67, 0.84)
                for t in t_positions:
                    x, y, ang = _bezier_point_angle(p0, p1, p2, p3, t)
                    body.append(
                        f'<image href="{uri}" x="{-sym_size / 2:.1f}" y="{-sym_size / 2:.1f}" '
                        f'width="{sym_size}" height="{sym_size}" '
                        f'transform="translate({x:.1f},{y:.1f}) rotate({ang:.1f})"/>'
                    )

    # Sample path label (e.g. highway ref or contour elevation) in detail view
    if entry.sample_label and not compact:
        pt_rows = [r for r in matched if r["instr"] == "pathText"]
        fill_rgb = "#222222"
        stroke_rgb = "#FFFFFF"
        if pt_rows:
            fill_rgb, _ = parse_mf_color(pt_rows[-1]["attrs"].get("fill", "#222222"))
            stroke_rgb, _ = parse_mf_color(pt_rows[-1]["attrs"].get("stroke", "#FFFFFF"))
        body.append(
            f'<text font-size="11" font-weight="700" font-family="sans-serif" '
            f'fill="{fill_rgb}" stroke="{stroke_rgb}" stroke-width="3" paint-order="stroke" '
            f'dy="3.5"><textPath href="#{prefix}-curve" startOffset="50%" text-anchor="middle">'
            f"{html.escape(entry.sample_label)}</textPath></text>"
        )

    return (
        f'<svg class="legend-svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(entry.name, quote=True)}">'
        f"<defs>{''.join(defs)}</defs>{''.join(body)}</svg>"
    )


def _synthesize_area_svg(
    entry: LegendEntry,
    matched: list[dict[str, Any]],
    res_dir: Path,
    prefix: str,
    compact: bool,
) -> str:
    w, h = (116, 36) if compact else (136, 74)
    pad_x, pad_y = (6, 4) if compact else (10, 9)
    rw, rh = w - 2 * pad_x, h - 2 * pad_y
    rx = 5 if compact else 8

    defs: list[str] = []
    body: list[str] = [
        f'<rect width="{w}" height="{h}" rx="{6 if compact else 8}" fill="#f7f6f1"/>'
    ]

    for idx, r in enumerate(matched):
        if r["instr"] == "area":
            attrs = r["attrs"]
            if "fill" in attrs:
                rgb, alpha = parse_mf_color(attrs["fill"])
                op = f' fill-opacity="{alpha}"' if alpha < 1.0 else ""
                body.append(
                    f'<rect x="{pad_x}" y="{pad_y}" width="{rw}" height="{rh}" rx="{rx}" fill="{rgb}"{op}/>'
                )
            if "src" in attrs:
                src_name = attrs["src"].split("/")[-1]
                uri = _file_data_uri(res_dir / src_name)
                if uri:
                    pat_id = f"{prefix}-apat-{idx}"
                    psize = 18 if compact else 28
                    defs.append(
                        f'<pattern id="{pat_id}" width="{psize}" height="{psize}" patternUnits="userSpaceOnUse">'
                        f'<image href="{uri}" width="{psize}" height="{psize}"/></pattern>'
                    )
                    body.append(
                        f'<rect x="{pad_x}" y="{pad_y}" width="{rw}" height="{rh}" rx="{rx}" fill="url(#{pat_id})"/>'
                    )
        elif r["instr"] == "line":
            attrs = r["attrs"]
            if "stroke" in attrs:
                rgb, alpha = parse_mf_color(attrs["stroke"])
                sw = min(4.0, _scale_line_width(attrs.get("stroke-width", "0.5"), compact))
                da = _scale_dasharray(attrs.get("stroke-dasharray", ""), compact)
                da_attr = f' stroke-dasharray="{da}"' if da else ""
                op = f' stroke-opacity="{alpha}"' if alpha < 1.0 else ""
                body.append(
                    f'<rect x="{pad_x}" y="{pad_y}" width="{rw}" height="{rh}" rx="{rx}" '
                    f'fill="none" stroke="{rgb}"{op} stroke-width="{sw}"{da_attr}/>'
                )

    # Subtle outer border so pale fills (e.g. residential/grass) stay crisp
    body.append(
        f'<rect x="{pad_x}" y="{pad_y}" width="{rw}" height="{rh}" rx="{rx}" '
        f'fill="none" stroke="#c8d1cb" stroke-width="1"/>'
    )

    return (
        f'<svg class="legend-svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(entry.name, quote=True)}">'
        f"<defs>{''.join(defs)}</defs>{''.join(body)}</svg>"
    )


def _synthesize_point_svg(
    entry: LegendEntry,
    matched: list[dict[str, Any]],
    res_dir: Path,
    compact: bool,
) -> str:
    w, h = (42, 36) if compact else (136, 74)
    has_label = bool(entry.sample_label) and not compact
    cap_rows = [r for r in matched if r["instr"] == "caption"]
    name_caps = [r for r in cap_rows if r["attrs"].get("k") == "name"]
    primary_cap = name_caps[-1] if name_caps else (cap_rows[-1] if cap_rows else None)

    label_above = False
    if has_label and primary_cap is not None:
        pos = primary_cap["attrs"].get("position", "")
        if pos == "above":
            label_above = True
        elif not pos:
            try:
                if float(primary_cap["attrs"].get("dy", "0")) < 0:
                    label_above = True
            except ValueError:
                pass

    cx = w / 2.0
    if has_label:
        cy = (h / 2.0 + 7.0) if label_above else (h / 2.0 - 9.0)
    else:
        cy = h / 2.0

    body: list[str] = [
        f'<rect width="{w}" height="{h}" rx="{6 if compact else 8}" fill="#f7f6f1"/>'
    ]

    # Render circles first (if any)
    for r in matched:
        if r["instr"] == "circle":
            attrs = r["attrs"]
            try:
                rad = max(5.0, min(14.0 if compact else 18.0, float(attrs.get("radius", "4")) * 2.2))
            except ValueError:
                rad = 8.0
            fill_rgb, fill_a = parse_mf_color(attrs.get("fill", "#CCCCCC"))
            stroke_attr = ""
            if "stroke" in attrs:
                s_rgb, s_a = parse_mf_color(attrs["stroke"])
                stroke_attr = f' stroke="{s_rgb}" stroke-opacity="{s_a}" stroke-width="2"'
            body.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" '
                f'fill="{fill_rgb}" fill-opacity="{fill_a}"{stroke_attr}/>'
            )

    # Render last matched symbol (most specific rule at this zoom)
    sym_rows = [r for r in matched if r["instr"] == "symbol" and "src" in r["attrs"]]
    if sym_rows:
        src_name = sym_rows[-1]["attrs"]["src"].split("/")[-1]
        uri = _file_data_uri(res_dir / src_name)
        if uri:
            icon_sz = 26 if compact else 36
            body.append(
                f'<image href="{uri}" x="{cx - icon_sz / 2:.1f}" y="{cy - icon_sz / 2:.1f}" '
                f'width="{icon_sz}" height="{icon_sz}" preserveAspectRatio="xMidYMid meet"/>'
            )

    if has_label:
        fill_rgb = "#222222"
        stroke_rgb = "#FFFFFF"
        weight = "700"
        if primary_cap is not None:
            c_attrs = primary_cap["attrs"]
            fill_rgb, _ = parse_mf_color(c_attrs.get("fill", "#222222"))
            stroke_rgb, _ = parse_mf_color(c_attrs.get("stroke", "#FFFFFF"))
            if c_attrs.get("font-style") == "normal":
                weight = "600"
        text_y = 18.0 if label_above else (h - 10.0)
        body.append(
            f'<text x="{cx:.1f}" y="{text_y:.1f}" text-anchor="middle" '
            f'font-size="12" font-weight="{weight}" font-family="sans-serif" '
            f'fill="{fill_rgb}" stroke="{stroke_rgb}" stroke-width="3.2" paint-order="stroke">'
            f"{html.escape(entry.sample_label)}</text>"
        )

    return (
        f'<svg class="legend-svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(entry.name, quote=True)}">'
        f"{''.join(body)}</svg>"
    )


# ---------------------------------------------------------------------------
# Entry loading, evaluation & coverage check
# ---------------------------------------------------------------------------


@dataclass
class UncatalogedIcon:
    src: str
    svg: str
    geom: str
    tags_text: str
    zoom_min: int
    cats_label: str
    rule_tests: list[list[tuple[str, str]]] = field(default_factory=list)
    taiwan_count: int | None = None


# ---------------------------------------------------------------------------
# Fast pure-stdlib PMTiles z=14 MVT scanner (detects Taiwan-wide occurrences)
# ---------------------------------------------------------------------------


def _mvt_varint(buf: bytes | memoryview, i: int) -> tuple[int, int]:
    val = shift = 0
    while True:
        b = buf[i]
        i += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, i
        shift += 7


def _mvt_skip(buf: memoryview, i: int, wire: int) -> int:
    if wire == 0:
        _, i = _mvt_varint(buf, i)
        return i
    if wire == 1:
        return i + 8
    if wire == 2:
        ln, i = _mvt_varint(buf, i)
        return i + ln
    if wire == 5:
        return i + 4
    raise ValueError(f"Unsupported protobuf wire type {wire}")


def _mvt_val(buf: memoryview) -> str:
    i = 0
    end = len(buf)
    while i < end:
        tag, i = _mvt_varint(buf, i)
        fn, wire = tag >> 3, tag & 7
        if fn == 1 and wire == 2:
            ln, i = _mvt_varint(buf, i)
            return bytes(buf[i : i + ln]).decode("utf-8", errors="replace")
        if fn == 2 and wire == 5:
            return str(struct.unpack("<f", buf[i : i + 4])[0])
        if fn == 3 and wire == 1:
            return str(struct.unpack("<d", buf[i : i + 8])[0])
        if fn in (4, 5) and wire == 0:
            v, i = _mvt_varint(buf, i)
            return str(v)
        if fn == 6 and wire == 0:
            v, i = _mvt_varint(buf, i)
            return str((v >> 1) ^ -(v & 1))
        if fn == 7 and wire == 0:
            v, i = _mvt_varint(buf, i)
            return "true" if v else "false"
        i = _mvt_skip(buf, i, wire)
    return ""


def _pmtiles_parse_dir(raw: bytes, comp: int) -> list[tuple[int, int, int, int]]:
    if comp == 2:
        raw = gzip.decompress(raw)
    n, i = _mvt_varint(raw, 0)
    tids: list[int] = []
    last = 0
    for _ in range(n):
        d, i = _mvt_varint(raw, i)
        last += d
        tids.append(last)
    runs: list[int] = []
    for _ in range(n):
        v, i = _mvt_varint(raw, i)
        runs.append(v)
    lens: list[int] = []
    for _ in range(n):
        v, i = _mvt_varint(raw, i)
        lens.append(v)
    offs: list[int] = []
    for k in range(n):
        v, i = _mvt_varint(raw, i)
        offs.append(offs[-1] + lens[k - 1] if k > 0 and v == 0 else v - 1)
    return list(zip(tids, offs, lens, runs, strict=True))


def _tid_to_zoom(tid: int) -> int:
    z = 0
    acc = 0
    while True:
        cnt = 1 << (2 * z)
        if tid < acc + cnt:
            return z
        acc += cnt
        z += 1


def _scan_pmtiles_chunk(
    args: tuple[str, int, list[tuple[int, int]], list[tuple[str, list[list[tuple[str, str]]]]]],
) -> dict[str, int]:
    path_str, data_off, chunk, targets = args
    counts: dict[str, int] = {src: 0 for src, _ in targets}
    # Precompute positive required key-sets per target rule for fast tile key-table skip
    compiled: list[tuple[str, list[tuple[list[tuple[str, str]], list[tuple[str, ...]]]]]] = []
    for src, rule_list in targets:
        c_rules = []
        for tests in rule_list:
            pos_key_groups: list[tuple[str, ...]] = []
            for k_expr, v_expr in tests:
                vals = v_expr.split("|")
                if "~" not in vals:
                    pos_key_groups.append(tuple(k_expr.split("|")))
            c_rules.append((tests, pos_key_groups))
        compiled.append((src, c_rules))

    with open(path_str, "rb") as f:
        for off, ln in chunk:
            f.seek(data_off + off)
            raw = f.read(ln)
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            mv = memoryview(raw)
            i = 0
            end = len(mv)
            while i < end:
                tag, i = _mvt_varint(mv, i)
                fn, wire = tag >> 3, tag & 7
                if fn == 3 and wire == 2:
                    lln, i = _mvt_varint(mv, i)
                    _scan_mvt_layer_for_targets(mv[i : i + lln], compiled, counts)
                    i += lln
                else:
                    i = _mvt_skip(mv, i, wire)
    return counts


def _scan_mvt_layer_for_targets(
    lmv: memoryview,
    compiled: list[tuple[str, list[tuple[list[tuple[str, str]], list[tuple[str, ...]]]]]],
    counts: dict[str, int],
) -> None:
    i = 0
    end = len(lmv)
    layer_name = ""
    keys: list[str] = []
    vals: list[str] = []
    feat_slices: list[memoryview] = []
    while i < end:
        tag, i = _mvt_varint(lmv, i)
        fn, wire = tag >> 3, tag & 7
        if fn == 1 and wire == 2:
            ln, i = _mvt_varint(lmv, i)
            layer_name = bytes(lmv[i : i + ln]).decode("utf-8", errors="replace")
            i += ln
            if layer_name in ("contour", "water", "route_label"):
                return
        elif fn == 2 and wire == 2:
            ln, i = _mvt_varint(lmv, i)
            feat_slices.append(lmv[i : i + ln])
            i += ln
        elif fn == 3 and wire == 2:
            ln, i = _mvt_varint(lmv, i)
            keys.append(bytes(lmv[i : i + ln]).decode("utf-8", errors="replace"))
            i += ln
        elif fn == 4 and wire == 2:
            ln, i = _mvt_varint(lmv, i)
            vals.append(_mvt_val(lmv[i : i + ln]))
            i += ln
        else:
            i = _mvt_skip(lmv, i, wire)

    key_set = set(keys)
    if layer_name == "transportation" and "class" in key_set:
        key_set.add("highway")
    if layer_name == "place" and "class" in key_set:
        key_set.add("place")
    if layer_name == "ele_point" and "class" in key_set:
        key_set.update(("natural", "man_made"))
    if layer_name == "landcover" and "area" not in key_set:
        key_set.add("area")

    active: list[tuple[str, list[list[tuple[str, str]]]]] = []
    for src, c_rules in compiled:
        matched_rules = [
            tests
            for tests, pos_groups in c_rules
            if all(any(k in key_set for k in grp) for grp in pos_groups)
        ]
        if matched_rules:
            active.append((src, matched_rules))
    if not active:
        return

    for fmv in feat_slices:
        fi = 0
        fend = len(fmv)
        tags_mv: memoryview | None = None
        while fi < fend:
            ftag, fi = _mvt_varint(fmv, fi)
            ffn, fwire = ftag >> 3, ftag & 7
            if ffn == 2 and fwire == 2:
                ln, fi = _mvt_varint(fmv, fi)
                tags_mv = fmv[fi : fi + ln]
                fi += ln
            else:
                fi = _mvt_skip(fmv, fi, fwire)
        if tags_mv is None:
            continue
        props: dict[str, str] = {}
        ti = 0
        tend = len(tags_mv)
        while ti < tend:
            ki, ti = _mvt_varint(tags_mv, ti)
            vi, ti = _mvt_varint(tags_mv, ti)
            if ki < len(keys) and vi < len(vals):
                props[keys[ki]] = vals[vi]
        if layer_name == "transportation" and "class" in props and "highway" not in props:
            props["highway"] = props["class"]
        if layer_name == "place" and "class" in props and "place" not in props:
            props["place"] = props["class"]
        if layer_name == "ele_point" and "class" in props:
            cls_v = props["class"]
            if cls_v in ("peak", "volcano") and "natural" not in props:
                props["natural"] = cls_v
            elif cls_v == "summit_board" and "man_made" not in props:
                props["man_made"] = cls_v
        if layer_name == "landcover" and "area" not in props:
            props["area"] = "yes"

        for src, rule_list in active:
            for tests in rule_list:
                if all(_test_matches(k, v, props) for k, v in tests):
                    counts[src] += 1
                    break


def count_uncataloged_in_pmtiles(
    pmtiles_path: Path, uncataloged: list[UncatalogedIcon]
) -> dict[str, int]:
    """Scan all unique maxzoom tiles in a local PMTiles archive for uncataloged icons."""
    if not uncataloged or not pmtiles_path.is_file():
        return {}
    with pmtiles_path.open("rb") as f:
        hdr = f.read(127)
        root_off, root_len, _mo, _ml, leaf_off, leaf_len, data_off, _dl = struct.unpack(
            "<QQQQQQQQ", hdr[8:72]
        )
        int_comp = hdr[97]
        max_z = hdr[101]
        f.seek(root_off)
        root_entries = _pmtiles_parse_dir(f.read(root_len), int_comp)
        f.seek(leaf_off)
        leaf_raw = f.read(leaf_len)

    all_entries: list[tuple[int, int, int, int]] = []
    for tid, off, ln, run in root_entries:
        if run == 0:
            all_entries.extend(_pmtiles_parse_dir(leaf_raw[off : off + ln], int_comp))
        else:
            all_entries.append((tid, off, ln, run))

    unique_maxz: dict[int, int] = {}
    for tid, off, ln, _run in all_entries:
        if _tid_to_zoom(tid) == max_z and off not in unique_maxz:
            unique_maxz[off] = ln

    tiles = list(unique_maxz.items())
    targets = [(u.src, u.rule_tests) for u in uncataloged]
    n_workers = min(8, os.cpu_count() or 4)
    chunk_size = max(1, (len(tiles) + n_workers - 1) // n_workers)
    chunks = [
        (str(pmtiles_path), data_off, tiles[i : i + chunk_size], targets)
        for i in range(0, len(tiles), chunk_size)
    ]

    totals: dict[str, int] = {u.src: 0 for u in uncataloged}
    with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as pool:
        for partial in pool.map(_scan_pmtiles_chunk, chunks):
            for k, v in partial.items():
                totals[k] += v
    return totals


# Catalog items whose tags are intentionally omitted by osm_scripts/pmtiles/process.lua
# are derived automatically via PmtilesExportSpec.is_exported() below.


@dataclass
class PmtilesExportSpec:
    """Parsed export whitelist from osm_scripts/pmtiles/process.lua + tag-mapping.xml."""

    tm_pois: dict[str, set[str]]
    tm_ways: dict[str, set[str]]
    hiking_poi: dict[str, set[str]]
    generic_poi: dict[str, set[str]]
    generic_area_poi: dict[str, set[str]]
    landcover: dict[str, set[str]]
    line_feature: dict[str, set[str]]
    waterway: set[str]
    water_natural: set[str]
    hiking_networks: set[str]
    cycle_networks: set[str]

    def is_exported(self, geom: str, tags: dict[str, str]) -> bool:
        """Return True if process.lua exports this feature type into PMTiles."""
        clean = {k: v for k, v in tags.items() if k not in ("name", "ele", "ref", "cap", "is_in", "area")}
        if geom == "point":
            if clean.get("man_made") == "summit_board" or clean.get("natural") in ("peak", "volcano"):
                return True
            if any(k in ("safety_rope", "ladder", "rungs", "via_ferrata_flag") for k in clean):
                return True
            for tbl in (self.hiking_poi, self.generic_poi, self.generic_area_poi):
                for k, v in clean.items():
                    if v in tbl.get(k, set()) and (v in self.tm_pois.get(k, set()) or v in self.tm_ways.get(k, set())):
                        return True
            return False
        if geom == "area":
            if clean.get("natural") in self.water_natural or clean.get("landuse") in ("reservoir", "basin"):
                return True
            if "building" in clean:
                return True
            for k, v in clean.items():
                if v in self.landcover.get(k, set()) and v in self.tm_ways.get(k, set()):
                    return True
            return False
        # line
        if "oneway" in clean:
            return False
        if "contour_ext" in clean:
            return True
        if clean.get("hknetwork") in self.hiking_networks or clean.get("highlight") == "yes":
            return True
        if clean.get("network") in self.cycle_networks:
            return True
        if clean.get("waterway") in self.waterway:
            return True
        if "admin_level" in clean and clean["admin_level"] in self.tm_ways.get("admin_level", set()):
            return True
        if "boundary" in clean and clean["boundary"] in self.tm_ways.get("boundary", set()):
            return True
        if "highway" in clean and clean["highway"] in self.tm_ways.get("highway", set()):
            return True
        if "railway" in clean and clean["railway"] in self.tm_ways.get("railway", set()):
            return True
        if "aerialway" in clean:
            return True
        return any(v in self.line_feature.get(k, set()) for k, v in clean.items())


def _extract_lua_nested_table(txt: str, var_name: str) -> dict[str, set[str]]:
    m = re.search(rf"local\s+{re.escape(var_name)}\s*=\s*\{{", txt)
    if not m:
        return {}
    i = m.end() - 1
    depth = 0
    end = i
    for j in range(i, len(txt)):
        ch = txt[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = j
                break
    body = txt[i + 1 : end]
    out: dict[str, set[str]] = {}
    for km in re.finditer(r'(?:\[\s*"([^"]+)"\s*\]|([A-Za-z0-9_:-]+))\s*=\s*\{([^}]*)\}', body):
        k = km.group(1) or km.group(2)
        vals = {
            vm.group(1) or vm.group(2)
            for vm in re.finditer(r'(?:\[\s*"([^"]+)"\s*\]|([A-Za-z0-9_:-]+))\s*=\s*(?:true|\d+)', km.group(3))
        }
        out[k] = vals
    return out


def _extract_lua_flat_set(txt: str, var_name: str) -> set[str]:
    m = re.search(rf"local\s+{re.escape(var_name)}\s*=\s*\{{([^}}]*)\}}", txt)
    if not m:
        return set()
    return {
        vm.group(1) or vm.group(2)
        for vm in re.finditer(r'(?:\[\s*"([^"]+)"\s*\]|([A-Za-z0-9_:-]+))\s*=\s*(?:true|\d+)', m.group(1))
    }


def parse_pmtiles_export_spec(process_lua_path: Path, tag_mapping_path: Path) -> PmtilesExportSpec | None:
    """Parse osm_scripts/pmtiles/process.lua and osm_scripts/tag-mapping.xml."""
    if not process_lua_path.is_file() or not tag_mapping_path.is_file():
        return None
    lua_txt = process_lua_path.read_text(encoding="utf-8")
    tm_root = ET.parse(tag_mapping_path).getroot()
    for el in tm_root.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]

    tm: dict[str, dict[str, set[str]]] = {"pois": {}, "ways": {}}
    for sec in ("pois", "ways"):
        sec_el = tm_root.find(sec)
        if sec_el is None:
            continue
        sec_map = tm[sec]
        for tag_el in sec_el.findall(".//osm-tag"):
            k = tag_el.get("key")
            v = tag_el.get("value")
            if not k or not v:
                continue
            vals = sec_map.setdefault(k, set())
            vals.add(v)
            eq = tag_el.get("equivalent-values", "")
            if eq:
                for ev in eq.split(","):
                    if ev.strip():
                        vals.add(ev.strip())

    return PmtilesExportSpec(
        tm_pois=tm["pois"],
        tm_ways=tm["ways"],
        hiking_poi=_extract_lua_nested_table(lua_txt, "hiking_poi_zoom"),
        generic_poi=_extract_lua_nested_table(lua_txt, "generic_poi_theme_zoom"),
        generic_area_poi=_extract_lua_nested_table(lua_txt, "generic_area_poi_zoom"),
        landcover=_extract_lua_nested_table(lua_txt, "landcover_theme"),
        line_feature=_extract_lua_nested_table(lua_txt, "line_feature_minzoom"),
        waterway=_extract_lua_flat_set(lua_txt, "waterway_class"),
        water_natural=_extract_lua_flat_set(lua_txt, "water_natural"),
        hiking_networks=_extract_lua_flat_set(lua_txt, "hiking_networks"),
        cycle_networks=_extract_lua_flat_set(lua_txt, "cycle_networks"),
    )


@dataclass
class PmtilesDiffItem:
    id: str
    name: str
    svg: str
    geom: str
    tags_text: str
    diff_kind: str  # "default_missing" | "partial" | "overlay_missing" | "uncataloged_missing"
    reason: str
    overlay_group: str
    exported_in_tiles: bool


def compute_mapsforge_pmtiles_diffs(
    theme_path: Path,
    pmtiles_style_path: Path,
    entries: list[LegendEntry],
    uncataloged: list[UncatalogedIcon],
    export_spec: PmtilesExportSpec | None,
) -> list[PmtilesDiffItem]:
    """Automatically compare MOI_OSM.xml (Mapsforge) against PMTiles style.json + process.lua."""
    if not pmtiles_style_path.is_file():
        return []
    style = json.loads(pmtiles_style_path.read_text(encoding="utf-8"))
    by_n: dict[int, list[str]] = {}
    by_xm: dict[int, list[str]] = {}
    custom_layer_ids: set[str] = set()
    for lay in style.get("layers", []):
        lid = str(lay.get("id", ""))
        m_xm = re.search(r"-x(\d+)$", lid)
        m_n = re.search(r"-(\d+)$", lid)
        if m_xm:
            by_xm.setdefault(int(m_xm.group(1)), []).append(lid)
        elif m_n:
            by_n.setdefault(int(m_n.group(1)), []).append(lid)
        else:
            custom_layer_ids.add(lid)

    root, active_cats, rows = pt.all_rows(str(theme_path), style_id="elmt-hiking")
    overlay_map = parse_stylemenu_overlays(root, style_id="elmt-hiking")
    all_ov_cats = set(overlay_map.keys())

    diffs: list[PmtilesDiffItem] = []

    for e in entries:
        mrows, _ = match_rows(rows, active_cats, e.e, e.closed, e.tags, e.zoom, e.extra_cats, all_ov_cats)
        vis_rows = [r for r in mrows if r["instr"] not in ("caption", "pathText")]
        if not vis_rows:
            continue

        # Handle the 3 custom-named non-numeric layer families in style.json
        has_custom = (
            ("contour_ext" in e.tags and any(lid.startswith("contour-ext-") for lid in custom_layer_ids))
            or (e.geom == "area" and e.tags.get("natural") == "water" and "water" in custom_layer_ids)
        )
        has_cycle_custom = (
            e.tags.get("network") in ("lcn", "rcn", "ncn", "icn", "mtb") and "cycle-route" in custom_layer_ids
        )
        if has_custom:
            continue

        matched_lids: list[str] = []
        missing_instrs: list[str] = []
        for r in vis_rows:
            cands = by_n.get(r["n"], []) if r["n"] is not None else by_xm.get(r["m"], [])
            if cands:
                matched_lids.extend(cands)
            else:
                missing_instrs.append(str(r["instr"]))

        exported = export_spec.is_exported(e.geom, e.tags) if export_spec else True
        off_ovs = [ov.name_zh for ov in e.overlays if not ov.enabled_default]
        tag_str = _format_tags(e.tags)

        if has_cycle_custom:
            diffs.append(
                PmtilesDiffItem(
                    id=e.id,
                    name=e.name,
                    svg=e.svg_compact,
                    geom=e.geom,
                    tags_text=tag_str,
                    diff_kind="partial",
                    reason="改以單一簡化線層（cycle-route）繪製，無分級光暈",
                    overlay_group="",
                    exported_in_tiles=exported,
                )
            )
            continue

        if not matched_lids:
            if off_ovs:
                diffs.append(
                    PmtilesDiffItem(
                        id=e.id,
                        name=e.name,
                        svg=e.svg_compact,
                        geom=e.geom,
                        tags_text=tag_str,
                        diff_kind="overlay_missing",
                        reason="style.json 未收錄此預設關閉圖層",
                        overlay_group=off_ovs[0],
                        exported_in_tiles=exported,
                    )
                )
            else:
                if "circle" in missing_instrs:
                    reason = "僅顯示名稱文字，未繪製圓點（<circle>）"
                elif e.geom == "area":
                    reason = "PMTiles 未繪製此區域紋理"
                else:
                    reason = "PMTiles style.json 未繪製"
                diffs.append(
                    PmtilesDiffItem(
                        id=e.id,
                        name=e.name,
                        svg=e.svg_compact,
                        geom=e.geom,
                        tags_text=tag_str,
                        diff_kind="default_missing",
                        reason=reason,
                        overlay_group="",
                        exported_in_tiles=exported,
                    )
                )
        elif missing_instrs:
            if "lineSymbol" in missing_instrs:
                reason = "僅畫線條，缺少沿線重複符號（<lineSymbol>）"
            else:
                reason = f"缺少部分繪圖指令（{', '.join(dict.fromkeys(missing_instrs))}）"
            diffs.append(
                PmtilesDiffItem(
                    id=e.id,
                    name=e.name,
                    svg=e.svg_compact,
                    geom=e.geom,
                    tags_text=tag_str,
                    diff_kind="partial",
                    reason=reason,
                    overlay_group="",
                    exported_in_tiles=exported,
                )
            )

    # Also compare ALL uncataloged MOI_OSM.xml resources against style.json
    rows_by_src: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        if r["instr"] in ("symbol", "area", "lineSymbol") and "src" in r["attrs"]:
            src = r["attrs"]["src"].split("/")[-1]
            if src:
                rows_by_src.setdefault(src, []).append(r)

    for u in uncataloged:
        s_rows = rows_by_src.get(u.src, [])
        in_style = any(
            (by_n.get(r["n"]) if r["n"] is not None else by_xm.get(r["m"]))
            for r in s_rows
        )
        if not in_style:
            is_other_mode = all(
                any(c in ("city", "nohike", "pt_network", "c_routes", "mtb_routes") for c in r["cats"])
                for r in s_rows
            )
            reason = (
                "僅都市／單車模式使用，PMTiles（登山風格）未收錄"
                if is_other_mode
                else "未收錄於 PMTiles style.json"
            )
            tw_note = f"（台灣 {u.taiwan_count:,} 筆）" if (u.taiwan_count or 0) > 0 else "（台灣 0 筆）"
            diffs.append(
                PmtilesDiffItem(
                    id=f"uncat-{u.src}",
                    name=u.src,
                    svg=u.svg,
                    geom=u.geom,
                    tags_text=u.tags_text,
                    diff_kind="uncataloged_missing",
                    reason=f"{reason}{tw_note}",
                    overlay_group="",
                    exported_in_tiles=(u.taiwan_count or 0) > 0,
                )
            )

    return diffs


def _normalize_pmtiles_tags(lname: str, td: dict[str, str]) -> dict[str, str]:
    """Map PMTiles MVT layer/class properties back to OSM-style tags used in catalog.toml."""
    out = dict(td)
    cls = td.get("class", "")
    sub = td.get("subclass", "")
    if lname == "transportation":
        if cls in (
            "motorway",
            "trunk",
            "primary",
            "secondary",
            "tertiary",
            "residential",
            "track",
            "path",
            "cycleway",
            "steps",
            "footway",
        ):
            out.setdefault("highway", cls)
        if cls == "cycleway":
            out.setdefault("network", "lcn")
        if sub == "steps":
            out["highway"] = "steps"
        if cls == "railway" and sub:
            out.setdefault("railway", sub)
        if cls == "aerialway" and sub:
            if sub in ("platter", "t-bar", "j-bar"):
                out["aerialway"] = "drag_lift"
            else:
                out.setdefault("aerialway", sub)
        if td.get("access") == "no":
            out["access"] = "acc_no"
    elif lname == "waterway":
        if cls:
            out.setdefault("waterway", cls)
    elif lname == "water":
        out.setdefault("natural", "water")
    elif lname == "boundary":
        if cls and cls != "administrative":
            out.setdefault("boundary", cls)
        if "admin_level" in td:
            out["admin_level"] = str(td["admin_level"])
    elif lname == "contour":
        if cls:
            out["contour_ext"] = cls
    elif lname == "building":
        out.setdefault("building", "yes")
    elif lname == "hiking_route":
        out.setdefault("highway", "path")
        out.setdefault("sac_scale", "hiking")
        if td.get("network"):
            out["hknetwork"] = td["network"]
    elif lname == "ele_point":
        if cls == "summit_board":
            out["man_made"] = "summit_board"
            if td.get("cat") == "baiyue":
                out["zl"] = "0"
            elif td.get("cat") == "xiaobaiyue":
                out["zl"] = "2"
        elif cls == "peak":
            out["natural"] = "peak"
        elif cls == "volcano":
            out["natural"] = "volcano"
        elif cls == "saddle":
            out["mountain_pass"] = "yes"
    elif lname == "poi":
        if cls == "tower" and sub:
            out.setdefault("tower", sub)
        if td.get("access") in ("no", "acc_no", "private"):
            out["access"] = "private"
        if td.get("aeroway") == "aerodrome":
            out["aeroway"] = "airport"
        if td.get("ford") in ("yes", "fd_yes"):
            out.setdefault("highway", "ford")
        if td.get("information") == "trail_milestone":
            out["zl"] = "0"
        if td.get("highway") == "emergency_access_point":
            out["zl"] = "0"
        if td.get("via_ferrata_flag") == "set":
            out["via_ferrata_flag"] = "yes"
    elif lname == "landcover":
        if td.get("access") == "no":
            out["access"] = "acc_no"
        if td.get("landuse") == "commercial":
            out["landuse"] = "industrial"
    return out


def _scan_pmtiles_catalog_chunk(
    args: tuple[str, int, list[tuple[int, int]], list[tuple[str, str, list[tuple[str, str]]]]],
) -> dict[str, int]:
    pm_path, data_off, tiles, specs = args
    by_kv: dict[tuple[str, str], list[tuple[str, str, list[tuple[str, str]]]]] = {}
    for iid, geom, req in specs:
        if req:
            by_kv.setdefault(req[0], []).append((iid, geom, req))

    counts: dict[str, int] = {iid: 0 for iid, _, _ in specs}
    with open(pm_path, "rb") as f:
        for off, ln in tiles:
            f.seek(data_off + off)
            raw = f.read(ln)
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            mv = memoryview(raw)
            p = 0
            n = len(mv)
            while p < n:
                tag, p = _mvt_varint(mv, p)
                fn, wt = tag >> 3, tag & 7
                if fn == 3 and wt == 2:
                    llen, p = _mvt_varint(mv, p)
                    lb = mv[p : p + llen]
                    p += llen
                    lp = 0
                    ln_len = len(lb)
                    lname = ""
                    keys: list[str] = []
                    vals: list[str] = []
                    feats: list[memoryview] = []
                    while lp < ln_len:
                        lt, lp = _mvt_varint(lb, lp)
                        lfn, lwt = lt >> 3, lt & 7
                        if lfn == 1 and lwt == 2:
                            sl, lp = _mvt_varint(lb, lp)
                            lname = bytes(lb[lp : lp + sl]).decode("utf-8", errors="ignore")
                            lp += sl
                        elif lfn == 3 and lwt == 2:
                            sl, lp = _mvt_varint(lb, lp)
                            keys.append(bytes(lb[lp : lp + sl]).decode("utf-8", errors="ignore"))
                            lp += sl
                        elif lfn == 4 and lwt == 2:
                            sl, lp = _mvt_varint(lb, lp)
                            vals.append(_mvt_val(lb[lp : lp + sl]))
                            lp += sl
                        elif lfn == 2 and lwt == 2:
                            sl, lp = _mvt_varint(lb, lp)
                            feats.append(lb[lp : lp + sl])
                            lp += sl
                        else:
                            lp = _mvt_skip(lb, lp, lwt)
                    for fb in feats:
                        fp = 0
                        f_len = len(fb)
                        gtype = 0
                        td: dict[str, str] = {}
                        while fp < f_len:
                            ft, fp = _mvt_varint(fb, fp)
                            ffn, fwt = ft >> 3, ft & 7
                            if ffn == 3 and fwt == 0:
                                gtype, fp = _mvt_varint(fb, fp)
                            elif ffn == 2 and fwt == 2:
                                sl, fp = _mvt_varint(fb, fp)
                                end = fp + sl
                                while fp < end:
                                    ki, fp = _mvt_varint(fb, fp)
                                    vi, fp = _mvt_varint(fb, fp)
                                    if ki < len(keys) and vi < len(vals):
                                        td[keys[ki]] = vals[vi]
                            else:
                                fp = _mvt_skip(fb, fp, fwt)
                        nt = _normalize_pmtiles_tags(lname, td)
                        for k, v in nt.items():
                            cands = by_kv.get((k, v))
                            if not cands:
                                continue
                            for iid, geom, req in cands:
                                if geom == "line" and gtype != 2:
                                    continue
                                if geom == "area" and gtype != 3:
                                    continue
                                if all(nt.get(rk) == rv for rk, rv in req):
                                    counts[iid] += 1
                else:
                    p = _mvt_skip(mv, p, wt)
    return counts


def count_catalog_in_pmtiles(
    pmtiles_path: Path,
    entries: list[LegendEntry],
    export_spec: PmtilesExportSpec | None = None,
) -> dict[str, int]:
    """Count max-zoom Taiwan occurrences for PMTiles-verifiable catalog entries."""
    with pmtiles_path.open("rb") as f:
        hdr = f.read(127)
        if hdr[:7] != b"PMTiles":
            return {}
        root_off, root_len, _m_off, _m_len, leaf_off, leaf_len, data_off, _d_len = struct.unpack("<8Q", hdr[8:72])
        int_comp = hdr[97]
        max_z = hdr[101]
        f.seek(root_off)
        root_entries = _pmtiles_parse_dir(f.read(root_len), int_comp)
        f.seek(leaf_off)
        leaf_raw = f.read(leaf_len)

    all_entries: list[tuple[int, int, int, int]] = []
    for tid, off, ln, run in root_entries:
        if run == 0:
            all_entries.extend(_pmtiles_parse_dir(leaf_raw[off : off + ln], int_comp))
        else:
            all_entries.append((tid, off, ln, run))

    unique_maxz: dict[int, int] = {}
    for tid, off, ln, _run in all_entries:
        if _tid_to_zoom(tid) == max_z and off not in unique_maxz:
            unique_maxz[off] = ln

    tiles = list(unique_maxz.items())
    specs: list[tuple[str, str, list[tuple[str, str]]]] = []
    for e in entries:
        if export_spec is not None and not export_spec.is_exported(e.geom, e.tags):
            continue
        req = [(k, v) for k, v in e.tags.items() if k not in ("name", "ele", "ref", "cap", "is_in", "area")]
        if req:
            specs.append((e.id, e.geom, req))

    n_workers = min(8, os.cpu_count() or 4)
    chunk_size = max(1, (len(tiles) + n_workers - 1) // n_workers)
    chunks = [
        (str(pmtiles_path), data_off, tiles[i : i + chunk_size], specs)
        for i in range(0, len(tiles), chunk_size)
    ]

    totals: dict[str, int] = {iid: 0 for iid, _, _ in specs}
    with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as pool:
        for partial in pool.map(_scan_pmtiles_catalog_chunk, chunks):
            for k, v in partial.items():
                totals[k] += v
    return totals


def _synthesize_uncataloged_svg(src: str, row: dict[str, Any], res_dir: Path) -> str:
    uri = _file_data_uri(res_dir / src)
    if not uri:
        return ""
    instr = row["instr"]
    if instr == "area":
        pat_id = f"uncat-{re.sub(r'[^a-zA-Z0-9_-]', '_', src)}"
        return (
            f'<svg class="uncat-svg" viewBox="0 0 64 40" width="64" height="40" xmlns="http://www.w3.org/2000/svg">'
            f'<defs><pattern id="{pat_id}" width="16" height="16" patternUnits="userSpaceOnUse">'
            f'<image href="{uri}" width="16" height="16"/></pattern></defs>'
            f'<rect width="64" height="40" rx="5" fill="#f7f6f1"/>'
            f'<rect x="4" y="4" width="56" height="32" rx="4" fill="url(#{pat_id})" stroke="#c8d1cb" stroke-width="0.8"/>'
            "</svg>"
        )
    if instr == "lineSymbol":
        return (
            '<svg class="uncat-svg" viewBox="0 0 64 40" width="64" height="40" xmlns="http://www.w3.org/2000/svg">'
            '<rect width="64" height="40" rx="5" fill="#f7f6f1"/>'
            '<line x1="6" y1="20" x2="58" y2="20" stroke="#777777" stroke-width="1.6"/>'
            f'<image href="{uri}" x="22" y="10" width="20" height="20" preserveAspectRatio="xMidYMid meet"/>'
            "</svg>"
        )
    return (
        '<svg class="uncat-svg" viewBox="0 0 44 44" width="44" height="44" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="44" height="44" rx="5" fill="#f7f6f1"/>'
        f'<image href="{uri}" x="8" y="8" width="28" height="28" preserveAspectRatio="xMidYMid meet"/>'
        "</svg>"
    )


def build_entries(
    catalog_path: Path,
    theme_path: Path,
    res_dir: Path,
) -> tuple[list[dict[str, Any]], list[LegendEntry], set[str], set[str], list[UncatalogedIcon]]:
    """Load catalog.toml, evaluate against MOI_OSM.xml, and synthesize SVGs."""
    catalog = tomllib.loads(catalog_path.read_text(encoding="utf-8"))
    categories: list[dict[str, Any]] = catalog["categories"]
    raw_items: list[dict[str, Any]] = catalog["items"]
    cat_dense = {c["id"]: bool(c.get("dense", False)) for c in categories}

    root, active_cats, rows = pt.all_rows(str(theme_path), style_id="elmt-hiking")
    overlay_map = parse_stylemenu_overlays(root, style_id="elmt-hiking")

    entries: list[LegendEntry] = []
    covered_srcs: set[str] = set()

    for raw in raw_items:
        geom = raw.get("geom", "point")
        e = raw.get("e", "node" if geom == "point" else "way")
        closed = raw.get("closed", "yes" if geom == "area" else ("no" if geom == "line" else "any"))
        tags = {str(k): str(v) for k, v in raw.get("tags", {}).items()}
        zoom = int(raw.get("zoom", 16))
        extra_cats = list(raw.get("extra_cats", []))
        is_dense = bool(raw.get("dense", False)) or cat_dense.get(raw["category"], False)

        entry = LegendEntry(
            id=raw["id"],
            category=raw["category"],
            name=raw["name"],
            desc=raw.get("desc", ""),
            compact=bool(raw.get("compact", False)),
            dense=is_dense,
            geom=geom,
            e=e,
            closed=closed,
            tags=tags,
            zoom=zoom,
            extra_cats=extra_cats,
            sample_label=raw.get("sample_label", ""),
            catalog_shapes=list(raw.get("shapes", [])),
            aliases=list(raw.get("aliases", [])),
            example=raw.get("example"),
        )

        matched, min_zoom = match_rows(
            rows, active_cats, e, closed, tags, zoom, extra_cats, set(overlay_map.keys())
        )
        entry.matched_count = len(matched)
        entry.zoom_min = min_zoom

        # Collect overlay layers required by matched visual instructions
        seen_ov: set[str] = set()
        for r in matched:
            if r["instr"] in ("caption", "pathText"):
                continue
            src = r["attrs"].get("src", "").split("/")[-1]
            if src:
                entry.matched_srcs.add(src)
                covered_srcs.add(src)
            for c in r["cats"]:
                if c in overlay_map and c not in seen_ov:
                    seen_ov.add(c)
                    entry.overlays.append(overlay_map[c])

        entry.colors, entry.shapes = detect_colors_and_shapes(
            matched, geom, res_dir, entry.catalog_shapes
        )
        entry.svg_detail = synthesize_svg(entry, matched, res_dir, compact=False)
        entry.svg_compact = synthesize_svg(entry, matched, res_dir, compact=True)
        entries.append(entry)

    # All non-GPX symbols and area patterns present in MOI_OSM.xml
    all_theme_srcs: set[str] = set()
    rows_by_src: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        if r["instr"] in ("symbol", "area", "lineSymbol") and "src" in r["attrs"]:
            src = r["attrs"]["src"].split("/")[-1]
            if src and not src.startswith("s_gpx_"):
                all_theme_srcs.add(src)
                rows_by_src.setdefault(src, []).append(r)

    uncataloged: list[UncatalogedIcon] = []
    for src in sorted(all_theme_srcs - covered_srcs):
        s_rows = rows_by_src.get(src, [])
        if not s_rows:
            continue
        r = s_rows[0]
        geom_u = "area" if r["instr"] == "area" else ("line" if r["instr"] == "lineSymbol" else "point")
        tag_pairs = [f"{k}={v}" for k, v in r["tests"] if not (k == "tunnel" and v == "~|no")]
        cat_labels = [
            overlay_map[c].name_zh if c in overlay_map else c
            for c in r["cats"]
            if c not in ("nocity", "nobike")
        ]
        # Collect distinct rule test-sets across all rules drawing this resource
        seen_tests: set[tuple[tuple[str, str], ...]] = set()
        rule_tests: list[list[tuple[str, str]]] = []
        for sr in s_rows:
            t_key = tuple(sr["tests"])
            if t_key not in seen_tests:
                seen_tests.add(t_key)
                rule_tests.append(list(sr["tests"]))
        uncataloged.append(
            UncatalogedIcon(
                src=src,
                svg=_synthesize_uncataloged_svg(src, r, res_dir),
                geom=geom_u,
                tags_text=", ".join(tag_pairs),
                zoom_min=min(int(sr["zmin"]) for sr in s_rows),
                cats_label=" / ".join(dict.fromkeys(cat_labels)),
                rule_tests=rule_tests,
            )
        )

    return categories, entries, covered_srcs, all_theme_srcs, uncataloged


# ---------------------------------------------------------------------------
# HTML Rendering (Web Interactive + Detail PDF + Compact PDF)
# ---------------------------------------------------------------------------


def _format_tags(tags: dict[str, str]) -> str:
    return ", ".join(f"{k}={v}" for k, v in tags.items() if k not in ("name", "ele", "ref"))


def _overlay_badges_html(entry: LegendEntry) -> tuple[str, bool]:
    """Return (overlay HTML badges, needs_manual_toggle)."""
    if not entry.overlays:
        return "", False
    # Prefer showing off-by-default overlays clearly
    off_ovs = [ov for ov in entry.overlays if not ov.enabled_default]
    if off_ovs:
        badges = "".join(
            f'<span class="meta-badge badge-off" title="預設關閉，需在圖層選單開啟">需開啟：{html.escape(ov.name_zh)}</span>'
            for ov in off_ovs
        )
        return badges, True
    ov = entry.overlays[0]
    return f'<span class="meta-badge">圖層：{html.escape(ov.name_zh)}</span>', False


def render_web_html(
    template: str,
    categories: list[dict[str, Any]],
    entries: list[LegendEntry],
    uncataloged: list[UncatalogedIcon],
    pmtiles_diffs: list[PmtilesDiffItem],
    version: str,
    samples_dir: Path | None,
    out_samples_rel: str,
) -> str:
    color_pills = "".join(
        f'<button type="button" class="filter-chip color-chip" data-color="{cid}">'
        f'<span class="color-dot" style="background:{hex_c}"></span>{label}</button>'
        for cid, label, hex_c in COLOR_META
    )
    shape_pills = "".join(
        f'<button type="button" class="filter-chip" data-shape="{sid}">{label}</button>'
        for sid, label in SHAPE_META
    )
    cat_nav = "".join(
        f'<a class="nav-pill" href="#cat-{c["id"]}">{html.escape(c["name"])}</a>'
        for c in categories
    )

    by_cat: dict[str, list[LegendEntry]] = {c["id"]: [] for c in categories}
    for e in entries:
        by_cat.setdefault(e.category, []).append(e)

    sections_html: list[str] = []
    for cat in categories:
        cat_entries = by_cat.get(cat["id"], [])
        if not cat_entries:
            continue
        normal_cards: list[str] = []
        dense_cards: list[str] = []
        for e in cat_entries:
            ov_html, needs_toggle = _overlay_badges_html(e)
            tw_zero_html = (
                '<span class="meta-badge badge-tw-zero" title="目前台灣最新圖資中尚無此類資料">台灣 0 筆</span>'
                if e.taiwan_count == 0
                else ""
            )
            zoom_html = f'<span class="meta-badge">z{e.zoom_min}+</span>'
            geom_html = f'<span class="meta-badge badge-geom">{GEOM_LABELS.get(e.geom, e.geom)}</span>'
            tag_str = _format_tags(e.tags)
            search_parts = [e.name, e.desc, tag_str, *e.aliases, *[ov.name_zh for ov in e.overlays]]
            if e.taiwan_count == 0:
                search_parts.append("台灣 0 筆 0筆")
            search_blob = " ".join(search_parts).lower()
            data_attrs = (
                f'data-geom="{e.geom}" '
                f'data-colors="{",".join(e.colors)}" '
                f'data-shapes="{",".join(e.shapes)}" '
                f'data-overlay="{"off" if needs_toggle else "on"}" '
                f'data-compact="{"1" if e.compact else "0"}" '
                f'data-search="{html.escape(search_blob, quote=True)}"'
            )

            if e.dense:
                dense_cards.append(
                    f'<article class="legend-card dense-card" {data_attrs}>'
                    f'<div class="dense-swatch dense-swatch-{e.geom}">{e.svg_compact}</div>'
                    '<div class="dense-body">'
                    f'<h3 class="dense-name">{html.escape(e.name)}</h3>'
                    f'<p class="dense-desc">{html.escape(e.desc)}</p>'
                    f'<div class="item-meta">{zoom_html}{ov_html}{tw_zero_html}</div>'
                    f'<div class="item-tags"><code>{html.escape(tag_str)}</code></div>'
                    "</div>"
                    "</article>"
                )
                continue

            # Real Taiwan map sample thumbnail if captured
            sample_html = ""
            if e.example:
                place = e.example.get("place", "")
                lat = e.example.get("lat")
                lon = e.example.get("lon")
                ez = e.example.get("zoom", 16)
                map_url = f"https://tiles.rudymap.tw/#{ez}/{lat}/{lon}"
                sample_file = samples_dir / f"{e.id}.png" if samples_dir else None
                if sample_file and sample_file.is_file():
                    img_src = f"{out_samples_rel}/{e.id}.png"
                    sample_html = (
                        '<div class="sample-box">'
                        f'<button type="button" class="sample-thumb-btn" '
                        f'data-src="{html.escape(img_src, quote=True)}" '
                        f'data-title="{html.escape(e.name, quote=True)}" '
                        f'data-place="{html.escape(place, quote=True)}" '
                        f'data-map-url="{html.escape(map_url, quote=True)}">'
                        f'<img src="{html.escape(img_src, quote=True)}" '
                        f'alt="{html.escape(place or e.name, quote=True)}" loading="lazy">'
                        '<span class="sample-tag">真實範例</span>'
                        "</button>"
                        f'<a class="sample-link" href="{html.escape(map_url, quote=True)}" '
                        f'target="_blank" rel="noopener">{html.escape(place)} ↗</a>'
                        "</div>"
                    )
                else:
                    sample_html = (
                        '<div class="sample-link-only">'
                        f'<a class="sample-link" href="{html.escape(map_url, quote=True)}" '
                        f'target="_blank" rel="noopener">真實地圖位置：{html.escape(place)} ↗</a>'
                        "</div>"
                    )

            normal_cards.append(
                f'<article class="legend-card" {data_attrs}>'
                '<div class="visual-row">'
                f'<div class="swatch-box">{e.svg_detail}<span class="swatch-tag">簡化圖示</span></div>'
                f"{sample_html}"
                "</div>"
                '<div class="card-body">'
                f'<h3 class="item-name">{html.escape(e.name)}</h3>'
                f'<p class="item-desc">{html.escape(e.desc)}</p>'
                f'<div class="item-meta">{geom_html}{zoom_html}{ov_html}{tw_zero_html}</div>'
                f'<div class="item-tags"><code>{html.escape(tag_str)}</code></div>'
                "</div>"
                "</article>"
            )

        body_parts: list[str] = []
        if normal_cards:
            body_parts.append(f'<div class="legend-grid">{"".join(normal_cards)}</div>')
        if dense_cards:
            sub = '<div class="dense-subhead">次要／進階符號</div>' if normal_cards else ""
            body_parts.append(f'<div class="dense-block">{sub}<div class="dense-grid">{"".join(dense_cards)}</div></div>')

        sections_html.append(
            f'<section class="legend-section" id="cat-{cat["id"]}">'
            f'<div class="section-head"><h2>{html.escape(cat["name"])}</h2>'
            f'<span class="section-count">{len(cat_entries)}</span></div>'
            f'<p class="section-desc">{html.escape(cat.get("desc", ""))}</p>'
            f'{"".join(body_parts)}'
            "</section>"
        )

    # Uncataloged MOI_OSM.xml resources: shown ONLY at bottom of web page, hidden by default.
    # Split into (a) present in Taiwan vs (b) absent in Taiwan when PMTiles counts are available.
    uncat_html = ""
    if uncataloged:
        def _render_uncat_cards(items: list[UncatalogedIcon]) -> str:
            out: list[str] = []
            for u in items:
                cat_badge = (
                    f'<span class="meta-badge">{html.escape(u.cats_label)}</span>'
                    if u.cats_label
                    else ""
                )
                cnt_badge = ""
                if u.taiwan_count is not None:
                    if u.taiwan_count > 0:
                        cnt_badge = f'<span class="meta-badge badge-tw-yes">台灣 {u.taiwan_count:,} 筆</span>'
                    else:
                        cnt_badge = '<span class="meta-badge">台灣 0 筆</span>'
                out.append(
                    '<div class="uncat-card">'
                    f'<div class="uncat-swatch">{u.svg}</div>'
                    '<div class="uncat-body">'
                    f'<div class="uncat-name">{html.escape(u.src)}</div>'
                    f'<div class="item-meta"><span class="meta-badge">z{u.zoom_min}+</span>{cnt_badge}{cat_badge}</div>'
                    f'<div class="item-tags"><code>{html.escape(u.tags_text)}</code></div>'
                    "</div>"
                    "</div>"
                )
            return "".join(out)

        has_counts = any(u.taiwan_count is not None for u in uncataloged)
        if has_counts:
            in_tw = sorted(
                [u for u in uncataloged if (u.taiwan_count or 0) > 0],
                key=lambda u: (-(u.taiwan_count or 0), u.src),
            )
            not_in_tw = sorted(
                [u for u in uncataloged if (u.taiwan_count or 0) == 0],
                key=lambda u: u.src,
            )
            summary_text = (
                f"未收錄於 catalog.toml 的 MOI_OSM.xml 原始圖示"
                f"（共 {len(uncataloged)} 項：台灣有出現 {len(in_tw)} 項 ／ 台灣未出現 {len(not_in_tw)} 項，預設隱藏 — 點擊展開）"
            )
            groups_html = ""
            if in_tw:
                groups_html += (
                    f'<div class="uncat-group-head uncat-head-yes">A. 不在 catalog，但有在台灣出現（{len(in_tw)} 項）</div>'
                    f'<div class="uncat-grid">{_render_uncat_cards(in_tw)}</div>'
                )
            if not_in_tw:
                groups_html += (
                    f'<div class="uncat-group-head uncat-head-no">B. 不在 catalog，且未在台灣出現（{len(not_in_tw)} 項）</div>'
                    f'<div class="uncat-grid">{_render_uncat_cards(not_in_tw)}</div>'
                )
        else:
            summary_text = (
                f"未收錄於 catalog.toml 的 MOI_OSM.xml 原始圖示（共 {len(uncataloged)} 項，預設隱藏 — 點擊展開）"
            )
            groups_html = f'<div class="uncat-grid">{_render_uncat_cards(uncataloged)}</div>'

        uncat_html = (
            '<details class="uncataloged-drawer">'
            f"<summary>{summary_text}</summary>"
            '<p class="uncat-note">以下圖示存在於樣式檔 MOI_OSM.xml（含其他風格專用或尺寸變體），尚未設定於 catalog.toml；僅顯示於網頁版供維護參考，不列入 PDF。</p>'
            f"{groups_html}"
            "</details>"
        )

    # Mapsforge vs PMTiles automatic diff drawer (web only, collapsed by default)
    diff_html = ""
    if pmtiles_diffs:
        default_or_partial = [d for d in pmtiles_diffs if d.diff_kind in ("default_missing", "partial")]
        overlay_missing = [d for d in pmtiles_diffs if d.diff_kind == "overlay_missing"]
        uncat_missing = [d for d in pmtiles_diffs if d.diff_kind == "uncataloged_missing"]

        def _render_diff_cards(items: list[PmtilesDiffItem], show_tile_badge: bool = True) -> str:
            out: list[str] = []
            for d in items:
                tile_badge = ""
                if show_tile_badge:
                    if d.exported_in_tiles:
                        tile_badge = '<span class="meta-badge badge-tile-yes">圖磚有資料</span>'
                    else:
                        tile_badge = '<span class="meta-badge badge-tile-no">process.lua 未匯出</span>'
                swatch_cls = "uncat-swatch" if d.diff_kind == "uncataloged_missing" else f"dense-swatch dense-swatch-{d.geom}"
                out.append(
                    '<div class="uncat-card">'
                    f'<div class="{swatch_cls}">{d.svg}</div>'
                    '<div class="uncat-body">'
                    f'<div class="uncat-name">{html.escape(d.name)}</div>'
                    f'<div class="diff-reason">{html.escape(d.reason)}</div>'
                    f'<div class="item-meta">{tile_badge}</div>'
                    f'<div class="item-tags"><code>{html.escape(d.tags_text)}</code></div>'
                    "</div>"
                    "</div>"
                )
            return "".join(out)

        diff_parts: list[str] = []
        if default_or_partial:
            diff_parts.append(
                f'<div class="uncat-group-head uncat-head-yes">'
                f"A. Mapsforge 預設顯示，但 PMTiles 未繪製或少畫部分符號（{len(default_or_partial)} 項）</div>"
                f'<div class="uncat-grid">{_render_diff_cards(default_or_partial)}</div>'
            )
        if overlay_missing:
            by_ov: dict[str, list[PmtilesDiffItem]] = {}
            for d in overlay_missing:
                by_ov.setdefault(d.overlay_group or "其他圖層", []).append(d)
            ov_blocks: list[str] = []
            for ov_name, ov_items in by_ov.items():
                n_yes = sum(1 for x in ov_items if x.exported_in_tiles)
                n_no = len(ov_items) - n_yes
                stat = f"圖磚有資料 {n_yes} ／ 未匯出 {n_no}"
                ov_blocks.append(
                    f'<div class="diff-overlay-sub">{html.escape(ov_name)}（{len(ov_items)} 項：{stat}）</div>'
                    f'<div class="uncat-grid">{_render_diff_cards(ov_items)}</div>'
                )
            diff_parts.append(
                f'<div class="uncat-group-head uncat-head-no">'
                f"B. Mapsforge 預設關閉圖層，PMTiles style.json 未收錄（{len(overlay_missing)} 項）</div>"
                '<p class="uncat-note">註：「標石（基點）」雖為 Mapsforge 預設關閉圖層，但 PMTiles style.json 已完整收錄並支援開關，故不在差異清單內。</p>'
                + "".join(ov_blocks)
            )
        if uncat_missing:
            diff_parts.append(
                f'<div class="uncat-group-head uncat-head-no">'
                f"C. 未收錄於 catalog 的 MOI_OSM.xml 資源在 PMTiles 未繪製（{len(uncat_missing)} 項）</div>"
                f'<div class="uncat-grid">{_render_diff_cards(uncat_missing, show_tile_badge=False)}</div>'
            )

        diff_summary = (
            f"Mapsforge 離線圖 vs PMTiles 線上圖磚差異清單"
            f"（共 {len(pmtiles_diffs)} 項：預設樣式差異 {len(default_or_partial)} ／ 關閉圖層未收錄 {len(overlay_missing)} ／ 未分類資源 {len(uncat_missing)}，預設收合 — 點擊展開）"
        )
        diff_html = (
            '<details class="uncataloged-drawer diff-drawer">'
            f"<summary>{diff_summary}</summary>"
            '<p class="uncat-note">'
            "由程式自動比對 <code>MOI_OSM.xml</code>（Mapsforge 登山風格）、<code>styles/pmtiles_style/style.json</code> 與 <code>osm_scripts/pmtiles/process.lua</code> 產生，僅顯示於網頁版，不列入 PDF。"
            "<br>共通引擎差異：Mapsforge 以 256px 圖磚為基準、MapLibre PMTiles 以 512px 為基準（同比例尺縮放級別差 1 級）；PMTiles 未畫圖示的次要 POI 會透過 <code>poi-other</code> 以純灰字顯示。"
            "</p>"
            f'{"".join(diff_parts)}'
            "</details>"
        )

    return (
        template.replace("{{VERSION}}", html.escape(version))
        .replace("{{TOTAL}}", str(len(entries)))
        .replace("{{COMPACT_COUNT}}", str(sum(1 for e in entries if e.compact)))
        .replace("{{CAT_NAV}}", cat_nav)
        .replace("{{COLOR_PILLS}}", color_pills)
        .replace("{{SHAPE_PILLS}}", shape_pills)
        .replace("{{SECTIONS}}", "".join(sections_html))
        .replace("{{PMTILES_DIFF_HTML}}", diff_html)
        .replace("{{UNCATALOGED_HTML}}", uncat_html)
    )


def render_pdf_detail_html(
    template: str,
    categories: list[dict[str, Any]],
    entries: list[LegendEntry],
    version: str,
    samples_dir: Path | None,
) -> str:
    by_cat: dict[str, list[LegendEntry]] = {c["id"]: [] for c in categories}
    for e in entries:
        by_cat.setdefault(e.category, []).append(e)

    sections: list[str] = []
    for idx, cat in enumerate(categories, start=1):
        cat_entries = by_cat.get(cat["id"], [])
        if not cat_entries:
            continue
        normal_rows: list[str] = []
        dense_cards: list[str] = []
        for e in cat_entries:
            ov_html, _ = _overlay_badges_html(e)
            tag_str = _format_tags(e.tags)

            if e.dense:
                dense_cards.append(
                    '<div class="pdf-dense-card">'
                    f'<div class="pdf-dense-swatch pdf-dense-swatch-{e.geom}">{e.svg_compact}</div>'
                    '<div class="pdf-dense-body">'
                    f'<div class="pdf-dense-title">{html.escape(e.name)}</div>'
                    f'<div class="pdf-dense-desc">{html.escape(e.desc)}</div>'
                    f'<div class="row-meta"><span class="meta-badge">z{e.zoom_min}+</span>{ov_html}</div>'
                    "</div>"
                    "</div>"
                )
                continue

            sample_cell = '<span class="no-sample">—</span>'
            if e.example and samples_dir:
                sample_file = samples_dir / f"{e.id}.png"
                if sample_file.is_file():
                    uri = _file_data_uri(sample_file)
                    place = e.example.get("place", "")
                    sample_cell = (
                        f'<div class="pdf-sample">'
                        f'<img src="{uri}" alt="{html.escape(place, quote=True)}">'
                        f'<div class="pdf-sample-cap">{html.escape(place)}</div>'
                        "</div>"
                    )
                else:
                    place = e.example.get("place", "")
                    if place:
                        sample_cell = f'<span class="no-sample">{html.escape(place)}</span>'

            normal_rows.append(
                "<tr>"
                '<td class="col-name">'
                f'<div class="row-title">{html.escape(e.name)}</div>'
                f'<div class="row-desc">{html.escape(e.desc)}</div>'
                f'<div class="row-meta"><span class="meta-badge">z{e.zoom_min}+</span>{ov_html}'
                f'<code class="row-tag">{html.escape(tag_str)}</code></div>'
                "</td>"
                f'<td class="col-svg">{e.svg_detail}</td>'
                f'<td class="col-sample">{sample_cell}</td>'
                "</tr>"
            )

        body_html = ""
        if normal_rows:
            body_html += (
                '<table class="legend-table">'
                '<colgroup><col class="col-name"><col class="col-svg"><col class="col-sample"></colgroup>'
                '<thead><tr><th class="col-name">名稱與說明</th>'
                '<th class="col-svg">簡化圖示</th>'
                '<th class="col-sample">真實地圖範例</th></tr></thead>'
                f'<tbody>{"".join(normal_rows)}</tbody>'
                "</table>"
            )
        if dense_cards:
            sub = '<div class="pdf-dense-subhead">次要／進階符號</div>' if normal_rows else ""
            body_html += f'{sub}<div class="pdf-dense-grid">{"".join(dense_cards)}</div>'

        sections.append(
            '<section class="pdf-section">'
            f'<h2>{idx}. {html.escape(cat["name"])}</h2>'
            f'<p class="sec-desc">{html.escape(cat.get("desc", ""))}</p>'
            f"{body_html}"
            "</section>"
        )

    return (
        template.replace("{{VERSION}}", html.escape(version))
        .replace("{{TOTAL}}", str(len(entries)))
        .replace("{{SECTIONS}}", "".join(sections))
    )


def render_pdf_compact_html(
    template: str,
    categories: list[dict[str, Any]],
    entries: list[LegendEntry],
    version: str,
) -> str:
    compact_entries = [e for e in entries if e.compact]
    by_cat: dict[str, list[LegendEntry]] = {c["id"]: [] for c in categories}
    for e in compact_entries:
        by_cat.setdefault(e.category, []).append(e)

    # Split cleanly into 2 balanced pages:
    # Page 1: trails, terrain, landcover, borders (linear/area & mountain core)
    # Page 2: peaks, shelters, emergency, roads, barriers, amenities (POIs & roads)
    page1_cats = {"trails", "terrain", "landcover", "borders"}

    def render_page_groups(cat_filter: set[str], include: bool) -> str:
        blocks: list[str] = []
        for cat in categories:
            if (cat["id"] in cat_filter) != include:
                continue
            items = by_cat.get(cat["id"], [])
            if not items:
                continue
            rows = []
            for e in items:
                off_ovs = [ov.name_zh for ov in e.overlays if not ov.enabled_default]
                note_html = (
                    f'<span class="c-note">需開啟：{html.escape(off_ovs[0])}</span>'
                    if off_ovs
                    else ""
                )
                short_name = e.name
                # Concise 1-line hint from desc
                short_desc = e.desc.split("。")[0].strip()
                rows.append(
                    '<div class="c-item">'
                    f'<div class="c-swatch c-swatch-{e.geom}">{e.svg_compact}</div>'
                    '<div class="c-text">'
                    f'<div class="c-name">{html.escape(short_name)}{note_html}</div>'
                    f'<div class="c-desc">{html.escape(short_desc)}</div>'
                    "</div>"
                    "</div>"
                )
            blocks.append(
                '<div class="c-group">'
                f'<h2 class="c-group-title">{html.escape(cat["name"])}</h2>'
                f'<div class="c-grid">{"".join(rows)}</div>'
                "</div>"
            )
        return "".join(blocks)

    return (
        template.replace("{{VERSION}}", html.escape(version))
        .replace("{{COUNT}}", str(len(compact_entries)))
        .replace("{{PAGE1}}", render_page_groups(page1_cats, include=True))
        .replace("{{PAGE2}}", render_page_groups(page1_cats, include=False))
    )


def render_pdf_onepage_html(
    template: str,
    categories: list[dict[str, Any]],
    entries: list[LegendEntry],
    version: str,
) -> str:
    """Render an ultra-compact 1-page A4 sheet (swatch + short name only, no descriptions)."""
    compact_entries = [e for e in entries if e.compact]
    by_cat: dict[str, list[LegendEntry]] = {}
    for e in compact_entries:
        by_cat.setdefault(e.category, []).append(e)

    blocks: list[str] = []
    for cat in categories:
        items = by_cat.get(cat["id"], [])
        if not items:
            continue
        rows = []
        for e in items:
            off_ovs = [ov.name_zh for ov in e.overlays if not ov.enabled_default]
            note_html = (
                f'<span class="o-note">開：{html.escape(off_ovs[0])}</span>'
                if off_ovs
                else ""
            )
            rows.append(
                '<div class="o-item">'
                f'<div class="o-swatch o-swatch-{e.geom}">{e.svg_compact}</div>'
                f'<div class="o-text"><div class="o-name">{html.escape(e.name)}{note_html}</div></div>'
                "</div>"
            )
        grid_cls = "o-grid o-grid-5" if (all(e.geom == "point" for e in items) and len(items) >= 5) else "o-grid"
        blocks.append(
            '<div class="o-group">'
            f'<h2 class="o-group-title">{html.escape(cat["name"])}</h2>'
            f'<div class="{grid_cls}">{"".join(rows)}</div>'
            "</div>"
        )

    return (
        template.replace("{{VERSION}}", html.escape(version))
        .replace("{{COUNT}}", str(len(compact_entries)))
        .replace("{{BODY}}", "".join(blocks))
    )


def print_html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise RuntimeError("Neither google-chrome nor chromium found in PATH for PDF generation")
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_path.resolve().as_uri(),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Build RudyMap legend web page and PDFs from MOI_OSM.xml.")
    parser.add_argument("--catalog", type=Path, default=Path("docs/legend/catalog.toml"))
    parser.add_argument("--theme", type=Path, default=Path("styles/mapsforge_style/MOI_OSM.xml"))
    parser.add_argument("--res-dir", type=Path, default=Path("styles/mapsforge_style/moiosm_res"))
    parser.add_argument("--templates-dir", type=Path, default=Path("docs/legend"))
    parser.add_argument("--samples-dir", type=Path, default=Path("download/legend_samples"))
    parser.add_argument(
        "--pmtiles",
        type=Path,
        default=None,
        help="Optional local PMTiles to classify uncataloged icons by Taiwan occurrence",
    )
    parser.add_argument("--pmtiles-style", type=Path, default=Path("styles/pmtiles_style/style.json"))
    parser.add_argument("--process-lua", type=Path, default=Path("osm_scripts/pmtiles/process.lua"))
    parser.add_argument("--tag-mapping", type=Path, default=Path("osm_scripts/tag-mapping.xml"))
    parser.add_argument("--out-dir", type=Path, default=Path("build"))
    parser.add_argument("--version", default="dev")
    parser.add_argument("--no-pdf", action="store_true", help="Skip generating PDF files")
    parser.add_argument("--check-coverage", action="store_true", help="Report MOI_OSM.xml rule coverage")
    parser.add_argument("--dump-meta", type=Path, help="Optional JSON path to dump evaluated legend metadata")
    args = parser.parse_args()

    categories, entries, covered_srcs, all_theme_srcs, uncataloged = build_entries(
        args.catalog, args.theme, args.res_dir
    )

    # Classify uncataloged icons into (A) present in Taiwan vs (B) absent in Taiwan
    pmtiles_path = args.pmtiles
    if pmtiles_path is None:
        for cand in (
            Path("build-taiwan/MOI_OSM_Taiwan_TOPO_Rudy.pmtiles"),
            Path("build/MOI_OSM_Taiwan_TOPO_Rudy.pmtiles"),
            Path("download/MOI_OSM_Taiwan_TOPO_Rudy.pmtiles"),
        ):
            if cand.is_file():
                pmtiles_path = cand
                break

    counts_cache = args.samples_dir / "uncataloged_taiwan_counts.json"
    tw_counts: dict[str, int] = {}
    if uncataloged:
        if pmtiles_path and pmtiles_path.is_file():
            tw_counts = count_uncataloged_in_pmtiles(pmtiles_path, uncataloged)
            args.samples_dir.mkdir(parents=True, exist_ok=True)
            counts_cache.write_text(
                json.dumps(tw_counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        elif counts_cache.is_file():
            cached = json.loads(counts_cache.read_text(encoding="utf-8"))
            if isinstance(cached, dict):
                tw_counts = {str(k): int(v) for k, v in cached.items()}

        for u in uncataloged:
            if u.src in tw_counts:
                u.taiwan_count = tw_counts[u.src]

    # Parse process.lua + tag-mapping.xml to automatically determine PMTiles export coverage
    export_spec = parse_pmtiles_export_spec(args.process_lua, args.tag_mapping)

    # Count catalog entries in Taiwan PMTiles so web legend can badge 0-occurrence items
    cat_counts_cache = args.samples_dir / "catalog_taiwan_counts.json"
    cat_tw_counts: dict[str, int] = {}
    if pmtiles_path and pmtiles_path.is_file():
        cat_tw_counts = count_catalog_in_pmtiles(pmtiles_path, entries, export_spec)
        args.samples_dir.mkdir(parents=True, exist_ok=True)
        cat_counts_cache.write_text(
            json.dumps(cat_tw_counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    elif cat_counts_cache.is_file():
        cached_cat = json.loads(cat_counts_cache.read_text(encoding="utf-8"))
        if isinstance(cached_cat, dict):
            cat_tw_counts = {str(k): int(v) for k, v in cached_cat.items()}

    for e in entries:
        if export_spec is not None and not export_spec.is_exported(e.geom, e.tags):
            e.taiwan_count = None
        elif args.samples_dir.is_dir() and (args.samples_dir / f"{e.id}.png").is_file():
            e.taiwan_count = max(1, cat_tw_counts.get(e.id, 1))
        elif e.id in cat_tw_counts:
            e.taiwan_count = cat_tw_counts[e.id]

    pmtiles_diffs = compute_mapsforge_pmtiles_diffs(
        args.theme, args.pmtiles_style, entries, uncataloged, export_spec
    )

    unmatched = [e.id for e in entries if e.matched_count == 0]
    if unmatched:
        print(f"WARNING: {len(unmatched)} catalog entries matched 0 MOI_OSM.xml rules: {unmatched}", file=sys.stderr)

    if args.check_coverage:
        missing_srcs = sorted(all_theme_srcs - covered_srcs)
        print(
            f"Catalog entries: {len(entries)} "
            f"(compact: {sum(1 for e in entries if e.compact)}, dense: {sum(1 for e in entries if e.dense)})"
        )
        print(f"Non-GPX theme resources covered: {len(covered_srcs)} / {len(all_theme_srcs)}")
        if missing_srcs:
            in_tw = [f"{u.src}({u.taiwan_count})" for u in uncataloged if (u.taiwan_count or 0) > 0]
            not_tw = [u.src for u in uncataloged if u.taiwan_count == 0]
            if in_tw or not_tw:
                print(f"Uncovered IN Taiwan ({len(in_tw)}): {', '.join(in_tw)}")
                print(f"Uncovered NOT in Taiwan ({len(not_tw)}): {', '.join(not_tw)}")
            else:
                print(f"Uncovered resources ({len(missing_srcs)}): {', '.join(missing_srcs)}")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # Copy captured real-map thumbnails next to legend.html if available
    samples_dir = args.samples_dir if args.samples_dir.is_dir() else None
    out_samples_rel = "legend_samples"
    if samples_dir:
        dst_samples = args.out_dir / out_samples_rel
        dst_samples.mkdir(parents=True, exist_ok=True)
        for png in samples_dir.glob("*.png"):
            shutil.copy2(png, dst_samples / png.name)

    docs_dir = args.templates_dir.resolve().parent

    def _load_tpl(name: str) -> str:
        raw = (args.templates_dir / name).read_text(encoding="utf-8")
        return template_assets.expand_template_assets(raw, docs_dir)

    # 1. Interactive web legend
    web_tpl = _load_tpl("template_web.html")
    web_html = render_web_html(
        web_tpl, categories, entries, uncataloged, pmtiles_diffs, args.version, samples_dir, out_samples_rel
    )
    web_out = args.out_dir / "legend.html"
    web_out.write_text(web_html, encoding="utf-8")
    print(f"Wrote {web_out} ({len(web_html) // 1024} KB)")

    # 2. Detail PDF & Compact PDF
    detail_tpl = _load_tpl("template_pdf_detail.html")
    detail_html = render_pdf_detail_html(detail_tpl, categories, entries, args.version, samples_dir)
    detail_html_out = args.out_dir / "legend_detail.html"
    detail_html_out.write_text(detail_html, encoding="utf-8")

    compact_tpl = _load_tpl("template_pdf_compact.html")
    compact_html = render_pdf_compact_html(compact_tpl, categories, entries, args.version)
    compact_html_out = args.out_dir / "legend_compact.html"
    compact_html_out.write_text(compact_html, encoding="utf-8")

    onepage_tpl = _load_tpl("template_pdf_onepage.html")
    onepage_html = render_pdf_onepage_html(onepage_tpl, categories, entries, args.version)
    onepage_html_out = args.out_dir / "legend_onepage.html"
    onepage_html_out.write_text(onepage_html, encoding="utf-8")

    if not args.no_pdf:
        detail_pdf = args.out_dir / "legend_detail.pdf"
        compact_pdf = args.out_dir / "legend_compact.pdf"
        onepage_pdf = args.out_dir / "legend_onepage.pdf"
        print_html_to_pdf(detail_html_out, detail_pdf)
        print_html_to_pdf(compact_html_out, compact_pdf)
        print_html_to_pdf(onepage_html_out, onepage_pdf)
        print(f"Wrote {detail_pdf} ({detail_pdf.stat().st_size // 1024} KB)")
        print(f"Wrote {compact_pdf} ({compact_pdf.stat().st_size // 1024} KB)")
        print(f"Wrote {onepage_pdf} ({onepage_pdf.stat().st_size // 1024} KB)")

    if args.dump_meta:
        meta = [
            {
                "id": e.id,
                "name": e.name,
                "category": e.category,
                "geom": e.geom,
                "colors": e.colors,
                "shapes": e.shapes,
                "zoom_min": e.zoom_min,
                "overlays": [{"cat": o.cat, "name": o.name_zh, "enabled": o.enabled_default} for o in e.overlays],
                "matched_count": e.matched_count,
                "example": e.example,
            }
            for e in entries
        ]
        args.dump_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
