# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import   UserError, RedirectWarning




# class ProductProduct(models.Model):
#     _inherit = 'product.product'
#
#
#     @api.multi
#     def price_compute(self, price_type, uom=False, currency=False, company=False):
#
#         if not currency and self._context.get('currency'):
#             currency = self.env['res.currency'].browse(self._context['currency'])
#
#         products = self.with_context(currency=False)
#         prices = super(ProductProduct, products).price_compute(price_type, uom, currency=False,  company=company)
#         if price_type == 'list_price':  # doar pretul pubilc poate fi in euro !
#             for product in self:
#                 prices[product.id] = product.price_currency_id.compute(prices[product.id], currency or product.currency_id, round=False)
#
#         return prices
