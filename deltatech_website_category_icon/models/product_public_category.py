# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import re

from lxml import etree
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain

SVG_NS = "http://www.w3.org/2000/svg"

# Flat drawings only: no <defs>, <use>, <image>, <style>, <script>, <foreignObject>,
# gradients or filters. Nothing here can load a resource or run code, and no
# element carries an id, so several icons can be inlined in the same page.
ALLOWED_TAGS = {"svg", "g", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "title"}

ALLOWED_ATTRIBUTES = {
    "viewBox",
    "d",
    "x",
    "y",
    "x1",
    "y1",
    "x2",
    "y2",
    "width",
    "height",
    "rx",
    "ry",
    "cx",
    "cy",
    "r",
    "points",
    "fill",
    "fill-opacity",
    "fill-rule",
    "clip-rule",
    "stroke",
    "stroke-width",
    "stroke-opacity",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-dasharray",
    "opacity",
    "transform",
    "aria-hidden",
}

# Colors, numbers, path data and keywords. No "(", so no url(), var() or expression().
PLAIN_VALUE = re.compile(r"^[#\w\s,.%-]*$")
# rgb()/rgba() colors are the one place a parenthesis is accepted outside transform.
RGB_VALUE = re.compile(r"^rgba?\(\s*[\d.\s,%]+\)$")
TRANSFORM_VALUE = re.compile(r"^(\s*(translate|rotate|scale|matrix|skewX|skewY)\(\s*[-\d.\s,e]+\)\s*,?)+$")

MAX_ICON_SIZE = 20000

# Most categories the snippet Category Icon Grid shows, whatever the editor asks.
MAX_GRID_CATEGORIES = 48


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    icon_svg = fields.Text(
        "Icon (SVG)",
        help="SVG markup of the category icon, square viewBox. Only flat shapes are kept: "
        "path, rect, circle, ellipse, line, polyline, polygon and g.",
    )
    # icon_svg went through _sanitize_icon_svg on the way in, so it is safe to inline.
    icon_html = fields.Html("Icon", compute="_compute_icon_html", sanitize=False)
    icon_preview = fields.Html("Icon Preview", compute="_compute_icon_html", sanitize=False)
    icon_inherited_html = fields.Html(
        "Inherited Icon",
        compute="_compute_icon_inherited_html",
        recursive=True,
        sanitize=False,
        help="Icon of the closest parent category that has one, for the website option Category Icons in List.",
    )

    @api.depends("icon_svg")
    def _compute_icon_html(self):
        for category in self:
            icon = Markup(category.icon_svg) if category.icon_svg else False
            category.icon_html = icon
            category.icon_preview = icon and Markup('<div style="width:96px;height:96px">%s</div>') % icon

    @api.depends("parent_id.icon_svg", "parent_id.icon_inherited_html")
    def _compute_icon_inherited_html(self):
        for category in self:
            parent = category.parent_id
            category.icon_inherited_html = Markup(parent.icon_svg) if parent.icon_svg else parent.icon_inherited_html

    @api.model
    def _get_icon_grid_categories(self, website, category_ids=None, limit=12):
        """Categories shown by the snippet Category Icon Grid on the given website.

        Without ``category_ids`` these are the main categories, in their shop order;
        with them, the chosen categories in the order they were chosen. Categories of
        another website, and for visitors categories without published products, are
        left out, as in the shop.
        """
        limit = max(1, min(int(limit or 12), MAX_GRID_CATEGORIES))
        domain = self._get_available_category_domain(website.id)
        if not category_ids:
            return self.search(domain & Domain("parent_id", "=", False), limit=limit)
        category_ids = [int(category_id) for category_id in category_ids]
        categories = self.search(domain & Domain("id", "in", category_ids))
        return categories.sorted(lambda category: category_ids.index(category.id))[:limit]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("icon_svg"):
                vals["icon_svg"] = self._sanitize_icon_svg(vals["icon_svg"])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("icon_svg"):
            vals["icon_svg"] = self._sanitize_icon_svg(vals["icon_svg"])
        return super().write(vals)

    @api.model
    def _sanitize_icon_svg(self, svg):
        """Return the icon as a clean, inline-safe <svg> element.

        The icon is inlined in public pages, so anything outside the allow-list
        is rejected rather than silently dropped: whoever drew it (a person, the
        icon skill or an LLM) gets told what to fix, and a stored icon is always
        exactly what was approved.
        """
        svg = svg.strip()
        if len(svg) > MAX_ICON_SIZE:
            raise ValidationError(
                self.env._(
                    "The icon is too large (%(size)s characters, at most %(max)s).", size=len(svg), max=MAX_ICON_SIZE
                )
            )
        parser = etree.XMLParser(resolve_entities=False, no_network=True, remove_comments=True, remove_pis=True)
        try:
            root = etree.fromstring(svg.encode(), parser=parser)
        except etree.XMLSyntaxError as e:
            raise ValidationError(self.env._("The icon is not valid SVG: %s", e)) from e
        if root.tag != f"{{{SVG_NS}}}svg" and root.tag != "svg":
            raise ValidationError(self.env._("The icon must be an <svg> element."))
        if not root.get("viewBox"):
            raise ValidationError(self.env._("The icon needs a viewBox, so it can scale to any size."))

        clean = self._copy_icon_element(root)
        # The size comes from the page (CSS), not from the drawing.
        for name in ("width", "height"):
            clean.attrib.pop(name, None)
        clean.set("aria-hidden", "true")
        return etree.tostring(clean, encoding="unicode", pretty_print=True).strip()

    @api.model
    def _copy_icon_element(self, element):
        """Copy one checked element and its children into the SVG namespace."""
        if not isinstance(element.tag, str):
            raise ValidationError(self.env._("The icon may only contain drawing elements."))
        tag = etree.QName(element).localname
        if element.tag not in (tag, f"{{{SVG_NS}}}{tag}") or tag not in ALLOWED_TAGS:
            raise ValidationError(self.env._("The icon contains a forbidden element: <%s>.", tag))
        for name, value in element.attrib.items():
            if name not in ALLOWED_ATTRIBUTES:
                raise ValidationError(
                    self.env._("The icon contains a forbidden attribute: %(name)s on <%(tag)s>.", name=name, tag=tag)
                )
            if name == "transform":
                value_ok = TRANSFORM_VALUE.match(value)
            else:
                value_ok = PLAIN_VALUE.match(value) or RGB_VALUE.match(value)
            if not value_ok:
                raise ValidationError(
                    self.env._("The icon has a forbidden value in %(name)s: %(value)s", name=name, value=value)
                )
        clean = etree.Element(f"{{{SVG_NS}}}{tag}", dict(element.attrib), nsmap={None: SVG_NS})
        if tag == "title":
            clean.text = element.text
        for child in element:
            clean.append(self._copy_icon_element(child))
        return clean
