# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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



from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import models, fields, api, _, tools
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta



class crm_claim(models.Model):
    _inherit = "crm.claim"
    
    
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string='Quantity rejected', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    quantity_claimed = fields.Float(string='Quantity claimed', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    value = fields.Float(string='Amount', digits=dp.get_precision('Account'), store=True, compute='_compute_value') 
    
    user_ids = fields.Many2many('res.users', 'crm_claim_team_rel', 'claim_id', 'user_id', string='Team')
    
    action_containment_ids = fields.One2many('crm.claim.action', 'claim_id', string="Containment actions", domain=[('type', '=', 'containment')])
    action_corrective_ids = fields.One2many('crm.claim.action', 'claim_id', string="Permanent Corrective actions", domain=[('type', '=', 'corrective')])
    action_verification_ids = fields.One2many('crm.claim.action', 'claim_id', string="Effectiveness verification", domain=[('type', '=', 'verification')])
    action_preventive_ids = fields.One2many('crm.claim.action', 'claim_id', string="Preventive actions", domain=[('type', '=', 'preventive')])

    action_ids = fields.One2many('crm.claim.action', 'claim_id', string="Actions")

    loc_detected = fields.Many2one("crm.claim.loc.detected", string="Detected in")
    comments = fields.Text(string="Comments")

    date_closed = fields.Datetime(readonly=False)
    closed_by_user_id = fields.Many2one('res.users', string="Closed by", track_visibility='onchange')
    

    # am incercat sa redefinesc cumpurile originale dar nu am mers
    date_action_next_comp = fields.Date(string="Next Action Date", compute="_compute_action_next", store=False)
    action_next_comp = fields.Char(string="Next Action", compute="_compute_action_next", store=False)
    
    # costs fields
    costs_management = fields.Float(string='Cost of complaints management', digits=dp.get_precision('Account'), store=True)
    costs_selection = fields.Float(string='Selection costs', digits=dp.get_precision('Account'), store=True)
    costs_logistic = fields.Float(string='Logistic costs', digits=dp.get_precision('Account'), store=True)
    costs_other = fields.Float(string='Other costs', digits=dp.get_precision('Account'), store=True)
    costs_total = fields.Float(string='Total costs', digits=dp.get_precision('Account'), store=True, readonly=True, compute='_compute_costs')
    user_uid = fields.Many2one('res.users', string="uid", compute = '_get_uid') 
    is_same_user = fields.Boolean(compute = '_is_same_user')
    
    def _is_same_user(self):
        if self.user_id == self.user_uid:
            self.is_same_user = True
        else:
            self.is_same_user = False
    
    def _get_uid(self):
        self.user_uid = self.env.user.id
    

    @api.one
    @api.depends('product_id', 'quantity')
    def _compute_value(self):
        self.value = self.quantity * self.product_id.lst_price
        
    @api.one
    @api.depends('costs_management', 'costs_selection', 'costs_logistic', 'costs_other')
    def _compute_costs(self):
        self.costs_total = self.costs_management + self.costs_selection + self.costs_logistic + self.costs_other


    @api.multi
    @api.depends('action_ids')
    def _compute_action_next(self):
        for claim in self:
            # actions = self.env['crm.claim.action'].search(['claim_id','=',claim.id])yyyy-mm-dd
            # print actions
            for action in claim.action_ids:
                if action.date_deadline > fields.Date.today() and (action.date_deadline < claim.date_action_next_comp or not claim.date_action_next_comp):
                     claim.date_action_next_comp = action.date_deadline
                     claim.action_next_comp = action.name



class crm_claim_action(models.Model):
    _name = "crm.claim.action"
    _description = "CRM Claim Action"
    _order = "date_deadline" 

    claim_id = fields.Many2one('crm.claim', string='Claim', required=True, index=True)
    type = fields.Selection([('containment', 'Containment'), ('corrective', 'Corrective'),
                             ('verification', 'Verification'), ('preventive', 'Preventive')], string="Type")
    name = fields.Char(string="Action", required=True) 
    user_id = fields.Many2one('res.users', 'Responsible', track_visibility='always')
    date_deadline = fields.Date(string='Deadline')
    
    state = fields.Selection([
            ('draft', 'Undone'),
            ('open', 'In Progress'),
            ('done', 'Done'),
        ], string='Status', index=True, default='draft', copy=False)    
    
    
class crm_claim_loc_detected(models.Model):
    _name = "crm.claim.loc.detected"
    _description = "CRM Location Detected"  
    
    name = fields.Char(string="Detected", required=True, translate=True)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: