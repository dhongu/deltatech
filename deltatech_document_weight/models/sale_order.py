from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "deltatech.document.weight.mixin"]

    def _get_document_weight_totals(self, lines=None):
        self.ensure_one()
        lines = self.order_line if lines is None else lines
        return self._sum_document_weights(
            (line.product_id, line.product_uom_qty, line.product_uom_id)
            for line in lines
            if line.product_id and not line.display_type
        )
