"""Inline shared CSS/JS design-system assets into RudyMap HTML templates.

Zero external dependencies (Python 3 standard library only). Used by both
``tools/render_topo_html.py`` and ``tools/build_legend.py`` so output HTML
pages remain self-contained while sharing one source of truth under
``docs/shared/``.
"""

from __future__ import annotations

import re
from pathlib import Path

_DARK_BLOCK_RE = re.compile(r'(:root\[data-theme="dark"\]\s*\{([^}]*)\})', re.DOTALL)


def infer_docs_dir(source_path: Path) -> Path:
    """Walk up from ``source_path`` to find the ``docs/`` directory containing ``shared/``."""
    resolved = source_path.resolve()
    for parent in resolved.parents:
        if (parent / "shared").is_dir():
            return parent
    return resolved.parent.parent


def _expand_dark_media(css_text: str) -> str:
    """Mirror ``:root[data-theme="dark"]`` tokens into ``prefers-color-scheme: dark``."""
    m = _DARK_BLOCK_RE.search(css_text)
    if not m:
        return css_text
    inner = m.group(2)
    media_block = (
        "@media (prefers-color-scheme: dark) {\n"
        '  :root:not([data-theme="light"]) {'
        f"{inner}"
        "}\n"
        "}\n\n"
    )
    return css_text[: m.start()] + media_block + css_text[m.start() :]


def expand_template_assets(template_html: str, docs_dir: Path) -> str:
    """Inline shared CSS/JS assets (``{{SHARED_*}}``) into an HTML template."""
    shared_dir = docs_dir / "shared"
    if "{{SHARED_THEME_CSS}}" in template_html:
        theme_css = _expand_dark_media((shared_dir / "theme.css").read_text(encoding="utf-8"))
        template_html = template_html.replace("{{SHARED_THEME_CSS}}", theme_css.strip())
    if "{{SHARED_THEME_JS}}" in template_html:
        theme_js = (shared_dir / "theme.js").read_text(encoding="utf-8")
        template_html = template_html.replace("{{SHARED_THEME_JS}}", theme_js.strip())
    if "{{SHARED_PDF_CSS}}" in template_html:
        pdf_css = (shared_dir / "pdf_base.css").read_text(encoding="utf-8")
        template_html = template_html.replace("{{SHARED_PDF_CSS}}", pdf_css.strip())
    return template_html
