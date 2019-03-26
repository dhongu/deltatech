# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp


class product_template(models.Model):
    _inherit = 'product.template'

    list_price_base = fields.Selection([('list_price', 'List price'), ('standard_price', 'Cost Price')],
                                       string='Base Price', default="standard_price")

    percent_bronze = fields.Float(string="Bronze Percent")
    percent_silver = fields.Float(string="Silver Percent")
    percent_gold = fields.Float(string="Gold Percent")
    percent_platinum = fields.Float(string="Platinum Percent")

    list_price_bronze = fields.Float(string="Bronze Price", compute="_compute_price", store=True, readonly=True,
                                     compute_sudo=True)
    list_price_silver = fields.Float(string="Silver Price", compute="_compute_price", store=True, readonly=True,
                                     compute_sudo=True)
    list_price_gold = fields.Float(string="Gold Price", compute="_compute_price", store=True, readonly=True,
                                   compute_sudo=True)
    list_price_platinum = fields.Float(string="Platinum Price", compute="_compute_price", store=True, readonly=True,
                                       compute_sudo=True)

    @api.multi
    @api.depends('list_price_base', 'standard_price', 'list_price', 'percent_bronze', 'percent_silver', 'percent_gold',
                 'taxes_id')
    def _compute_price(self):
        for product in self:

            tax_inc = False

            taxe = product.taxes_id.sudo()

            for tax in taxe:
                if tax.price_include:
                    tax_inc = True

            if product.list_price_base == 'standard_price':
                try:
                    price = product.standard_price
                except:
                    price = product.sudo().standard_price
            else:
                price = product.list_price
                if tax_inc:
                    taxes = taxe.compute_all(product.list_price, 1)
                    price = taxes['total']

            product.list_price_bronze = price * (1 + product.percent_bronze)
            product.list_price_silver = price * (1 + product.percent_silver)
            product.list_price_gold = price * (1 + product.percent_gold)
            product.list_price_platinum = price * (1 + product.percent_platinum)

            if tax_inc:
                taxes = taxe.compute_all(product.list_price_bronze, 1, force_excluded=True)
                product.list_price_bronze = taxes['total_included']
                taxes = taxe.compute_all(product.list_price_silver, 1, force_excluded=True)
                product.list_price_silver = taxes['total_included']
                taxes = taxe.compute_all(product.list_price_gold, 1, force_excluded=True)
                product.list_price_gold = taxes['total_included']
                taxes = taxe.compute_all(product.list_price_platinum, 1, force_excluded=True)
                product.list_price_platinum = taxes['total_included']
