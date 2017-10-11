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
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
import math
from dateutil.relativedelta import relativedelta
from datetime import date, datetime




class service_equipment(models.Model):
    _inherit = 'service.equipment'

    
    plan_ids = fields.One2many('service.plan', 'equipment_id', string='Plans' ) 
    
    # canda a fost facuta ultima revizie ? si trebuie putin modificata
    last_call_done  = fields.Date(string="Last call done", compute="_compute_last_call_done")



    @api.one
    def _compute_last_call_done(self):
        plans = self.env['service.plan'].search([('equipment_id','=',self.id),('state','=','active')])
        if plans:
            calls = self.env['service.plan.call'].search([('plan_id','in',plans.ids),('state','=','completion')],order='completion_date DESC', limit=1)
            if calls:
                self.last_call_done = calls.completion_date



    @api.multi
    def notification_button(self):
        notifications = self.env['service.notification'].search([('equipment_id','in',self.ids)])
        context = {
                    'default_equipment_id':self.id,
                    'default_partner_id':self.partner_id.id,
                    'default_agreement_id':self.agreement_id.id,
                    'default_address_id':self.address_id.id,
                    'default_contact_id':self.contact_id.id,
                   }    
        return {
            'domain': "[('id','in', ["+','.join(map(str,notifications.ids))+"])]",
            'name': _('Notifications'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'service.notification',
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window'
        }       


    @api.multi
    def order_button(self):
        orders = self.env['service.order'].search([('equipment_id','in',self.ids)])
        context = {
                    'default_equipment_id':self.id,
                    'default_partner_id':self.partner_id.id,
                    'default_agreement_id':self.agreement_id.id,
                    'default_address_id':self.address_id.id,
                    'default_contact_id':self.contact_id.id,
                   }     
        return {
            'domain': "[('id','in', ["+','.join(map(str,orders.ids))+"])]",
            'name': _('Orders'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'service.order',
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window'
        }  


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
