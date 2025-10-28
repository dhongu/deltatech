# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    visibility = fields.Selection(
        selection=[("visible", "Visible"), ("hidden", "Hidden")], default="visible", index=True
    )
