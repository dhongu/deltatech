# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "deltatech.secondary.uom.mixin"]

    def _get_secondary_product(self):
        return self.product_id

    def _get_line_qty_and_uom(self):
        return self.product_qty, self.product_uom_id

    def _set_line_qty(self, qty):
        self.product_qty = qty

    @api.depends("product_qty", "product_uom_id", "secondary_uom_id", "product_id")
    def _compute_secondary_uom_qty(self):
        return super()._compute_secondary_uom_qty()

    @api.depends("product_id")
    def _compute_allowed_secondary_uom_ids(self):
        return super()._compute_allowed_secondary_uom_ids()

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        vals = super()._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        if self.secondary_uom_id:
            vals["secondary_uom_id"] = self.secondary_uom_id.id
        return vals
