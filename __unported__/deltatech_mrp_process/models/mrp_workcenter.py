# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    location_id = fields.Many2one('stock.location', string='Tank', domain="[('usage','=','internal')]")
    product_id = fields.Many2one('product.product', compute='_compute_quantity')
    quantity = fields.Float(string='Quantity', compute='_compute_quantity')
    max_quantity = fields.Float(string='Max Quantity')


    cleaning_date = fields.Date()
    cleaning_note = fields.Text()


    @api.multi
    def _compute_quantity(self):
        for workcenter in self:
            qty = 0.0
            location_id = workcenter.location_id
            products = self.env['product.product']
            quants = self.env['stock.quant'].search([('location_id', '=', location_id.id)])
            for quant in quants:
                qty += quant.quantity
                products |= quant.product_id

            workcenter.quantity = qty

            if len(products) == 1:
                workcenter.product_id = products
            else:
                workcenter.product_id = False

    @api.multi
    def show_stock(self):
        if self.location_id:
            action = self.env.ref('stock.location_open_quants').read()[0]
            action['domain'] = [('location_id', '=', self.location_id.id)]
            return action
