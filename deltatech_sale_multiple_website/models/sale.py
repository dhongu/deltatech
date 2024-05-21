# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update_order_line(self, product_id, quantity, order_line, **kwargs):
        if product_id and quantity:
            product = self.env["product.product"].browse(product_id)
            new_qty = order_line.fix_qty_multiple(product, product.uom_id, quantity)
            return super()._cart_update_order_line(product_id, new_qty, order_line, **kwargs)
        else:
            return super()._cart_update_order_line(product_id, quantity, order_line, **kwargs)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def fix_qty_multiple(self, product, product_uom, qty=0):
        if product.check_min_website:  # daca se face verificare doar in website
            if self.env.context.get("website_id"):
                qty = super().fix_qty_multiple(product, product_uom, qty)
        else:
            qty = super().fix_qty_multiple(product, product_uom, qty)

        return qty
