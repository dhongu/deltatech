# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    search_ok = fields.Boolean(
        string="Searchable",
        default=True,
        help="Include the values of this attribute when searching for a product. "
        "Turn it off for attributes whose values are too generic to be useful in a "
        "search and would only add noise to the results.",
    )
