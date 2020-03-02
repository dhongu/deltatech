# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, models, fields, _, tools
import odoo.addons.decimal_precision as dp



class deltatech_cost_detail(models.Model):
    _name = 'deltatech.cost.detail'
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
        tools.drop_view_if_exists(self.env.cr, 'deltatech_cost_detail')
        self.env.cr.execute("""
            create or replace view deltatech_cost_detail as (

                SELECT max(sm.id) AS id,
                    sm.raw_material_production_id AS production_id,
                    SUM (sm.value) AS amount,
                    pc.cost_categ
                FROM
                    stock_move sm
                    LEFT JOIN product_product pr ON pr. ID = sm.product_id
                    LEFT JOIN product_template pt ON pt. ID = pr.product_tmpl_id
                    LEFT JOIN product_category pc ON pc. ID = pt.categ_id
                WHERE
                     raw_material_production_id IS NOT NULL
                     AND sm.state = 'done' :: TEXT
                GROUP BY
                    sm.raw_material_production_id, pc.cost_categ
        )"""
        )


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    cost_detail_ids = fields.One2many('deltatech.cost.detail', 'production_id', compute="_compute_cost_detail")

    @api.multi
    def recompute_cost_detail(self):
        for production in self:
            production._compute_cost_detail()



    @api.one
    @api.depends('move_raw_ids')
    def _compute_cost_detail(self):

        domain = [('production_id','=',self.id)]
        cost_detail_ids = self.env['deltatech.cost.detail'].search(domain)
        self.cost_detail_ids = cost_detail_ids
        # cost = {}
        # for move in self.move_raw_ids:
        #     cost_categ = move.product_id.categ_id.cost_categ
        #     cost[cost_categ] = cost.get(cost_categ, 0) + move.value
        #
        # cost_detail_ids = self.env['deltatech.cost.detail']
        # for cost_categ, amount in cost.items():
        #     values = {'production_id': self.id, 'cost_categ': cost_categ, 'amount': amount}
        #     cost_detail_ids = cost_detail_ids + cost_detail_ids.new(values)
        # self.cost_detail_ids = cost_detail_ids
        # self.write({'cost_detail_ids':self.cost_detail_ids})

    '''
    ca sa functioneze treaba asta am modificat metoda din fields:
    
    def convert_to_read(self, value, use_name_get=True):
        if all(value._ids):
            return value.ids
        else:
            # this is useful for computed fields that use new records as values
            return self.convert_to_write(value)
    '''
