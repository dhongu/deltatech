from odoo import models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "deltatech.document.weight.mixin"]

    def _get_document_weight_totals(self, lines=None):
        self.ensure_one()
        lines = self.invoice_line_ids if lines is None else lines
        return self._sum_document_weights(
            (line.product_id, line.quantity, line.product_uom_id)
            for line in lines
            if line.product_id and line.display_type == "product"
        )
