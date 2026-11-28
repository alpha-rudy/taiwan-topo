#!/usr/bin/env python3
"""Render TOPO Markdown documentation into a modern, self-contained HTML page.

Zero external dependencies (Python 3 standard library only). Supports the
Markdown conventions used in docs/*/*_topo*.md and docs/Taiwan/beta.md
(including Discount's `=36x` / `=x36` image width/height syntax, autolinks,
nested lists with blockquotes, and `[[自動分流]](url)` download links).
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region_doc
import template_assets

# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------


@dataclass
class Heading:
    level: int
    raw: str


@dataclass
class Paragraph:
    lines: list[str]


@dataclass
class CodeBlock:
    lines: list[str]


@dataclass
class Blockquote:
    children: list[Block]


@dataclass
class ListItem:
    text: str
    children: list[Block] = field(default_factory=list)


@dataclass
class BulletList:
    ordered: bool
    items: list[ListItem]


Block = Heading | Paragraph | CodeBlock | Blockquote | BulletList


# ---------------------------------------------------------------------------
# Markdown block parser
# ---------------------------------------------------------------------------

_ATX_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
_SETEXT_H1_RE = re.compile(r"^={3,}\s*$")
_SETEXT_H2_RE = re.compile(r"^-{3,}\s*$")
_LIST_ITEM_RE = re.compile(r"^(\s*)([*\-]|\d+\.)\s+(.*)$")
_BQ_RE = re.compile(r"^(\s*)>\s?(.*)$")
_FENCE_RE = re.compile(r"^```")


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_blocks(lines: list[str], allow_indented_code: bool = True) -> list[Block]:
    """Parse Markdown lines into a list of Block AST nodes."""
    blocks: list[Block] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Fenced code block
        if _FENCE_RE.match(stripped):
            i += 1
            code_lines: list[str] = []
            while i < n and not _FENCE_RE.match(lines[i].strip()):
                code_lines.append(lines[i])
                i += 1
            if i < n:
                i += 1
            blocks.append(CodeBlock(code_lines))
            continue

        # Indented code block (4+ spaces at top level, not starting a list/bq)
        if allow_indented_code and line.startswith("    "):
            code_lines = []
            while i < n:
                cur = lines[i]
                if not cur.strip():
                    code_lines.append("")
                    i += 1
                elif cur.startswith("    "):
                    code_lines.append(cur[4:])
                    i += 1
                else:
                    break
            while code_lines and not code_lines[-1]:
                code_lines.pop()
            blocks.append(CodeBlock(code_lines))
            continue

        # ATX heading
        atx = _ATX_RE.match(stripped)
        if atx and _indent_of(line) == 0:
            blocks.append(Heading(len(atx.group(1)), atx.group(2).strip()))
            i += 1
            continue

        # Setext heading
        if _indent_of(line) == 0 and i + 1 < n:
            nxt = lines[i + 1]
            if _SETEXT_H1_RE.match(nxt):
                blocks.append(Heading(1, stripped))
                i += 2
                continue
            if _SETEXT_H2_RE.match(nxt):
                blocks.append(Heading(2, stripped))
                i += 2
                continue

        # Blockquote
        bq = _BQ_RE.match(line)
        if bq:
            bq_indent = len(bq.group(1))
            bq_lines: list[str] = []
            while i < n:
                m = _BQ_RE.match(lines[i])
                if m and len(m.group(1)) >= bq_indent:
                    bq_lines.append(m.group(2))
                    i += 1
                else:
                    break
            blocks.append(Blockquote(parse_blocks(bq_lines, allow_indented_code=False)))
            continue

        # List
        li = _LIST_ITEM_RE.match(line)
        if li:
            list_block, i = _parse_list(lines, i)
            blocks.append(list_block)
            continue

        # Paragraph
        para_lines: list[str] = []
        while i < n:
            cur = lines[i]
            cur_s = cur.strip()
            if not cur_s:
                break
            if _indent_of(cur) == 0 and (
                _ATX_RE.match(cur_s)
                or _LIST_ITEM_RE.match(cur)
                or _BQ_RE.match(cur)
                or _FENCE_RE.match(cur_s)
            ):
                break
            if (
                _indent_of(cur) == 0
                and i + 1 < n
                and (_SETEXT_H1_RE.match(lines[i + 1]) or _SETEXT_H2_RE.match(lines[i + 1]))
            ):
                break
            para_lines.append(cur_s)
            i += 1
        blocks.append(Paragraph(para_lines))

    return blocks


def _parse_list(lines: list[str], start: int) -> tuple[BulletList, int]:
    first = _LIST_ITEM_RE.match(lines[start])
    assert first is not None
    base_indent = len(first.group(1))
    ordered = first.group(2).endswith(".")
    items: list[ListItem] = []
    i = start
    n = len(lines)

    while i < n:
        line = lines[i]
        if not line.strip():
            # Look ahead to see if the list continues at >= base_indent
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j >= n:
                break
            nxt_match = _LIST_ITEM_RE.match(lines[j])
            if nxt_match and len(nxt_match.group(1)) == base_indent:
                nxt_ordered = nxt_match.group(2).endswith(".")
                if nxt_ordered == ordered:
                    i = j
                    continue
            if _indent_of(lines[j]) > base_indent:
                i = j
                continue
            break

        m = _LIST_ITEM_RE.match(line)
        if not m or len(m.group(1)) != base_indent or m.group(2).endswith(".") != ordered:
            break

        item_text_parts = [m.group(3).strip()]
        i += 1

        # Collect indented child lines for this list item
        child_lines: list[str] = []
        while i < n:
            cur = lines[i]
            if not cur.strip():
                # Peek ahead: keep blank line only if more indented content follows
                j = i + 1
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and _indent_of(lines[j]) > base_indent:
                    child_lines.append("")
                    i += 1
                    continue
                break
            if _indent_of(cur) > base_indent:
                child_lines.append(cur)
                i += 1
            else:
                break

        # Separate leading plain continuation lines from structured child blocks
        structured_start = 0
        while structured_start < len(child_lines):
            cl = child_lines[structured_start]
            if not cl.strip():
                structured_start += 1
                continue
            if _LIST_ITEM_RE.match(cl) or _BQ_RE.match(cl):
                break
            item_text_parts.append(cl.strip())
            structured_start += 1

        children: list[Block] = []
        remaining = child_lines[structured_start:]
        if remaining:
            non_empty = [ln for ln in remaining if ln.strip()]
            if non_empty:
                min_ind = min(_indent_of(ln) for ln in non_empty)
                dedented = [ln[min_ind:] if len(ln) >= min_ind else "" for ln in remaining]
                children = parse_blocks(dedented, allow_indented_code=False)

        items.append(ListItem(" ".join(item_text_parts), children))

    return BulletList(ordered=ordered, items=items), i


# ---------------------------------------------------------------------------
# Inline Markdown renderer
# ---------------------------------------------------------------------------

_IMG_DIM_RE = re.compile(r"^(.*?)\s+=(\d*)x(\d*)$")
_AUTOLINK_RE = re.compile(r"https?://[^\s<>\"']+")
_TRAILING_PUNCT = ".,;:!?)]}）」，。、；："
_BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_CODE_SPAN_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def _find_matching_bracket(text: str, start: int) -> int:
    depth = 0
    for idx in range(start, len(text)):
        ch = text[idx]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return idx
    return -1


def _find_matching_paren(text: str, start: int) -> int:
    depth = 0
    for idx in range(start, len(text)):
        ch = text[idx]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return idx
    return -1


def _render_img_tag(alt: str, target: str) -> str:
    width_attr = ""
    height_attr = ""
    src = target.strip()
    m = _IMG_DIM_RE.match(src)
    if m:
        src = m.group(1).strip()
        if m.group(2):
            width_attr = f' width="{html.escape(m.group(2), quote=True)}"'
        if m.group(3):
            height_attr = f' height="{html.escape(m.group(3), quote=True)}"'
    return (
        f'<img src="{html.escape(src, quote=True)}" '
        f'alt="{html.escape(alt, quote=True)}"{width_attr}{height_attr} loading="lazy">'
    )


def render_inline(text: str) -> str:
    """Render inline Markdown (images, links, autolinks, bold, code, <br>)."""
    out: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        # <br /> or <br>
        if text[i] == "<":
            br = _BR_RE.match(text, i)
            if br:
                out.append("<br>")
                i = br.end()
                continue

        # Image: ![alt](src [=WxH])
        if text[i : i + 2] == "![":
            end_br = _find_matching_bracket(text, i + 1)
            if end_br != -1 and end_br + 1 < n and text[end_br + 1] == "(":
                end_p = _find_matching_paren(text, end_br + 1)
                if end_p != -1:
                    alt = text[i + 2 : end_br]
                    target = text[end_br + 2 : end_p]
                    out.append(_render_img_tag(alt, target))
                    i = end_p + 1
                    continue

        # Link: [label](url) (supports nested brackets like [[自動分流]](url))
        if text[i] == "[":
            end_br = _find_matching_bracket(text, i)
            if end_br != -1 and end_br + 1 < n and text[end_br + 1] == "(":
                end_p = _find_matching_paren(text, end_br + 1)
                if end_p != -1:
                    label = text[i + 1 : end_br]
                    url = text[end_br + 2 : end_p].strip()
                    label_html = render_inline(label)
                    extra = ' target="_blank" rel="noopener"' if url.startswith(("http://", "https://")) else ""
                    out.append(f'<a href="{html.escape(url, quote=True)}"{extra}>{label_html}</a>')
                    i = end_p + 1
                    continue

        # Inline code
        if text[i] == "`":
            cm = _CODE_SPAN_RE.match(text, i)
            if cm:
                out.append(f"<code>{html.escape(cm.group(1))}</code>")
                i = cm.end()
                continue

        # Bold
        if text[i : i + 2] == "**":
            bm = _BOLD_RE.match(text, i)
            if bm:
                out.append(f"<strong>{render_inline(bm.group(1))}</strong>")
                i = bm.end()
                continue

        # Autolink
        if text[i : i + 7] == "http://" or text[i : i + 8] == "https://":
            am = _AUTOLINK_RE.match(text, i)
            if am:
                raw_url = am.group(0)
                trimmed = raw_url
                while trimmed and trimmed[-1] in _TRAILING_PUNCT:
                    if trimmed[-1] == ")" and trimmed.count("(") >= trimmed.count(")"):
                        break
                    trimmed = trimmed[:-1]
                esc_url = html.escape(trimmed, quote=True)
                out.append(f'<a href="{esc_url}" target="_blank" rel="noopener">{html.escape(trimmed)}</a>')
                i += len(trimmed)
                continue

        out.append(html.escape(text[i]))
        i += 1

    return "".join(out)


def strip_markdown_images(text: str) -> str:
    """Remove Markdown image tags and return plain label text."""
    return re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text).strip()


def extract_leading_images(text: str) -> tuple[list[str], str]:
    """Split leading Markdown images from the remaining text."""
    imgs: list[str] = []
    rest = text.lstrip()
    while rest.startswith("!["):
        end_br = _find_matching_bracket(rest, 1)
        if end_br == -1 or end_br + 1 >= len(rest) or rest[end_br + 1] != "(":
            break
        end_p = _find_matching_paren(rest, end_br + 1)
        if end_p == -1:
            break
        alt = rest[2:end_br]
        target = rest[end_br + 2 : end_p]
        imgs.append(_render_img_tag(alt, target))
        rest = rest[end_p + 1 :].lstrip()
    return imgs, rest


# ---------------------------------------------------------------------------
# Semantic HTML builders
# ---------------------------------------------------------------------------

_DL_LINK_RE = re.compile(r"^\[(?:\[)?([^\]]+?)(?:\])?\]\(([^)]+)\)$")
_PASTE_URL_RE = re.compile(r"^(.+?)\s*[:：]\s*(https?://\S+)\s*$")
_COORD_ITEM_RE = re.compile(r"^(?:緯度範圍|經度範圍|Latitude range|Longitude range)\s*[:：]")
_SIZE_SUFFIX_RE = re.compile(r"^(.*?)\s*\(([^()]*?(?:MB|GB|KB))\)\s*$")
_VERSION_RE = re.compile(r"(v\d{4}\.\d{2}\.\d{2}|v__version__)")
_LFS_HEADER = "version https://git-lfs.github.com/spec/v1"
_LFS_SIZE_RE = re.compile(r"^size\s+(\d+)\s*$", re.MULTILINE)


def format_file_size(num_bytes: int) -> str:
    """Format a byte count into a compact badge string (e.g. 26KB, 5.4MB, 347MB, 1.2GB)."""
    if num_bytes < 1024:
        return f"{num_bytes}B"
    kb = num_bytes / 1024
    if round(kb) < 1024:
        return f"{round(kb)}KB"
    mb = kb / 1024
    if mb < 9.95:
        return f"{mb:.1f}MB"
    if round(mb) < 1024:
        return f"{round(mb)}MB"
    return f"{mb / 1024:.1f}GB"


def _file_byte_size(path: Path) -> int | None:
    """Return real file size in bytes, reading ``size`` from Git LFS pointers."""
    if not path.is_file():
        return None
    st_size = path.stat().st_size
    if st_size <= 0:
        return None
    if st_size < 512:
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return st_size
        if head.startswith(_LFS_HEADER):
            m = _LFS_SIZE_RE.search(head)
            if m:
                val = int(m.group(1))
                return val if val > 0 else None
    return st_size


def _url_filename(url: str) -> str:
    """Extract the trailing filename from an http(s) or custom-scheme download URL."""
    cleaned = url.strip()
    if not cleaned:
        return ""
    parsed = urlsplit(cleaned)
    raw_path = parsed.path or cleaned
    name = PurePosixPath(raw_path).name
    if not name or "." not in name:
        return ""
    return name


class FileSizeResolver:
    """Resolve download URLs to human-readable sizes from local build/asset directories."""

    def __init__(self, search_dirs: list[Path], locus_dir: Path | None = None) -> None:
        dedup: list[Path] = []
        seen_dirs: set[Path] = set()
        for d in search_dirs:
            resolved = d.resolve()
            if resolved not in seen_dirs and resolved.is_dir():
                seen_dirs.add(resolved)
                dedup.append(resolved)
        self._search_dirs = dedup
        self._xml_index: dict[str, Path] = {}
        if locus_dir is not None and locus_dir.is_dir():
            for xml_path in sorted(locus_dir.rglob("*.xml")):
                self._xml_index.setdefault(xml_path.name, xml_path)
        self._byte_cache: dict[str, int | None] = {}

    def _find_xml(self, fname: str) -> Path | None:
        for d in self._search_dirs:
            cand = d / fname
            if cand.is_file():
                return cand
        return self._xml_index.get(fname)

    def _resolve_filename_bytes(self, fname: str, seen: frozenset[str] = frozenset()) -> int | None:
        if fname in self._byte_cache:
            return self._byte_cache[fname]
        if fname in seen:
            return None

        result: int | None = None
        if fname.lower().endswith(".xml"):
            xml_path = self._find_xml(fname)
            if xml_path is not None:
                try:
                    root = ET.parse(xml_path).getroot()
                except (ET.ParseError, OSError):
                    root = None
                if root is not None:
                    sources = [
                        _url_filename(el.text or "")
                        for el in root.iter("source")
                        if el.text and el.text.strip()
                    ]
                    if sources:
                        total = 0
                        next_seen = seen | {fname}
                        all_found = True
                        for src_name in sources:
                            sz = self._resolve_filename_bytes(src_name, next_seen) if src_name else None
                            if sz is None:
                                all_found = False
                                break
                            total += sz
                        if all_found and total > 0:
                            result = total
        else:
            for d in self._search_dirs:
                sz = _file_byte_size(d / fname)
                if sz is not None:
                    result = sz
                    break

        self._byte_cache[fname] = result
        return result

    def resolve_url(self, url: str) -> str | None:
        fname = _url_filename(url)
        if not fname or fname.lower().endswith((".html", ".htm")):
            return None
        num_bytes = self._resolve_filename_bytes(fname)
        return format_file_size(num_bytes) if num_bytes is not None else None
_COPY_ICON_SVG = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>'
    '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>'
    "</svg>"
)
_DL_ICON_SVG = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>'
    '<polyline points="7 10 12 15 17 10"></polyline>'
    '<line x1="12" y1="15" x2="12" y2="3"></line>'
    "</svg>"
)


def _extract_download_link(children: list[Block]) -> tuple[str, str] | None:
    """If children is a single Blockquote with one download link, return (label, url)."""
    if len(children) != 1 or not isinstance(children[0], Blockquote):
        return None
    bq_children = children[0].children
    if len(bq_children) != 1 or not isinstance(bq_children[0], Paragraph):
        return None
    if len(bq_children[0].lines) != 1:
        return None
    raw = bq_children[0].lines[0].strip()
    m = _DL_LINK_RE.match(raw)
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()


def _has_download_items(blist: BulletList) -> bool:
    for item in blist.items:
        if _extract_download_link(item.children) is not None:
            return True
        for child in item.children:
            if isinstance(child, BulletList) and _has_download_items(child):
                return True
    return False


def _render_generic_block(block: Block) -> str:
    if isinstance(block, Heading):
        return f"<h{block.level}>{render_inline(block.raw)}</h{block.level}>"
    if isinstance(block, Paragraph):
        rendered_lines = [render_inline(ln) for ln in block.lines]
        buf: list[str] = []
        for idx, rln in enumerate(rendered_lines):
            buf.append(rln)
            if idx + 1 < len(rendered_lines) and not rln.rstrip().endswith("<br>"):
                buf.append("<br>")
        return f"<p>{''.join(buf)}</p>"
    if isinstance(block, CodeBlock):
        return f"<pre><code>{html.escape(chr(10).join(block.lines))}</code></pre>"
    if isinstance(block, Blockquote):
        inner = "".join(_render_generic_block(ch) for ch in block.children)
        return f"<blockquote>{inner}</blockquote>"
    tag = "ol" if block.ordered else "ul"
    parts = [f"<{tag}>"]
    for item in block.items:
        inner = "".join(_render_generic_block(ch) for ch in item.children)
        parts.append(f"<li>{render_inline(item.text)}{inner}</li>")
    parts.append(f"</{tag}>")
    return "".join(parts)


def _render_download_row(
    item: ListItem,
    label: str,
    url: str,
    is_en: bool,
    size_resolver: FileSizeResolver | None = None,
) -> str:
    imgs, rest_text = extract_leading_images(item.text)
    static_size = ""
    m_size = _SIZE_SUFFIX_RE.match(rest_text)
    if m_size:
        rest_text = m_size.group(1).strip()
        static_size = m_size.group(2)

    dyn_size = size_resolver.resolve_url(url) if size_resolver is not None else None
    badge_size = dyn_size if dyn_size is not None else static_size
    size_html = f'<span class="size-badge">{html.escape(badge_size)}</span>' if badge_size else ""

    icons_html = f'<span class="dl-icons">{"".join(imgs)}</span>' if imgs else ""
    esc_url = html.escape(url, quote=True)
    is_http = url.startswith(("http://", "https://"))
    btn_cls = "dl-btn dl-btn-secondary" if is_http else "dl-btn"
    target_attr = ' target="_blank" rel="noopener"' if is_http else ""

    copy_html = ""
    if is_http:
        copy_title = "Copy link" if is_en else "複製連結"
        copied_msg = "Link copied" if is_en else "已複製下載連結"
        copy_html = (
            f'<button type="button" class="copy-btn" data-url="{esc_url}" '
            f'data-copied="{copied_msg}" title="{copy_title}" aria-label="{copy_title}">'
            f"{_COPY_ICON_SVG}</button>"
        )

    return (
        '<div class="dl-row">'
        f'<div class="dl-info">{icons_html}'
        f'<div class="dl-text">{render_inline(rest_text)}{size_html}</div>'
        "</div>"
        f'<div class="dl-actions">'
        f'<a class="{btn_cls}" href="{esc_url}"{target_attr}>{_DL_ICON_SVG}{html.escape(label)}</a>'
        f"{copy_html}"
        "</div>"
        "</div>"
    )


def _flush_rows(parts: list[str], row_buf: list[str]) -> None:
    if row_buf:
        parts.append(f'<div class="dl-list">{"".join(row_buf)}</div>')
        row_buf.clear()


def _render_paste_url_row(
    label: str,
    url: str,
    is_en: bool,
    size_resolver: FileSizeResolver | None = None,
) -> str:
    esc_url = html.escape(url, quote=True)
    copy_title = "Copy link" if is_en else "複製連結"
    copied_msg = "Link copied" if is_en else "已複製下載連結"
    static_size = ""
    m_size = _SIZE_SUFFIX_RE.match(label)
    if m_size:
        label = m_size.group(1).strip()
        static_size = m_size.group(2)
    dyn_size = size_resolver.resolve_url(url) if size_resolver is not None else None
    badge_size = dyn_size if dyn_size is not None else static_size
    size_html = f'<span class="size-badge">{html.escape(badge_size)}</span>' if badge_size else ""
    return (
        '<div class="dl-row">'
        '<div class="dl-info"><div class="dl-text">'
        f"{render_inline(label)}{size_html}"
        f'<div class="dl-desc"><a href="{esc_url}" target="_blank" rel="noopener">{html.escape(url)}</a></div>'
        "</div></div>"
        '<div class="dl-actions">'
        f'<button type="button" class="copy-btn" data-url="{esc_url}" '
        f'data-copied="{copied_msg}" title="{copy_title}" aria-label="{copy_title}">'
        f"{_COPY_ICON_SVG}</button>"
        "</div>"
        "</div>"
    )


def _render_plain_list(block: BulletList) -> str:
    tag = "ol" if block.ordered else "ul"
    items_html: list[str] = []
    for item in block.items:
        inner = "".join(_render_generic_block(ch) for ch in item.children)
        items_html.append(f"<li>{render_inline(item.text)}{inner}</li>")
    return f'<{tag} class="plain-list">{"".join(items_html)}</{tag}>'


def _has_card_special_items(block: BulletList) -> bool:
    if _has_download_items(block):
        return True
    for item in block.items:
        if item.children and all(isinstance(ch, Blockquote) for ch in item.children):
            return True
        if not item.children and _PASTE_URL_RE.match(item.text.strip()):
            return True
    return False


def _render_card_body(
    blocks: list[Block],
    is_en: bool,
    size_resolver: FileSizeResolver | None = None,
) -> str:
    """Render content inside a download card (tips, grouped download rows, plain items)."""
    parts: list[str] = []
    for block in blocks:
        if not isinstance(block, BulletList):
            parts.append(_render_generic_block(block))
            continue

        if not _has_card_special_items(block):
            parts.append(_render_plain_list(block))
            continue

        row_buf: list[str] = []

        for item in block.items:
            dl = _extract_download_link(item.children)
            if dl is not None:
                row_buf.append(_render_download_row(item, dl[0], dl[1], is_en, size_resolver))
                continue

            if not item.children:
                pm = _PASTE_URL_RE.match(item.text.strip())
                if pm:
                    row_buf.append(
                        _render_paste_url_row(pm.group(1).strip(), pm.group(2).strip(), is_en, size_resolver)
                    )
                    continue

            # Sub-group containing download items (e.g., 傳統版 / 輕量版 / 疊圖專用 Styles)
            if (
                len(item.children) == 1
                and isinstance(item.children[0], BulletList)
                and _has_download_items(item.children[0])
            ):
                _flush_rows(parts, row_buf)
                group_body = _render_card_body([item.children[0]], is_en, size_resolver)
                parts.append(
                    '<div class="dl-group">'
                    f'<div class="dl-group-title">{render_inline(item.text)}</div>'
                    f"{group_body}"
                    "</div>"
                )
                continue

            # Tip / demo video / install guide item (text + blockquote without download link)
            if item.children and all(isinstance(ch, Blockquote) for ch in item.children):
                _flush_rows(parts, row_buf)
                bq_inner = "".join(
                    "".join(_render_generic_block(gch) for gch in ch.children)
                    for ch in item.children
                    if isinstance(ch, Blockquote)
                )
                # Distinguish extra-layer non-download item (has URL or "...") from pure tip
                if "http://" in item.text or "https://" in item.text or item.text.strip() == "...":
                    row_buf.append(
                        '<div class="dl-row">'
                        '<div class="dl-info"><div class="dl-text">'
                        f"{render_inline(item.text)}"
                        f'<div class="dl-desc">{bq_inner}</div>'
                        "</div></div></div>"
                    )
                else:
                    parts.append(
                        '<div class="card-tip">'
                        f"<p><strong>{render_inline(item.text)}</strong></p>"
                        f"{bq_inner}"
                        "</div>"
                    )
                continue

            # Generic list item fallback
            _flush_rows(parts, row_buf)
            inner = "".join(_render_generic_block(ch) for ch in item.children)
            parts.append(f'<ul class="plain-list"><li>{render_inline(item.text)}{inner}</li></ul>')

        _flush_rows(parts, row_buf)

    return "".join(parts)


def _render_links_section(blocks: list[Block]) -> str:
    parts: list[str] = []
    for block in blocks:
        if isinstance(block, BulletList):
            parts.append('<div class="links-grid">')
            for item in block.items:
                inner = "".join(_render_generic_block(ch) for ch in item.children)
                parts.append(f'<div class="link-item">{render_inline(item.text)}{inner}</div>')
            parts.append("</div>")
        else:
            parts.append(_render_generic_block(block))
    return "".join(parts)


def _render_region_card(item: ListItem, group_id: str, group_title: str) -> str:
    url = ""
    coords: list[str] = []
    extra_notes: list[str] = []

    if item.children and isinstance(item.children[0], BulletList):
        for sub in item.children[0].items:
            sub_s = sub.text.strip()
            if sub_s.startswith(("http://", "https://")):
                url = sub_s
            elif sub.children and isinstance(sub.children[0], BulletList):
                for coord_item in sub.children[0].items:
                    coords.append(coord_item.text.strip())
            else:
                extra_notes.append(sub_s)

    name_raw = item.text.strip()
    search_blob = f"{group_title} {name_raw} {' '.join(coords)}".strip().lower()
    if url:
        esc_url = html.escape(url, quote=True)
        name_html = (
            f'<a href="{esc_url}" target="_blank" rel="noopener">{render_inline(name_raw)} ↗</a>'
        )
    else:
        name_html = render_inline(name_raw)

    coords_html = ""
    if coords:
        pills = "".join(f'<span class="coord-pill">{html.escape(c)}</span>' for c in coords)
        coords_html = f'<div class="region-coords">{pills}</div>'

    extra_html = "".join(f'<div class="dl-desc">{render_inline(n)}</div>' for n in extra_notes)

    group_attr = f' data-group="{html.escape(group_id, quote=True)}"' if group_id else ""
    return (
        f'<div class="region-card" data-search="{html.escape(search_blob, quote=True)}"{group_attr}>'
        f'<div class="region-name">{name_html}</div>'
        f"{coords_html}{extra_html}"
        "</div>"
    )


def _render_regions_section(blocks: list[Block], is_en: bool) -> str:
    intro_parts: list[str] = []
    groups: list[tuple[str, str, list[str]]] = []
    ungrouped_cards: list[str] = []
    current_group: tuple[str, str, list[str]] | None = None

    for block in blocks:
        if isinstance(block, Heading) and block.level == 3:
            title = strip_markdown_images(block.raw)
            gid = f"rg-{len(groups) + 1}"
            current_group = (gid, title, [])
            groups.append(current_group)
        elif isinstance(block, BulletList):
            if current_group is not None:
                gid, gtitle, gcards = current_group
                for item in block.items:
                    gcards.append(_render_region_card(item, gid, gtitle))
            else:
                for item in block.items:
                    ungrouped_cards.append(_render_region_card(item, "", ""))
        else:
            intro_parts.append(_render_generic_block(block))

    total = len(ungrouped_cards) + sum(len(g[2]) for g in groups)
    placeholder = (
        "Filter overseas regions (e.g., Japan, Alps, Fuji)..."
        if is_en
        else "搜尋國外山區（例：日本、阿爾卑斯、富士山）..."
    )
    empty_msg = "No matching regions found." if is_en else "找不到符合條件的山區。"
    intro_html = f'<div class="section-notice">{"".join(intro_parts)}</div>' if intro_parts else ""

    filters_html = ""
    if groups:
        all_label = f"All ({total})" if is_en else f"全部 ({total})"
        pills = [
            f'<button type="button" class="filter-pill is-active" data-filter="all">{all_label}</button>'
        ]
        for gid, gtitle, gcards in groups:
            pills.append(
                f'<button type="button" class="filter-pill" data-filter="{html.escape(gid, quote=True)}">'
                f"{html.escape(gtitle)} ({len(gcards)})</button>"
            )
        filters_html = f'<div class="region-filters" role="group">{"".join(pills)}</div>'

    body_parts: list[str] = []
    if ungrouped_cards:
        body_parts.append(f'<div class="region-grid">{"".join(ungrouped_cards)}</div>')
    for gid, gtitle, gcards in groups:
        body_parts.append(
            f'<div class="region-group" data-group="{html.escape(gid, quote=True)}">'
            f'<h3 class="region-group-title">{html.escape(gtitle)}'
            f'<span class="size-badge">{len(gcards)}</span></h3>'
            f'<div class="region-grid">{"".join(gcards)}</div>'
            "</div>"
        )

    return (
        f"{intro_html}"
        '<div class="region-toolbar">'
        f'<input type="search" id="region-search" class="region-search" '
        f'placeholder="{placeholder}" aria-label="{placeholder}">'
        f'<span class="region-count" id="region-count">{total} / {total}</span>'
        "</div>"
        f"{filters_html}"
        f'{"".join(body_parts)}'
        f'<div class="region-empty" id="region-empty">{empty_msg}</div>'
    )


def _render_changelog_section(blocks: list[Block], is_en: bool, visible_count: int = 5) -> str:
    parts: list[str] = []
    for block in blocks:
        if not isinstance(block, BulletList):
            parts.append(_render_generic_block(block))
            continue

        def render_entry(it: ListItem) -> str:
            inner = "".join(_render_generic_block(ch) for ch in it.children)
            return (
                '<li class="changelog-item">'
                f'<div class="changelog-date">{render_inline(it.text)}</div>'
                f"{inner}"
                "</li>"
            )

        recent = block.items[:visible_count]
        older = block.items[visible_count:]
        parts.append(f'<ul class="changelog-list">{"".join(render_entry(it) for it in recent)}</ul>')

        if older:
            summary = (
                f"Show earlier revision history ({len(older)} entries)"
                if is_en
                else f"展開更早的修改歷程（共 {len(older)} 筆）"
            )
            parts.append(
                '<details class="collapsible">'
                f"<summary>{summary}</summary>"
                '<div class="collapsible-body">'
                f'<ul class="changelog-list" style="margin-top:12px;">'
                f'{"".join(render_entry(it) for it in older)}'
                "</ul>"
                "</div>"
                "</details>"
            )
    return "".join(parts)


def _render_copyright_collapsible(title: str, blocks: list[Block], section_id: str) -> str:
    parts: list[str] = []
    for block in blocks:
        if isinstance(block, BulletList):
            items_html: list[str] = []
            for item in block.items:
                body = "".join(
                    "".join(_render_generic_block(gch) for gch in ch.children)
                    if isinstance(ch, Blockquote)
                    else _render_generic_block(ch)
                    for ch in item.children
                )
                items_html.append(
                    "<li>"
                    f'<div class="copyright-title">{render_inline(item.text)}</div>'
                    f'<div class="copyright-body">{body}</div>'
                    "</li>"
                )
            parts.append(f'<ul class="copyright-list">{"".join(items_html)}</ul>')
        else:
            parts.append(_render_generic_block(block))

    return (
        f'<details class="collapsible" id="{section_id}">'
        f"<summary>{html.escape(title)}</summary>"
        f'<div class="collapsible-body">{"".join(parts)}</div>'
        "</details>"
    )


def _render_card_section(
    blocks: list[Block],
    is_en: bool,
    size_resolver: FileSizeResolver | None = None,
) -> str:
    """Render an H2 section containing H3 cards and optional intro notice."""
    intro_blocks: list[Block] = []
    cards: list[tuple[Heading, list[Block]]] = []
    current_h3: Heading | None = None
    current_body: list[Block] = []

    for block in blocks:
        if isinstance(block, Heading) and block.level == 3:
            if current_h3 is not None:
                cards.append((current_h3, current_body))
            current_h3 = block
            current_body = []
        elif current_h3 is None:
            intro_blocks.append(block)
        else:
            current_body.append(block)

    if current_h3 is not None:
        cards.append((current_h3, current_body))

    out: list[str] = []
    if intro_blocks:
        notice_parts: list[str] = []
        for blk in intro_blocks:
            if isinstance(blk, BulletList):
                if all(not it.children and _COORD_ITEM_RE.match(it.text.strip()) for it in blk.items):
                    pills = "".join(
                        f'<span class="coord-pill">{html.escape(it.text.strip())}</span>'
                        for it in blk.items
                    )
                    notice_parts.append(f'<div class="region-coords">{pills}</div>')
                elif all(not it.children for it in blk.items):
                    notice_parts.append(_render_generic_block(blk))
                else:
                    for item in blk.items:
                        inner = "".join(
                            "".join(_render_generic_block(gch) for gch in ch.children)
                            if isinstance(ch, Blockquote)
                            else _render_generic_block(ch)
                            for ch in item.children
                        )
                        notice_parts.append(f"<p><strong>{render_inline(item.text)}</strong></p>{inner}")
            else:
                notice_parts.append(_render_generic_block(blk))
        out.append(f'<div class="section-notice">{"".join(notice_parts)}</div>')

    out.append('<div class="card-grid">')
    for h3, body_blocks in cards:
        out.append(
            '<article class="card">'
            f'<h3 class="card-title">{render_inline(h3.raw)}</h3>'
            f"{_render_card_body(body_blocks, is_en, size_resolver)}"
            "</article>"
        )
    out.append("</div>")
    return "".join(out)


def _nav_short_label(title_plain: str) -> str:
    """Produce a concise navigation pill label from an H2 title."""
    short = re.sub(r"\s*[\(（][^()（）]*[\)）]\s*$", "", title_plain).strip()
    replacements = {
        "手機 App 自動安裝": "手機 App",
        "手機離線地圖": "手機離線",
        "Extra 離線圖層專區": "Extra 圖層",
        "Mapsforge 手動下載自行安裝": "手動下載",
        "PMTiles 向量圖磚": "PMTiles",
        "Garmin 離線地圖": "Garmin",
        "其他國外山區": "國外山區",
        "地圖範圍與地區介紹": "地區介紹",
        "地圖範圍與城市介紹": "城市介紹",
        "相關資源與鏡像站": "相關資源",
        "疊圖專用風格": "疊圖風格",
        "Mobile App Auto Install": "Mobile Apps",
        "Extra Offline Layer Zone": "Extra Layers",
        "Mapsforge Manual Download": "Manual Download",
        "PMTiles Vector Tiles": "PMTiles",
        "Garmin Offline Maps": "Garmin",
        "Other Overseas Mountain Regions": "Overseas",
        "Map Coverage & Region Guide": "Region Guide",
        "Map Coverage & City Guide": "City Guide",
        "Related Resources & Mirrors": "Resources",
        "Major Revision History": "History",
    }
    return replacements.get(short, short)


def _slugify(title_plain: str, index: int) -> str:
    ascii_part = re.sub(r"[^a-z0-9]+", "-", title_plain.lower()).strip("-")
    return ascii_part or f"section-{index}"


def render_document(
    md_text: str,
    template_html: str,
    version: str,
    lang: str,
    alt_lang_href: str,
    alt_lang_label: str,
    size_resolver: FileSizeResolver | None = None,
) -> str:
    """Convert Markdown text into the complete self-contained HTML page."""
    is_en = lang.lower().startswith("en")
    substituted = md_text.replace("__version__", version)
    blocks = parse_blocks(substituted.splitlines())

    # Split into Hero (before first H2) and H2 sections
    hero_title = "MOI.OSM - Taiwan TOPO"
    hero_paragraphs: list[Paragraph] = []
    sections: list[tuple[Heading, list[Block]]] = []
    current_h2: Heading | None = None
    current_blocks: list[Block] = []

    for blk in blocks:
        if isinstance(blk, Heading) and blk.level == 1 and current_h2 is None:
            hero_title = strip_markdown_images(blk.raw)
        elif isinstance(blk, Heading) and blk.level == 2:
            if current_h2 is not None:
                sections.append((current_h2, current_blocks))
            current_h2 = blk
            current_blocks = []
        elif current_h2 is None:
            if isinstance(blk, Paragraph):
                hero_paragraphs.append(blk)
        else:
            current_blocks.append(blk)

    if current_h2 is not None:
        sections.append((current_h2, current_blocks))

    # Build Hero HTML
    version_badge = f"v{version}"
    subtitle_html_parts: list[str] = []
    description_plain = hero_title
    for para in hero_paragraphs:
        joined = " ".join(para.lines)
        if _VERSION_RE.search(joined) or (version and f"v{version}" in joined):
            version_badge = joined
        elif "](" in joined and "·" in joined:
            link_chips = [
                render_inline(seg.strip()) for seg in joined.split("·") if seg.strip()
            ]
            subtitle_html_parts.append(f'<div class="hero-quicklinks">{"".join(link_chips)}</div>')
        else:
            description_plain = joined
            subtitle_html_parts.append(f'<p class="hero-subtitle">{render_inline(joined)}</p>')

    alt_btn = (
        f'<a class="hero-btn" href="{html.escape(alt_lang_href, quote=True)}">'
        f"{html.escape(alt_lang_label)}</a>"
        if alt_lang_href and alt_lang_label
        else ""
    )
    hero_html = (
        '<div class="hero-topbar">'
        f'<span class="version-pill">{html.escape(version_badge)}</span>'
        '<div class="hero-actions">'
        f"{alt_btn}"
        '<button type="button" id="theme-toggle" class="hero-btn" aria-label="Toggle color theme">☾</button>'
        "</div>"
        "</div>"
        f"<h1>{html.escape(hero_title)}</h1>"
        f'{"".join(subtitle_html_parts)}'
    )

    # Render sections into main vs footer
    nav_pills: list[str] = []
    main_parts: list[str] = []
    footer_parts: list[str] = []
    used_ids: set[str] = set()

    for idx, (h2, sec_blocks) in enumerate(sections, start=1):
        plain_title = strip_markdown_images(h2.raw)
        sec_id = _slugify(plain_title, idx)
        while sec_id in used_ids:
            sec_id = f"{sec_id}-{idx}"
        used_ids.add(sec_id)

        lower_title = plain_title.lower()
        is_copyright = "版權宣告" in plain_title or "copyright" in lower_title
        is_license = "地圖版權與散佈說明" in plain_title or "map license" in lower_title

        if is_copyright or is_license:
            footer_parts.append(_render_copyright_collapsible(plain_title, sec_blocks, sec_id))
            continue

        nav_pills.append(
            f'<a class="nav-pill" href="#{sec_id}">{html.escape(_nav_short_label(plain_title))}</a>'
        )

        has_h3 = any(isinstance(b, Heading) and b.level == 3 for b in sec_blocks)
        has_dl = any(isinstance(b, BulletList) and _has_download_items(b) for b in sec_blocks)

        if (
            "相關網頁" in plain_title
            or "相關資源" in plain_title
            or "related links" in lower_title
            or "related resources" in lower_title
        ):
            body_html = _render_links_section(sec_blocks)
        elif "國外山區" in plain_title or "overseas mountain" in lower_title:
            body_html = _render_regions_section(sec_blocks, is_en)
        elif "修改歷程" in plain_title or "revision history" in lower_title:
            body_html = _render_changelog_section(sec_blocks, is_en)
        elif has_h3:
            body_html = _render_card_section(sec_blocks, is_en, size_resolver)
        elif has_dl:
            body_html = f'<div class="card">{_render_card_body(sec_blocks, is_en, size_resolver)}</div>'
        else:
            body_html = f'<div class="prose-card">{"".join(_render_generic_block(b) for b in sec_blocks)}</div>'

        main_parts.append(
            f'<section class="topo-section" id="{sec_id}">'
            f'<h2 class="section-heading">{render_inline(h2.raw)}</h2>'
            f"{body_html}"
            "</section>"
        )

    if footer_parts:
        footer_label = "License" if is_en else "版權"
        first_footer_id = "copyright"
        m_id = re.search(r'id="([^"]+)"', footer_parts[0])
        if m_id:
            first_footer_id = m_id.group(1)
        nav_pills.append(f'<a class="nav-pill" href="#{first_footer_id}">{footer_label}</a>')

    footer_meta = (
        f'<div class="footer-meta">{html.escape(hero_title)} · v{html.escape(version)}</div>'
    )
    footer_html = "".join(footer_parts) + footer_meta

    page_title = f"{hero_title} v{version}"
    return (
        template_html.replace("{{LANG}}", html.escape(lang, quote=True))
        .replace("{{TITLE}}", html.escape(page_title))
        .replace("{{DESCRIPTION}}", html.escape(description_plain, quote=True))
        .replace("{{HERO}}", hero_html)
        .replace("{{NAV}}", "".join(nav_pills))
        .replace("{{MAIN}}", "".join(main_parts))
        .replace("{{FOOTER}}", footer_html)
    )


def _infer_docs_dir(source_path: Path) -> Path:
    """Walk up from source_path to find the ``docs/`` directory containing ``shared/site.toml``."""
    resolved = source_path.resolve()
    for parent in resolved.parents:
        if (parent / "shared" / "site.toml").exists():
            return parent
    return resolved.parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Render TOPO documentation to modern HTML.")
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--input", type=Path, help="Input Markdown file (supports <!-- include: ... -->)")
    src_group.add_argument(
        "--region-config",
        type=Path,
        help="Input region.toml file (assembled with guide*.md and docs/shared/site.toml)",
    )
    parser.add_argument("--docs-dir", type=Path, default=None, help="Root docs/ directory (auto-detected if omitted)")
    parser.add_argument("--template", type=Path, help="HTML template file (required unless --dump-md)")
    parser.add_argument("--output", type=Path, help="Output HTML file (required unless --dump-md)")
    parser.add_argument("--version", default="dev", help="Map version string (e.g. 2026.11.24)")
    parser.add_argument("--lang", default="zh-Hant", help="HTML lang attribute (zh-Hant or en)")
    parser.add_argument("--alt-lang-href", default="", help="Alternate language page href")
    parser.add_argument("--alt-lang-label", default="", help="Alternate language toggle label")
    parser.add_argument(
        "--size-dir",
        action="append",
        type=Path,
        default=[],
        help="Directory to scan for built/asset files when computing dynamic download sizes (repeatable)",
    )
    parser.add_argument(
        "--locus-dir",
        type=Path,
        default=None,
        help="Root auto-install/locus directory for summing Locus XML download sizes (auto-detected if omitted)",
    )
    parser.add_argument(
        "--dump-md",
        action="store_true",
        help="Print assembled/expanded Markdown to stdout instead of rendering HTML",
    )
    args = parser.parse_args()

    source_path: Path = args.region_config or args.input
    docs_dir = args.docs_dir or _infer_docs_dir(source_path)

    if args.region_config is not None:
        region_cfg = region_doc.load_region_config(args.region_config, docs_dir=docs_dir)
        site_cfg = region_doc.load_site_config(docs_dir)
        guide_name = "guide-en.md" if args.lang.lower().startswith("en") else "guide.md"
        guide_path = args.region_config.parent / guide_name
        guide_md = guide_path.read_text(encoding="utf-8") if guide_path.exists() else ""
        md_text = region_doc.build_region_markdown(region_cfg, site_cfg, guide_md, args.lang)
    else:
        raw_md = args.input.read_text(encoding="utf-8")
        md_text = region_doc.expand_includes(raw_md, docs_dir, args.lang)

    if args.dump_md:
        sys.stdout.write(md_text)
        return

    if not args.template or not args.output:
        parser.error("--template and --output are required unless --dump-md is specified")

    size_resolver: FileSizeResolver | None = None
    if args.size_dir:
        locus_dir = args.locus_dir
        if locus_dir is None:
            candidate_locus = docs_dir.resolve().parent / "auto-install" / "locus"
            if candidate_locus.is_dir():
                locus_dir = candidate_locus
        size_resolver = FileSizeResolver(args.size_dir, locus_dir=locus_dir)

    template_html = template_assets.expand_template_assets(
        args.template.read_text(encoding="utf-8"),
        docs_dir,
    )
    rendered = render_document(
        md_text=md_text,
        template_html=template_html,
        version=args.version,
        lang=args.lang,
        alt_lang_href=args.alt_lang_href,
        alt_lang_label=args.alt_lang_label,
        size_resolver=size_resolver,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
