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


class mrp_workcenter(models.Model):
    _inherit = 'mrp.workcenter'
    
    operator_ids = fields.One2many('mrp.workcenter.operator','workcenter_id', string='Operators')  
    
 
    
class mrp_workcenter_operator(models.Model):
    _name = 'mrp.workcenter.operator'
    _description = 'Work Center Operator' 
    _order = "to_date DESC"  
    
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', required=True)
    partner_id = fields.Many2one('res.partner',string="Operator")
    from_date = fields.Date(string="Form Date", default=lambda * a:fields.Date.today())
    to_date   = fields.Date(string="To Date", default='2999-12-31')
    



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: