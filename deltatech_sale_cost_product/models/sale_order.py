from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cost_of_goods = fields.Monetary(string="Cost of Goods", default=0.0)

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if "state" in vals and vals["state"] == "sale":
                vals["cost_of_goods"] = sum(
                    line.product_id.standard_price * line.product_uom_qty
                    for line in self.env["sale.order.line"].browse(vals.get("order_line"))
                )
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "state" in vals and vals["state"] == "sale":
            for order in self:
                order.cost_of_goods = sum(
                    line.product_id.standard_price * line.product_uom_qty for line in order.order_line
                )
        return res

    def calculate_cost_of_goods_for_confirmed_orders(self):
        confirmed_orders = self.search([("state", "=", "sale")])
        for order in confirmed_orders:
            order.cost_of_goods = sum(
                line.product_id.standard_price * line.product_uom_qty for line in order.order_line
            )
