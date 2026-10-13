# © 2026 Deltatech
# See README.rst file on addons root folder for license details
"""Convert a module sheet (readme/FISA_CONSULTANT.md) into self-contained HTML.

Relatively-referenced images (e.g. `screenshots/01.png`) are embedded as base64, so the
resulting HTML can be attached as a single document to a process in `deltatech_business_process`.
"""

import base64
import os
import re

_STYLE = (
    "body{font-family:Arial,Helvetica,sans-serif;max-width:1000px;margin:auto;color:#222}"
    "h1{font-size:22px}h2{font-size:17px;margin-top:22px}h3{font-size:15px}"
    "img{max-width:100%;border:1px solid #ddd;margin:8px 0;border-radius:4px}"
    "table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid #ccc;padding:4px 8px}"
    "code,pre{background:#f5f5f5;border-radius:3px}pre{padding:8px;overflow:auto}"
)


def _embed_images(html, base_dir):
    def repl(match):
        prefix, src, suffix = match.group(1), match.group(2), match.group(3)
        if src.startswith(("http:", "https:", "data:")):
            return match.group(0)
        path = os.path.normpath(os.path.join(base_dir, src))
        if os.path.isfile(path):
            with open(path, "rb") as fh:
                b64 = base64.b64encode(fh.read()).decode("ascii")
            ext = (os.path.splitext(path)[1].lstrip(".") or "png").lower()
            return f"{prefix}data:image/{ext};base64,{b64}{suffix}"
        return match.group(0)

    # match src="..." regardless of attribute order in the <img> tag
    return re.sub(r'(<img[^>]*?\bsrc=")([^"]+)(")', repl, html)


def fisa_md_to_html(md_path):
    """Return self-contained HTML for a markdown sheet, or None if missing/fails."""
    if not md_path or not os.path.isfile(md_path):
        return None
    try:
        import markdown  # noqa: PLC0415
    except ImportError:
        return None
    with open(md_path, encoding="utf-8") as fh:
        text = fh.read()
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    body = _embed_images(body, os.path.dirname(md_path))
    return (
        f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        f"<style>{_STYLE}</style></head><body>{body}</body></html>"
    )
