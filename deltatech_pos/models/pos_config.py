# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    ecr_type = fields.Selection([('datecs18',"Datecs 2018"),('optima','Optima')], default='datecs18')
    file_prefix = fields.Char(string='File prefix', default='order')
    file_ext = fields.Char(string='File extension', default='inp')


    quantity = fields.Float(compute='_compute_quantity')



    @api.multi
    def _compute_quantity(self):
        for config in self:
            qty =  0.0
            stock_location_id = config.stock_location_id
            quants = self.env['stock.quant'].search([('location_id','=',config.stock_location_id.id)])
            for quant in quants:
                qty += quant.quantity
            config.quantity = qty


    @api.multi
    def open_stock(self):
        self.ensure_one()
        action = self.env.ref('product.product_template_action').read()[0]
        action['context'] = {'location':self.stock_location_id.id,'search_default_real_stock_available':1}
        return action