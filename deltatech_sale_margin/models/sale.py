# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def change_price_or_product(self, res):
        if not res:
            res = {}
        if not res.get("warning", False):
            if self.price_unit < self.purchase_price and self.purchase_price > 0:
                warning = {"title": _("Price Error!"), "message": _("Do not sell below the purchase price.")}
                res["warning"] = warning
        return res

    @api.onchange("product_id")
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change() or {}
        res = self.change_price_or_product(res)
        return res

    @api.onchange("price_unit")
    def price_unit_change(self):
        res = {}
        res = self.change_price_or_product(res)
        return res

    @api.constrains("price_unit", "purchase_price")
    def _check_sale_price(self):
        for line in self:
            if line.display_type:
                continue
            if line.price_unit == 0:
                if not self.env["res.users"].has_group("deltatech_sale_margin.group_sale_below_purchase_price"):
                    raise UserError(_("You can not sell without price."))
                else:
                    message = _("Sale %s without price.") % line.product_id.name
                    self.order_id.message_post(body=message)

            if line.price_unit < line.purchase_price:
                if not self.env["res.users"].has_group("deltatech_sale_margin.group_sale_below_purchase_price"):
                    raise UserError(_("You can not sell below the purchase price."))
                else:
                    message = _("Sale %s under the purchase price.") % line.product_id.name
                    self.order_id.message_post(body=message)
