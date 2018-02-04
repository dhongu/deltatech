# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2014 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from odoo import tools


class product_category(models.Model):
    _inherit = 'product.category'
    cost_categ = fields.Selection([('raw', 'Raw materials'),
                                   ('semi', 'Semi-products'),
                                   ('pak', 'Packing Material'),
                                   ], string='Cost Category')


class deltatech_mrp_cost_detail(models.Model):
    _name = 'deltatech.mrp.cost.detail'
    _description = "Cost Detail"
    _auto = False
    production_id = fields.Many2one('mrp.production', string='Production Order')
    cost_categ = fields.Selection([('raw', 'Raw materials'),
                                   ('semi', 'Semi-products'),
                                   ('pak', 'Packing Material'),
                                   ], string='Cost Category')
    amount = fields.Float(string='Amount', digits=dp.get_precision('Account'))

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'deltatech_mrp_cost_detail')
        self.env.cr.execute("""
            create or replace view deltatech_mrp_cost_detail as (
 
SELECT sm.raw_material_production_id AS id,
    sm.raw_material_production_id AS production_id,
    SUM (q.qty * q. COST) AS amount,
    pc.cost_categ
FROM
    stock_move sm
    LEFT JOIN stock_quant_move_rel ON stock_quant_move_rel.move_id = sm.id
    LEFT JOIN stock_quant q ON stock_quant_move_rel.quant_id = q.id
    LEFT JOIN product_product pr ON pr. ID = sm.product_id
    LEFT JOIN product_template pt ON pt. ID = pr.product_tmpl_id
    LEFT JOIN product_category pc ON pc. ID = pt.categ_id
WHERE
    q.qty > 0
    AND raw_material_production_id IS NOT NULL

    AND sm.state = 'done' :: TEXT
GROUP BY
    sm.raw_material_production_id, pc.cost_categ
 
  )""")


class mrp_production(models.Model):
    _inherit = 'mrp.production'
    cost_detail_ids = fields.One2many('deltatech.mrp.cost.detail', 'production_id', compute="_compute_cost_detail")

    @api.one
    @api.depends('move_raw_ids')
    def _compute_cost_detail(self):
        cost = {}
        for move in self.move_raw_ids:
            cost_categ = move.product_id.categ_id.cost_categ
            amount = 0.0
            for quant in move.quant_ids:
                if quant.qty > 0:
                    amount += quant.cost * quant.qty
            cost[cost_categ] = cost.get(cost_categ, 0) + amount

        cost_detail_ids = self.env['deltatech.mrp.cost.detail']
        for cost_categ, amount in cost.items():
            values = {'production_id': self.id, 'cost_categ': cost_categ, 'amount': amount}
            cost_detail_ids = cost_detail_ids + cost_detail_ids.new(values)
        self.cost_detail_ids = cost_detail_ids

    '''
    ca sa functioneze treaba asta am modificat metoda din fields:
    
    def convert_to_read(self, value, use_name_get=True):
        if all(value._ids):
            return value.ids
        else:
            # this is useful for computed fields that use new records as values
            return self.convert_to_write(value)
    '''
