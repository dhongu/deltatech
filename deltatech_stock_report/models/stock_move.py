# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


class stock_move(models.Model):
    _inherit = 'stock.move'

    qty_sing = fields.Float(string="Quantity with Sing", compute='_compute_qty_sing', store=True)


    @api.depends('product_qty','location_id','location_dest_id')
    @api.multi
    def _compute_qty_sing(self):
        for move in self:
            coef = 0.0
            if move.location_id.usage != move.location_dest_id.usage:
                if move.location_id.usage == 'internal':
                    coef = -1.0
                elif move.location_dest_id.usage == 'internal':
                    coef = 1.0
            move.qty_sing = move.product_qty * coef