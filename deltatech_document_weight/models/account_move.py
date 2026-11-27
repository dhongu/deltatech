from odoo import api, fields, models


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


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    document_weight_gross = fields.Float(
        string="Gross weight",
        compute="_compute_document_weight_gross",
        digits="Stock Weight",
        help="Estimated gross weight of the quantity on the line, in the weight unit of the database.",
    )

    @api.depends("product_id", "product_id.weight", "quantity", "product_uom_id", "display_type")
    def _compute_document_weight_gross(self):
        for line in self:
            if line.product_id and line.display_type == "product":
                weights = line.product_id._get_document_weights(line.quantity, line.product_uom_id)
                line.document_weight_gross = weights["gross"]
            else:
                line.document_weight_gross = 0.0
