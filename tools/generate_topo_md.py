#!/usr/bin/env python3
"""Scaffold documentation files for a new TOPO map region.

Creates three concise files under ``docs/<Region>/``:
- ``region.toml``: structured metadata (title, group, bounds, elevation, HGT list)
- ``guide.md``: Traditional Chinese prose sections (peaks, routes, sights, history)
- ``guide-en.md``: English prose sections

At build time, ``tools/render_topo_html.py`` + ``tools/region_doc.py`` combine
``region.toml``, ``guide*.md``, and ``docs/shared/site.toml`` into the full
responsive HTML pages (and automatically list the new region on the Taiwan
main page).

Usage:
    python3 tools/generate_topo_md.py \\
        --region Everest \\
        --region-lower everest \\
        --title "Everest Region Climbing Map" \\
        --group south_asia \\
        --lat "N27.50 ~ N28.20" \\
        --lon "E86.40 ~ E87.20" \\
        --hgt-files "N27E086, N28E086"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

GUIDE_ZH_TEMPLATE = """\
### 著名的山頭 (Famous Peaks)

### 著名的健行路線 (Famous Trekking Routes)

### 著名景點

### 歷史事件
"""

GUIDE_ZH_CITY_TEMPLATE = """\
### 著名徒步散步的路線

### 著名景點

### 歷史事件
"""

GUIDE_EN_TEMPLATE = """\
### Famous Peaks

### Famous Trekking Routes

### Famous Sights

### Historical Events
"""

GUIDE_EN_CITY_TEMPLATE = """\
### Famous Walking Routes

### Famous Sights

### Historical Events
"""


def _toml_str(val: str) -> str:
    return json.dumps(val, ensure_ascii=False)


def build_region_toml(
    *,
    region: str,
    suite: str,
    title: str,
    group: str,
    order: int,
    elevation: bool,
    hgt_files: str,
) -> str:
    """Format a new region.toml file (build facts come from suites/<suite>/<suite>.mk)."""
    guide_kind = "region" if elevation else "city"
    lines = [
        f"suite = {_toml_str(suite)}",
        f"group = {_toml_str(group)}",
        f"order = {order}",
        f"guide_kind = {_toml_str(guide_kind)}",
        "ai_notice = true",
    ]
    if elevation and hgt_files:
        lines.append(f"hgt_files = {_toml_str(hgt_files)}")
    lines += [
        "",
        "[zh]",
        f"title = {_toml_str(title)}",
        f"garmin_name = {_toml_str(f'{region} Region')}",
        f"index_label = {_toml_str(region)}",
        "",
        "[en]",
        f"title = {_toml_str(title)}",
        f"garmin_name = {_toml_str(f'{region} Region')}",
        f"index_label = {_toml_str(region)}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    """Scaffold region.toml, guide.md, and guide-en.md for a new TOPO map region."""
    parser = argparse.ArgumentParser(
        description="Scaffold region.toml, guide.md, and guide-en.md for a new TOPO map region."
    )
    parser.add_argument("--region", required=True, help="Region name (e.g., Everest)")
    parser.add_argument("--region-lower", required=True, help="Region suite identifier (e.g., everest)")
    parser.add_argument("--title", required=True, help="Full title for documentation")
    parser.add_argument("--lang", default=None, help=argparse.SUPPRESS)
    parser.add_argument(
        "--group",
        default="other",
        help="Region group ID from docs/shared/site.toml (e.g., japan, hk_kr, south_asia, europe_alps, russia)",
    )
    parser.add_argument("--order", default=90, type=int, help="Sort order within the group on the Taiwan main page")
    parser.add_argument("--lat", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--lon", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--hgt-files", default="", help=argparse.SUPPRESS)
    parser.add_argument(
        "--no-elevation",
        action="store_true",
        help="Region without contours/HGT (selects city guide headings; elevation flag comes from suites/*.mk)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview files without writing them")
    args = parser.parse_args()

    elevation = not args.no_elevation
    toml_content = build_region_toml(
        region=args.region,
        suite=args.region_lower,
        title=args.title,
        group=args.group,
        order=args.order,
        elevation=elevation,
        hgt_files=args.hgt_files,
    )
    guide_zh = GUIDE_ZH_TEMPLATE if elevation else GUIDE_ZH_CITY_TEMPLATE
    guide_en = GUIDE_EN_TEMPLATE if elevation else GUIDE_EN_CITY_TEMPLATE

    doc_dir = Path("docs") / args.region
    files = [
        (doc_dir / "region.toml", toml_content),
        (doc_dir / "guide.md", guide_zh),
        (doc_dir / "guide-en.md", guide_en),
    ]

    print(f"\n{'=' * 70}")
    print(f"Scaffolding Documentation: {args.region} ({args.region_lower})")
    print(f"{'=' * 70}\n")
    for path, content in files:
        print(f"  ✓ {path} ({len(content.splitlines())} lines)")

    if not args.dry_run:
        doc_dir.mkdir(parents=True, exist_ok=True)
        for path, content in files:
            path.write_text(content, encoding="utf-8")
        print("\n✓ Documentation scaffold created!")
        print(f"  1. Review titles/index_label/lat/lon in {doc_dir / 'region.toml'}")
        print(f"  2. Fill in prose sections in {doc_dir / 'guide.md'} and {doc_dir / 'guide-en.md'}")
        print("  3. The Taiwan main page automatically lists this region from region.toml.")
    else:
        print("\n✓ Dry run completed - no files were created")
        print("\n--- region.toml preview ---")
        print(toml_content)

    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
