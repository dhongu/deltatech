# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, api, models


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    standard_price = fields.Float(track_visibility='always')

    @api.one
    @api.depends('property_cost_method', 'categ_id.property_cost_method')
    def _compute_cost_method(self):
        super(ProductTemplate, self)._compute_cost_method()
        if self.cost_method == 'fifo' and self.env.context.get('force_fifo_to_average', False):
            self.cost_method = 'average'


    @api.multi
    def update_standard_price(self):
        self.seller_ids.update_standard_price()

class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    @api.multi
    def update_standard_price(self):
        for item in self:
            price = item.product_uom._compute_price(item.price, item.product_tmpl_id.uom_id)
            if item.currency_id:
                price = item.currency_id.compute(price,   self.env.user.company_id.currency_id)
            item.product_tmpl_id.write({'standard_price': price})
            break
