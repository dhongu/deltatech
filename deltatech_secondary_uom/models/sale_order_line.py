# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "deltatech.secondary.uom.mixin"]

    def _get_secondary_product(self):
        return self.product_id

    def _get_line_qty_and_uom(self):
        return self.product_uom_qty, self.product_uom_id

    def _set_line_qty(self, qty):
        self.product_uom_qty = qty

    @api.depends("product_uom_qty", "product_uom_id", "secondary_uom_id", "product_id")
    def _compute_secondary_uom_qty(self):
        return super()._compute_secondary_uom_qty()

    @api.depends("product_id")
    def _compute_allowed_secondary_uom_ids(self):
        return super()._compute_allowed_secondary_uom_ids()

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()
        if self.secondary_uom_id:
            values["secondary_uom_id"] = self.secondary_uom_id.id
        return values
