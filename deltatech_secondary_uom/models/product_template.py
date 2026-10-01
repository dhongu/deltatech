# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    secondary_uom_ids = fields.One2many(
        "deltatech.product.uom.conversion", "product_tmpl_id", string="Alternative Units"
    )

    def _get_secondary_uom_conversion(self, uom):
        self.ensure_one()
        if not uom:
            return self.env["deltatech.product.uom.conversion"]
        return self.secondary_uom_ids.filtered(lambda c: c.uom_id == uom)[:1]
