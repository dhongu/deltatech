# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = "product.template"

    list_price = fields.Float(tracking=True)
    last_purchase_price = fields.Float(digits="Product Price", tracking=True)
    trade_markup = fields.Float(string="Trade Markup", tracking=True)

    @api.depends("property_cost_method", "categ_id.property_cost_method")
    def _compute_cost_method(self):
        super(ProductTemplate, self)._compute_cost_method()
        if self.cost_method == "fifo" and self.env.context.get("force_fifo_to_average", False):
            self.cost_method = "average"

    @api.onchange("last_purchase_price", "trade_markup")
    def onchange_last_purchase_price(self):
        AccountTax = self.env["account.tax"]
        for product in self:
            if not product.last_purchase_price:
                product.last_purchase_price = product.standard_price
            if not product.trade_markup:
                list_price = AccountTax._fix_tax_included_price_company(
                    product.list_price, product.taxes_id, AccountTax, product.company_id
                )
                trade_markup = (list_price - product.last_purchase_price) / product.last_purchase_price * 100
                product.trade_markup = trade_markup
            list_price = product.last_purchase_price * (1 + product.trade_markup / 100)
            list_price_tax = 0
            if product.taxes_id.price_include:
                list_price_tax = product.taxes_id.with_context(force_price_include=False)._compute_amount(list_price, 1)
            product.list_price = list_price + list_price_tax
