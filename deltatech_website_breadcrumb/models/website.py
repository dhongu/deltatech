# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    breadcrumb_show_product_name = fields.Boolean(
        string="Product Name in Breadcrumb",
        default=True,
        help="Show the product name at the end of the breadcrumb of the product page. "
        "Off when the page title, right under it, already shows it.",
    )
