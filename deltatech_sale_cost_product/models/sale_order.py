from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    cost_of_goods = fields.Monetary(
        string="Cost of Goods",
        default=0.0,
        groups="deltatech_sale_cost_product.group_view_cost_on_sale",
    )

    def _get_cost_of_goods(self):
        """Cost of the order lines in the order currency, read in the order company
        and converted from the product base UoM to the line UoM."""
        self.ensure_one()
        cost = 0.0
        for line in self.order_line.with_company(self.company_id):
            if not line.product_id or not line.product_uom_id:
                continue
            product = line.product_id
            unit_cost = product.uom_id._compute_price(product.standard_price, line.product_uom_id)
            cost += line._convert_to_sol_currency(unit_cost, product.cost_currency_id) * line.product_uom_qty
        return cost

    def _update_cost_of_goods(self):
        for order in self:
            order.sudo().cost_of_goods = order._get_cost_of_goods()

    def write(self, vals):
        res = super().write(vals)
        if "state" in vals and vals["state"] == "sale":
            self._update_cost_of_goods()
        return res

    def calculate_cost_of_goods_for_confirmed_orders(self):
        confirmed_orders = self.search([("state", "=", "sale")])
        confirmed_orders._update_cost_of_goods()
