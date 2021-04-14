# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    trade_markup = fields.Float(string="Trade Markup", compute="_compute_trade_markup", readonly=False, store=True)
    margin = fields.Float(string="Margin", compute="_compute_trade_markup", readonly=False, store=True)

    @api.depends("standard_price", "list_price")
    def _compute_trade_markup(self):
        AccountTax = self.env["account.tax"]
        for product in self:
            trade_markup = 100
            list_price = AccountTax._fix_tax_included_price_company(
                product.list_price, product.taxes_id, AccountTax, product.company_id
            )
            if product.standard_price:
                trade_markup = (list_price - product.standard_price) / product.standard_price * 100
            product.trade_markup = trade_markup
            margin = 0
            if list_price:
                margin = (list_price - product.standard_price) / list_price * 100
            product.margin = margin

    def set_inverse_trade_markup(self):

        for product in self:
            list_price = product.standard_price * (1 + product.trade_markup / 100)
            list_price_tax = 0
            if product.taxes_id.price_include:
                list_price_tax = product.taxes_id.with_context(force_price_include=False)._compute_amount(list_price, 1)
            product.list_price = list_price + list_price_tax

    def set_inverse_margin(self):

        for product in self:
            if product.margin != 100:
                list_price = product.standard_price / (1 - product.margin / 100)
                list_price_tax = 0
                if product.taxes_id.price_include:
                    list_price_tax = product.taxes_id.with_context(force_price_include=False)._compute_amount(
                        list_price, 1
                    )
                product.list_price = list_price + list_price_tax


class ProductProduct(models.Model):
    _inherit = "product.product"

    def set_inverse_trade_markup(self):
        for product in self:
            product.product_tmpl_id.set_inverse_trade_markup()

    def set_inverse_margin(self):
        for product in self:
            product.product_tmpl_id.set_inverse_margin()
