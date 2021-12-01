# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    discount_received = fields.Float("Discount %", digits=(4, 2))
    price_without_discount = fields.Monetary("Price w discount", currency_field="currency_id")

    @api.onchange("product_id")
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        self.price_without_discount = self.price_unit
        return res

    @api.onchange("price_without_discount", "discount_received")
    def onchange_discount(self):
        if self.price_without_discount:
            self.price_unit = self.price_without_discount * (1.0 - self.discount_received / 100.0)
