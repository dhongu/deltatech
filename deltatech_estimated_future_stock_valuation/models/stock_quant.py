from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    forcasted_quantity = fields.Float(string="Forcasted Quantity", store=True, digits="Product Unit of Measure")
    estimated_future_stock_valuation = fields.Float(string="Forcasted Value", store=True, digits="Product Price")

    def _compute_available_quantity(self):
        super()._compute_available_quantity()
        for quant in self:
            if quant.location_id.usage == "internal":
                incoming_pickings = self.env["stock.picking"].search(
                    [("location_dest_id", "=", quant.location_id.id), ("state", "not in", ["done", "cancel"])]
                )
                outgoing_pickings = self.env["stock.picking"].search(
                    [("location_id", "=", quant.location_id.id), ("state", "not in", ["done", "cancel"])]
                )
                incoming_qty = sum(
                    incoming_pickings.mapped("move_lines")
                    .filtered(lambda m: m.product_id == quant.product_id)
                    .mapped("product_uom_qty")
                )
                outgoing_qty = sum(
                    outgoing_pickings.mapped("move_lines")
                    .filtered(lambda m: m.product_id == quant.product_id)
                    .mapped("product_uom_qty")
                )
                quant.forcasted_quantity = quant.inventory_quantity_auto_apply + incoming_qty - outgoing_qty
                quant.estimated_future_stock_valuation = quant.forcasted_quantity * quant.product_id.standard_price
            else:
                quant.forcasted_quantity = 0
                quant.estimated_future_stock_valuation = 0
