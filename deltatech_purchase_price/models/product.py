# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(tracking=True)

    @api.onchange("last_purchase_price", "trade_markup")
    def onchange_last_purchase_price(self):
        self.product_tmpl_id.onchange_last_purchase_price()


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(tracking=True)
    list_price = fields.Float(tracking=True)
    last_purchase_price = fields.Float(digits="Product Price", tracking=True)

    @api.onchange("list_price")
    def onchange_list_price(self):
        AccountTax = self.env["account.tax"]
        list_price = AccountTax._fix_tax_included_price_company(
            self.list_price, self.taxes_id, AccountTax, self.company_id
        )
        if self.last_purchase_price:
            trade_markup = (list_price - self.last_purchase_price) / self.last_purchase_price * 100
            self.trade_markup = trade_markup

    @api.onchange("last_purchase_price", "trade_markup")
    def onchange_last_purchase_price(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        change_list_price = safe_eval(get_param("purchase.update_list_price", "False"))
        if not change_list_price:
            return
        AccountTax = self.env["account.tax"]

        currency = self.env.user.company_id.currency_id
        company = self.env.user.company_id
        date = self._context.get("date") or fields.Date.today()

        for product in self:
            if product.trade_markup:
                if not product.last_purchase_price:
                    product.last_purchase_price = product.standard_price
                if not product.trade_markup:
                    list_price = AccountTax._fix_tax_included_price_company(
                        product.list_price,
                        product.taxes_id,
                        AccountTax,
                        product.company_id,
                    )
                    if product.last_purchase_price:
                        trade_markup = (list_price - product.last_purchase_price) / product.last_purchase_price * 100
                        product.trade_markup = trade_markup
                list_price = product.last_purchase_price * (1 + product.trade_markup / 100)
                list_price_tax = 0
                if product.taxes_id.price_include:
                    list_price_tax = product.taxes_id.with_context(force_price_include=False)._compute_amount(
                        list_price, 1
                    )
                list_price = list_price + list_price_tax

                list_price = currency._convert(list_price, product.currency_id, company, date)
                list_price_round = safe_eval(get_param("sale.list_price_round", "2"))
                product.list_price = round(list_price, list_price_round)


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    def update_last_purchase_price(self):
        date = self._context.get("date") or fields.Date.today()
        for item in self:
            from_uom = item.product_uom or item.product_tmpl_id.uom_id
            to_uom = item.product_tmpl_id.uom_id
            if not from_uom or not to_uom:
                raise UserError(
                    _("You cannot update the supplier price here. Please edit the supplier info separately")
                )
            price = from_uom._compute_price(item.price, to_uom)

            if item.currency_id:
                to_currency = self.env.user.company_id.currency_id
                company = self.env.user.company_id
                price = item.currency_id._convert(price, to_currency, company, date)
            if price:
                item.product_tmpl_id.last_purchase_price = price
                item.product_tmpl_id.onchange_last_purchase_price()

    def write(self, vals):
        res = super().write(vals)
        if "price" in vals:
            if not self.env.context.get("from_po_confirmation"):
                self.update_last_purchase_price()
        return res

    def create(self, vals_list):
        res = super().create(vals_list)
        if not self.env.context.get("from_po_confirmation"):
            res.update_last_purchase_price()
        return res
