from odoo import api, fields, models


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


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    document_weight_gross = fields.Float(
        string="Gross weight",
        compute="_compute_document_weight_gross",
        digits="Stock Weight",
        help="Estimated gross weight of the quantity on the line, in the weight unit of the database.",
    )

    @api.depends("product_id", "product_id.weight", "product_uom_qty", "product_uom_id", "display_type")
    def _compute_document_weight_gross(self):
        for line in self:
            if line.product_id and not line.display_type:
                weights = line.product_id._get_document_weights(line.product_uom_qty, line.product_uom_id)
                line.document_weight_gross = weights["gross"]
            else:
                line.document_weight_gross = 0.0
