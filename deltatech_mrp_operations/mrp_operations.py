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

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.tools import float_is_zero
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




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: