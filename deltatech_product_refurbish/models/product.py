# -*- coding: utf-8 -*-
# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models, fields, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    has_refurbish = fields.Boolean(compute='_get_refurbish')
    refurbish_ids = fields.Many2many('stock.production.lot', compute='_get_refurbish')

    def _get_refurbish(self):
        domain_loc = self.env['product.product']._get_domain_locations()[0]

        for product in self:
            refurbish_ids = self.env['stock.production.lot']
            domain = domain_loc + [('product_id', 'in', product.product_variant_ids.ids)]
            quants = self.env['stock.quant'].search(domain)
            for quant in quants:
                if quant.lot_id.condition == 'refurbish' and not quant.reserved_quantity:
                    refurbish_ids |= quant.lot_id
            product.refurbish_ids = refurbish_ids
            product.has_refurbish = bool(refurbish_ids)
