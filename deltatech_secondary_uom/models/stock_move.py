# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move", "deltatech.secondary.uom.mixin"]

    def _get_secondary_product(self):
        return self.product_id

    def _get_line_qty_and_uom(self):
        return self.product_uom_qty, self.product_uom

    def _set_line_qty(self, qty):
        self.product_uom_qty = qty

    @api.depends("product_uom_qty", "product_uom", "secondary_uom_id", "product_id")
    def _compute_secondary_uom_qty(self):
        return super()._compute_secondary_uom_qty()

    @api.depends("product_id")
    def _compute_allowed_secondary_uom_ids(self):
        return super()._compute_allowed_secondary_uom_ids()

    def _prepare_merge_moves_distinct_fields(self):
        return super()._prepare_merge_moves_distinct_fields() + ["secondary_uom_id"]
