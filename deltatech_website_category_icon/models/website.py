# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    category_icon_inherit = fields.Boolean(
        "Inherit Category Icons",
        help="In the category list, a subcategory without its own icon shows the icon of its closest parent that has one.",
    )
