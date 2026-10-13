from odoo import api, fields, models


class StockReplenishmentExplanation(models.TransientModel):
    _name = "stock.replenishment.explanation"
    _description = "Replenishment Explanation"

    orderpoint_id = fields.Many2one("stock.warehouse.orderpoint", required=True, ondelete="cascade")
    product_id = fields.Many2one(related="orderpoint_id.product_id")
    warehouse_id = fields.Many2one(related="orderpoint_id.warehouse_id")
    qty_forecast = fields.Float(related="orderpoint_id.qty_forecast")
    qty_to_order = fields.Float(related="orderpoint_id.qty_to_order")
    explanation_html = fields.Html(compute="_compute_explanation_html", sanitize=False)

    @api.depends("orderpoint_id")
    def _compute_explanation_html(self):
        for wizard in self:
            if not wizard.orderpoint_id:
                wizard.explanation_html = False
                continue
            values = wizard.orderpoint_id._get_replenishment_explanation()
            wizard.explanation_html = self.env["ir.qweb"]._render(
                "deltatech_replenishment_explain.replenishment_explanation", values
            )

    def action_open_forecast_report(self):
        self.ensure_one()
        return self.orderpoint_id.action_product_forecast_report()
