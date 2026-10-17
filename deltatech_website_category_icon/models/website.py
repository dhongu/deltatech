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
