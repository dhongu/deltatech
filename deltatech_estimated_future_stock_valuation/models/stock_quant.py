from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    estimated_future_stock_valuation = fields.Float(string="Available Value", store=True, digits="Product Price")

    def _compute_available_quantity(self):
        super()._compute_available_quantity()
        for quant in self:
            quant.estimated_future_stock_valuation = quant.available_quantity * quant.product_id.standard_price
