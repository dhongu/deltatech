# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    raw_product_id = fields.Many2one('product.product', string='Raw product', store=True, index=True,
                                     compute='_compute_raw_product_id')



    @api.depends('bom_id')
    @api.multi
    def _compute_raw_product_id(self):
        productions = self.filtered(lambda x: x.bom_id is not False)
        for production in productions:
            production.raw_product_id = production.bom_id.bom_line_ids[0].product_id




