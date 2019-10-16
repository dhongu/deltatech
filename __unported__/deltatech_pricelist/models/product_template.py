# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'



    @api.multi
    def _compute_currency_id(self):
        main_company = self.env['res.company']._get_main_company()
        for template in self:
            template.currency_id = template.company_id.sudo().price_currency_id.id or main_company.price_currency_id.id

    # price_currency_id = fields.Many2one('res.currency', string='Price List Currency', compute='_compute_price_currency_id')
    #
    #
    # @api.multi
    # def _compute_price_currency_id(self):
    #     main_company = self.env['res.company']._get_main_company()
    #     for template in self:
    #         template.price_currency_id = template.company_id.sudo().price_currency_id.id or main_company.price_currency_id.id
    #
    # @api.multi
    # def price_compute(self, price_type, uom=False, currency=False, company=False):
    #
    #     if not currency and self._context.get('currency'):
    #         currency = self.env['res.currency'].browse(self._context['currency'])
    #
    #     templates = self.with_context(currency=False)
    #     prices = super(ProductTemplate, templates).price_compute(price_type, uom, currency=False,  company=company)
    #     if price_type in ['list_price', 'list_price']:  # pretul pubilc poate fi in euro !
    #         for template in self:
    #
    #             prices[template.id] = template.price_currency_id.compute(prices[template.id],  currency or template.currency_id, round=False)
    #
    #
    #     return prices
