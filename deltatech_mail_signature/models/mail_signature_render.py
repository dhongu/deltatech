# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
"""Filling of the ``{{field}}`` placeholders of a signature template.

Pure functions, without database access: the values come in a dictionary. The HTML is parsed, the
values are put in the tree as text (so they are escaped when serialized, never parsed as markup) and
the result goes through ``html_sanitize``.
"""

import re

from lxml import etree
from lxml import html as lxml_html

from odoo.tools import html_sanitize

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")
_FRAGMENT = "signatureroot"
# elements that are a "line" of the signature: removed when all their fields are empty
LINE_TAGS = frozenset(
    ("p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "tr", "dd", "dt", "blockquote", "pre")
)
SAFE_SCHEMES = ("http:", "https:", "mailto:", "tel:")
_SCHEME = re.compile(r"^[a-z][a-z0-9+.\-]*:")
_DOUBLE_SCHEME = re.compile(r"^(?:https?://)(https?://)", re.I)
_CONTROL = re.compile(r"[\x00-\x20]")
EMPTY_LINKS = ("", "mailto:", "tel:", "https://", "http://")


def field_names(text):
    """The names of the fields written as ``{{name}}`` in ``text``, in order."""
    return PLACEHOLDER.findall(text or "")


def find_invalid(text, valid):
    """The unknown field names of ``text`` and whether it has a malformed ``{{`` / ``}}``."""
    unknown = [name for name in field_names(text) if name not in valid]
    rest = PLACEHOLDER.sub("", text or "")
    return list(dict.fromkeys(unknown)), "{{" in rest or "}}" in rest


def _own_texts(element):
    """The strings of an element that can hold fields: its attributes and text, and the tail of each child."""
    yield from element.attrib.values()
    if element.text:
        yield element.text
    for child in element:
        if child.tail:
            yield child.tail


def _line_fields(line):
    """The field names used in a line (own and inline descendants), not in nested lines."""
    names = []
    for element in line.iter():
        if element is not line and element.tag in LINE_TAGS:
            if element.tail:
                names += field_names(element.tail)
            continue
        if not isinstance(element.tag, str):
            continue
        for text in _own_texts(element):
            names += field_names(text)
    return names


def _substitute(text, values):
    return PLACEHOLDER.sub(lambda m: values.get(m.group(1), ""), text)


def _safe_href(value):
    """``value`` when it is a web, mail or phone address (or a relative one), else ``None``."""
    compact = _CONTROL.sub("", value).lower()
    if _SCHEME.match(compact) and not compact.startswith(SAFE_SCHEMES):
        return None
    return value.strip()


def _fill_element(element, values, href_values):
    for key, text in list(element.attrib.items()):
        if "{{" not in text:
            continue
        names = field_names(text)
        if key.lower() == "href":
            filled = _DOUBLE_SCHEME.sub(r"\1", _substitute(text, href_values).strip())
            filled = _safe_href(filled) if filled.lower() not in EMPTY_LINKS else None
            if filled is None or not any(href_values.get(name) for name in names):
                del element.attrib[key]
            else:
                element.set(key, filled)
        else:
            element.set(key, _substitute(text, values))
    if element.text and "{{" in element.text:
        element.text = _substitute(element.text, values)
    for child in element:
        if child.tail and "{{" in child.tail:
            child.tail = _substitute(child.tail, values)


def _drop(element):
    """Remove an element keeping the text that follows it."""
    parent = element.getparent()
    if element.tail:
        previous = element.getprevious()
        if previous is not None:
            previous.tail = (previous.tail or "") + element.tail
        else:
            parent.text = (parent.text or "") + element.tail
    parent.remove(element)


def render(body, values, href_values=None):
    """The HTML ``body`` with the ``{{field}}`` placeholders filled from ``values`` (name -> text).

    A line (block element) in which every field is empty is removed; elsewhere an empty field is
    replaced by nothing. ``href_values`` are the values used inside links (default ``values``)."""
    if not body or not body.strip():
        return ""
    href_values = values if href_values is None else href_values
    try:
        root = lxml_html.fragment_fromstring(body, create_parent=_FRAGMENT)
    except (etree.ParserError, etree.XMLSyntaxError):
        return ""
    lines = [
        el
        for el in root.iter()
        if isinstance(el.tag, str)
        and el.tag in LINE_TAGS
        and not any(isinstance(d.tag, str) and d.tag in LINE_TAGS for d in el.iterdescendants())
    ]
    for line in lines:
        names = _line_fields(line)
        if names and not any(values.get(name) for name in names):
            _drop(line)
    # rows left without any cell
    for row in list(root.iter("tr")):
        if not any(True for _cell in row.iterchildren("td", "th")):
            _drop(row)
    for element in list(root.iter()):
        if isinstance(element.tag, str):
            _fill_element(element, values, href_values)
    serialized = etree.tostring(root, encoding="unicode", method="html")
    result = serialized[len(f"<{_FRAGMENT}>") : -len(f"</{_FRAGMENT}>")].strip()
    return html_sanitize(result, sanitize_attributes=False, sanitize_style=False)
