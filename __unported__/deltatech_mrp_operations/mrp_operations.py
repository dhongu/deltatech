# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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
import odoo.addons.decimal_precision as dp
from odoo import tools
import logging

_logger = logging.getLogger(__name__)



    

class mrp_production_workcenter_line(models.Model):
    _inherit = 'mrp.production.workcenter.line'


    #possible_partner_ids = fields.Many2many('res.partner', compute='_get_possible_partner_ids', readonly=True)
    
    partner_id = fields.Many2one('res.partner',string="Operator", domain="[('id', 'in', possible_partner_ids[0][2])]")
    
    possible_partner_ids = fields.Many2many('res.partner', compute='_get_possible_partner_ids', readonly=True)

    amount = fields.Float(string="Amount",compute='_get_amount')
    
    @api.one
    def _get_amount(self):    
        self.amount = self.hour * self.workcenter_id.costs_hour

    @api.multi
    def action_start_working(self):
        super(mrp_production_workcenter_line,self).action_start_working()
        for work in self:
            if not work.partner_id:
                if len(work.possible_partner_ids)==1:
                    partner_id = work.possible_partner_ids[0]
                    work.write({'partner_id':partner_id.id})
        return True


    @api.one
    def _get_possible_partner_ids(self):
        partners = self.env['res.partner']
        for operator in self.workcenter_id.operator_ids:
            if operator.from_date <= fields.Date.today() <= operator.to_date:
                partners |= operator.partner_id 
        self.possible_partner_ids = partners  

class mrp_workorder(models.Model):
    _inherit = "mrp.workorder"

    partner_id = fields.Many2one('res.partner',string="Operator")
    total_cost = fields.Float( string="Total Cost")

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'mrp_workorder')
        cr.execute("""
            create or replace view mrp_workorder as (
                select
                    date(wl.date_planned) as date,
                    min(wl.id) as id,
                    mp.product_id as product_id,
                    wl.partner_id as partner_id,
                    sum(wl.hour) as total_hours,
                    avg(wl.delay) as delay,
                    (w.costs_hour*sum(wl.hour)) as total_cost,
                    wl.production_id as production_id,
                    wl.workcenter_id as workcenter_id,
                    sum(wl.cycle) as total_cycles,
                    count(*) as nbr,
                    sum(mp.product_qty) as product_qty,
                    wl.state as state
                from mrp_production_workcenter_line wl
                    left join mrp_workcenter w on (w.id = wl.workcenter_id)
                    left join mrp_production mp on (mp.id = wl.production_id)
                group by
                    w.costs_hour, mp.product_id, wl.partner_id, mp.name, wl.state, wl.date_planned, wl.production_id, wl.workcenter_id
        )""")



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: