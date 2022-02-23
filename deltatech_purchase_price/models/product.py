# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.tools import safe_eval

from odoo.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(track_visibility="always")

    @api.onchange("last_purchase_price", "trade_markup")
    def onchange_last_purchase_price(self):
        self.product_tmpl_id.onchange_last_purchase_price()


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(track_visibility="always")
    list_price = fields.Float(track_visibility="always")
    last_purchase_price = fields.Float(digits=dp.get_precision("Product Price"), track_visibility="always")
    trade_markup = fields.Float(string="Trade Markup", track_visibility="always")

    @api.onchange("list_price")
    def onchange_list_price(self):
        AccountTax = self.env["account.tax"]
        list_price = AccountTax._fix_tax_included_price_company(
            self.list_price, self.taxes_id, AccountTax, self.company_id
        )
        if self.last_purchase_price:
            trade_markup = (list_price - self.last_purchase_price) / self.last_purchase_price * 100
            self.trade_markup = trade_markup

    @api.one
    @api.depends("property_cost_method", "categ_id.property_cost_method")
    def _compute_cost_method(self):
        super(ProductTemplate, self)._compute_cost_method()
        if self.cost_method == "fifo" and self.env.context.get("force_fifo_to_average", False):
            self.cost_method = "average"

    @api.onchange("last_purchase_price", "trade_markup")
    def onchange_last_purchase_price(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        change_list_price = safe_eval(get_param("purchase.update_list_price", "True"))
        if change_list_price:
            AccountTax = self.env["account.tax"]
            for product in self:
                if not product.last_purchase_price:
                    product.last_purchase_price = product.standard_price
                if not product.trade_markup or product.trade_markup < 0:
                    list_price = AccountTax._fix_tax_included_price_company(
                        product.list_price, product.taxes_id, AccountTax, product.company_id
                    )
                    if product.last_purchase_price:
                        trade_markup = (list_price - product.last_purchase_price) / product.last_purchase_price * 100
                        product.trade_markup = trade_markup
                list_price = product.last_purchase_price * (1 + product.trade_markup / 100)
                list_price_tax = 0
                if product.taxes_id.price_include:
                    list_price_tax = product.taxes_id.with_context(handle_price_include=False)._compute_amount(
                        list_price, 1
                    )
                list_price = list_price + list_price_tax
                list_price = self.env.user.company_id.currency_id.compute(list_price, product.currency_id)
                product.list_price = round(list_price, 0)


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    def update_last_purchase_price(self):
        for item in self:
            price = item.product_uom._compute_price(item.price, item.product_tmpl_id.uom_id)
            if item.currency_id:
                price = item.currency_id.compute(price, self.env.user.company_id.currency_id)
            if price:
                item.product_tmpl_id.last_purchase_price = price
                item.product_tmpl_id.onchange_last_purchase_price()

    @api.multi
    def write(self, vals):
        res = super(SupplierInfo, self).write(vals)
        if "price" in vals:
            self.update_last_purchase_price()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(SupplierInfo, self).create(vals_list)
        res.update_last_purchase_price()
        return res
