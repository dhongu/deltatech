# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(selection_add=[
        ('list_price_bronze', 'Bronze Price'),
        ('list_price_silver', 'Silver Price'),
        ('list_price_gold', 'Gold Price'),
        ('list_price_platinum', 'Platinum Price'),
    ])


class product_template(models.Model):
    _inherit = 'product.template'

    list_price_base = fields.Selection([('list_price', 'List price'), ('standard_price', 'Cost Price')],
                                       string='Base Price', default="standard_price")

    percent_bronze = fields.Float(string="Bronze Percent")
    percent_silver = fields.Float(string="Silver Percent")
    percent_gold = fields.Float(string="Gold Percent")
    percent_platinum = fields.Float(string="Platinum Percent")

    # todo: de adus valorile din listele de preturi
    list_price_bronze = fields.Float(string="Bronze Price", compute="_compute_price_list", store=True, readonly=True,
                                     compute_sudo=True)
    list_price_silver = fields.Float(string="Silver Price", compute="_compute_price_list", store=True, readonly=True,
                                     compute_sudo=True)
    list_price_gold = fields.Float(string="Gold Price", compute="_compute_price_list", store=True, readonly=True,
                                   compute_sudo=True)
    list_price_platinum = fields.Float(string="Platinum Price", compute="_compute_price_list", store=True, readonly=True,
                                       compute_sudo=True)

    @api.multi
    @api.depends('list_price_base', 'standard_price', 'list_price', 'percent_bronze', 'percent_silver', 'percent_gold',
                 'taxes_id')
    def _compute_price_list(self):

        for product in self:

            if not product.percent_bronze and not product.percent_silver and not product.percent_gold and not product.percent_platinum:
                return
            tax_inc = False
            # de regula este o singura  taxa
            taxe = product.taxes_id.sudo()

            for tax in taxe:
                if tax.price_include:
                    tax_inc = True

            # se presupune ca pretul de achizitie este cu taxa inclusa
            if product.list_price_base == 'standard_price':
                try:
                    price = product.standard_price
                except:
                    price = product.sudo().standard_price
                #taxe = taxe.with_context(base_values=price)
            else:
                price = product.list_price
                if tax_inc:
                    taxes = taxe.compute_all(product.list_price)
                    price = taxes['total_excluded']

            if tax_inc:
                tax_value = 0.0
                for tax in taxe.sorted(key=lambda r: r.sequence):
                    tax_value += price * tax.amount / 100
                price += tax_value
                price = round(price, 2)

            product.list_price_bronze = price * (1 + product.percent_bronze)
            product.list_price_silver = price * (1 + product.percent_silver)
            product.list_price_gold = price * (1 + product.percent_gold)
            product.list_price_platinum = price * (1 + product.percent_platinum)
