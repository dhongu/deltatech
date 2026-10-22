# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    category_icon_levels = fields.Selection(
        [
            ("root", "Main categories only"),
            ("all", "All categories"),
            ("inherit", "All categories, inherit from parent"),
        ],
        string="Category Icons in List",
        default="root",
        required=True,
        help="Which categories of the shop's category list show an icon.\n"
        "Main categories only: the opened branch shows its subcategories as text, which keeps "
        "the list light and easy to read.\n"
        "All categories: every category with its own icon shows it.\n"
        "All categories, inherit from parent: a subcategory without its own icon shows the icon "
        "of its closest parent that has one.",
    )

    # No cache to clear on a change: website.write clears the registry cache, the
    # automatic category menu of deltatech_website_shop_snippets included.
    category_icon_order = fields.Selection(
        [
            ("svg_image_product", "SVG, image, first product image"),
            ("image_svg_product", "Image, SVG, first product image"),
            ("svg_image", "SVG, image, none"),
            ("image_svg", "Image, SVG, none"),
        ],
        string="Category Icon Order",
        default="svg_image",
        required=True,
        help="What the shop shows for a category, in this order, the first one found:\n"
        "SVG: the category's own icon, else the icon of its closest parent that has one.\n"
        "Image: the category's own image.\n"
        "First product image: the picture of the first published product of the category "
        "or of its subcategories.\n"
        "None: nothing, the name alone.",
    )
