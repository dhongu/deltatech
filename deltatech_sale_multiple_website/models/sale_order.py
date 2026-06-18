from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update_order_line(self, order_line, quantity, **kwargs):
        order_line = order_line.with_env(self.env)
        if quantity > 0:
            quantity = order_line.fix_qty_multiple(
                order_line.product_id,
                order_line.product_uom_id,
                quantity,
            )
        return super()._cart_update_order_line(order_line, quantity, **kwargs)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def fix_qty_multiple(self, product, product_uom, qty=0):
        if not product.check_min_website or self.env.context.get("website_id"):
            return super().fix_qty_multiple(product, product_uom, qty)
        return qty
