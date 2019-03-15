# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group')
    raw_product_id = fields.Many2one('product.product', string='Raw product', store=True,
                                     related='production_id.raw_product_id')

    @api.model
    def create(self, vals):
        if 'procurement_group_id' not in vals and 'production_id' in vals:
            production = self.env['mrp.production'].browse(vals['production_id'])
            vals['procurement_group_id'] = production.procurement_group_id.id
        return super(MrpWorkorder, self).create(vals)
