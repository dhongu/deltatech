# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_price_unit_w_taxes(self):
        # check if price_unit is with taxes
        if not self.display_type:
            with_taxes = False
            for tax in self.tax_id:
                if tax.price_include:
                    with_taxes = True
            if with_taxes:
                if self.product_uom_qty != 0.0:
                    price_unit = self.price_unit - self.price_tax / self.product_uom_qty
                else:
                    price_unit = self.price_unit - self.price_tax
            else:
                price_unit = self.price_unit
            return price_unit
        else:
            return False

    def change_price_or_product(self, res):
        if not res:
            res = {}
        if not res.get("warning", False):
            price_unit = self.get_price_unit_w_taxes()
            get_param = self.env["ir.config_parameter"].sudo().get_param
            check_on_validate = safe_eval(get_param("sale.margin_limit_check_validate", "0"))
            if price_unit and price_unit < self.purchase_price and self.purchase_price > 0 and not check_on_validate:
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

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        get_param = self.env["ir.config_parameter"].sudo().get_param
        check_on_validate = safe_eval(get_param("sale.margin_limit_check_validate", "0"))
        if check_on_validate:
            for line in self:
                line.check_sale_price()
        return res

    def check_sale_price(self):
        res = {}
        if self.env.context.get("ignore_price_check", False):
            return res
        # daca comanda se face in website se ignora verificarea pretului de cost pentru a face unele promotii
        if self.env.context.get("website_id", False):
            return res

        get_param = self.env["ir.config_parameter"].sudo().get_param
        margin_limit = safe_eval(get_param("sale.margin_limit", "0"))
        # verificare doar la validare
        check_on_validate = safe_eval(get_param("sale.margin_limit_check_validate", "0"))
        if check_on_validate and not self.env.context.get("call_from_action_confirm", False):
            return res

        for line in self:
            if line.display_type or line.product_type == "service":
                continue
            if line.product_uom_qty < 0:
                continue
            if line.is_delivery:
                continue
            if line.price_unit == 0 and line.product_id:
                if not self.env["res.users"].has_group("deltatech_sale_margin.group_sale_below_purchase_price"):
                    raise UserError(_("You can not sell %s without price.") % line.product_id.name)
                else:
                    message = _("Sale %s without price.") % line.product_id.name
                    line.order_id.message_post(body=message)
            price_unit = line.get_price_unit_w_taxes()
            if price_unit:
                if price_unit < line.purchase_price:
                    if not self.env["res.users"].has_group("deltatech_sale_margin.group_sale_below_purchase_price"):
                        raise UserError(_("You can not sell below the purchase price."))
                    else:
                        message = _("Sale %s under the purchase price.") % line.product_id.name
                        line.order_id.message_post(body=message)

                margin = (price_unit - line.purchase_price) / price_unit * 100
                if margin < margin_limit:
                    if not self.env["res.users"].has_group("deltatech_sale_margin.group_sale_below_margin"):
                        raise UserError(_("You can not sell below margin: %s") % line.product_id.name)
                    else:
                        message = _("Sale %s below margin.") % line.product_id.name
                        line.order_id.message_post(body=message)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.env.context.get("ignore_price_check", False):
            return res
        # daca comanda se face in website se ignora verificarea pretului de cost pentru a face unele promotii
        if self.env.context.get("website_id", False):
            return res
        get_param = self.env["ir.config_parameter"].sudo().get_param
        check_on_validate = safe_eval(get_param("sale.margin_limit_check_validate", False))
        if check_on_validate:
            for order in self:
                for line in order.order_line:
                    line.with_context(call_from_action_confirm=True).check_sale_price()
        return res
