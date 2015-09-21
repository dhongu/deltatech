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


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


# sesizari primite din partea clientilor

# todo: de  definit in configurare o adresa in care se introduc sesizarile de service 
# la creare se incearca o determinare a echipamentului  

AVAILABLE_PRIORITIES = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
]


class service_notification(models.Model):
    _name = 'service.notification'
    _description = "Notification"
    _inherit = ['mail.thread', 'ir.needaction_mixin'] 

    def compute_default_user_id(self):
        return self.env.user.id


    name = fields.Char(string='Reference', readonly=True, default='/')    
    date = fields.Date(string='Date', default=fields.Date.today() , readonly=True, states={'new': [('readonly', False)]})
    
    state = fields.Selection([  ('new','New'), 
                                ('assigned','Assigned'),
                                ('progress','In Progress'), 
                                ('done','Done')], default='new', string='Status',  track_visibility='always')

    equipment_history_id = fields.Many2one('service.equipment.history', string='Equipment history')         
    equipment_id = fields.Many2one('service.equipment', string='Equipment',index=True , readonly=True, states={'new': [('readonly', False)]})
 
    partner_id = fields.Many2one('res.partner', string='Partner', related='equipment_history_id.partner_id', readonly=True)
    address_id = fields.Many2one('res.partner', string='Location',   related='equipment_history_id.address_id', readonly=True)
    emplacement = fields.Char(string='Emplacement', related='equipment_history_id.emplacement', readonly=True)
    agreement_id = fields.Many2one('service.agreement', string='Service Agreement', related='equipment_history_id.agreement_id',readonly=True)        
  
    contact_id = fields.Many2one('res.partner', string='Reported by',help='The person who reported the notification', readonly=True, states={'new': [('readonly', False)]})

    user_id = fields.Many2one('res.users', string='Responsible', readonly=True, states={'new': [('readonly', False)]})
    
    type =  fields.Selection([ ('external','External'), ('internal','Internal')], default='external', string='Type' , readonly=True, states={'new': [('readonly', False)]})   
    
    subject = fields.Char('Subject', readonly=True, states={'new': [('readonly', False)]})
    description = fields.Text('Notes', readonly=True, states={'new': [('readonly', False)]})
    
    date_assing = fields.Datetime('Assigning Date', readonly=True, copy=False)
    date_start = fields.Datetime('Start Date', readonly=True, copy=False)
    date_done = fields.Datetime('Done Date', readonly=True, copy=False)
    
    
    priority =  fields.Selection(AVAILABLE_PRIORITIES, string='Priority', select=True, readonly=True, states={'new': [('readonly', False)]})  
    color =  fields.Integer(string='Color Index', default=0)  
    order_id = fields.Many2one('service.order', string='Order', readonly=True, copy=False, compute='_compute_order_id' )    
    piking_id = fields.Many2one('stock.picking', string="Consumables")  # legatua cu necesarul / consumul de consumabile



    @api.model
    def company_user(self, present_ids, domain, **kwargs):
        partner_id = self.env.user.company_id.partner_id
        users = self.env['res.users'].search([('partner_id.parent_id','=',partner_id.id)])         
        users_name = users.name_get()
        users_name.append((False,False)) 
        return users_name, None
        
    _group_by_full = {
        'user_id': company_user,
    }
    

    @api.one
    def _compute_order_id(self ):
        self.order_id = self.env['service.order'].search([('notification_id','=',self.id)], limit=1)
    

    @api.onchange('equipment_id','date')
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.equipment_history_id = self.equipment_id.get_history_id(self.date)        
            self.user_id =  self.equipment_id.user_id
        else: 
            self.equipment_history_id = False     
                
            

    @api.model
    def create(self,   vals ):  

        equipment_id = vals.get('equipment_id',False)
        
        if not equipment_id:
            equipments = self.env['service.equipment']
            contact_id = vals.get('contact_id',False)
            if contact_id:
                equipments = self.env['service.equipment'].search([('contact_id','=',contact_id)])  
           
            description = vals.get('description',False)
            
            if description and ( len(equipments) != 1 ):   
                keywords = description.split()
                equipments_by_ean = self.env['service.equipment']
                for keyword in keywords:
                    equipments_by_ean |= self.env['service.equipment'].search([('ean_code','=',keyword)])
                
                if len(equipments) == 0:
                    equipments = equipments_by_ean
                else:
                    equipments &= equipments_by_ean
                
        
            if len(equipments) == 1:
                 vals['equipment_id'] = equipments.id
                 if not vals.get('address_id',False):
                     vals['address_id'] = equipments.address_id.id
                 if not vals.get('user_id',False):
                     vals['user_id'] = equipments.user_id.id
                 if not vals.get('agreement_id',False):
                     vals['agreement_id'] = equipments.agreement_id.id
                 if not vals.get('partner_id',False):
                     vals['partner_id'] = equipments.agreement_id.partner_id.id                     

        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            sequence_notification = self.env.ref('deltatech_service_maintenance.sequence_notification')
            if sequence_notification:
                vals['name'] = self.env['ir.sequence'].next_by_id(sequence_notification.id)                     
        return super(service_notification, self).create( vals )


    @api.multi
    def write(self, vals):
        if 'user_id' in vals:
            if  self.state != 'new': 
                raise Warning(_('Notification is assigned.'))
        result = super(service_notification, self).write(vals)
        return result 

    @api.multi
    def action_cancel_assing(self):
        if  self.state != 'assigned': 
            raise Warning(_('Notification is not assigned.'))
        self.write({'state':'new',
            'date_assing':fields.Datetime.now()})
         
    @api.multi
    def action_assing(self):
        if not self.user_id:
            raise Warning(_('Please select a responsible.')) 
        if self.state != 'new': 
            raise Warning(_('Notification is already assigned.')) 
                
        self.write({'state':'assigned',
                    'date_assing':fields.Datetime.now()})

        new_follower_ids = [self.user_id.partner_id.id]
        if self.user_id <> self.env.user.id:
            msg = _('Please solve notification: %s') % (self.description or '')
       
            if msg and not self.env.context.get('no_message',False):
                document = self
                message = self.env['mail.message'].with_context({'default_starred':True}).create({
                    'model': 'service.notification',
                    'res_id': document.id,
                    'record_name': document.name_get()[0][1],
                    'email_from': self.env['mail.message']._get_default_from( ),
                    'reply_to': self.env['mail.message']._get_default_from( ),

                    'subject': self.subject,
                    'body': msg,
                     
                    'message_id': self.env['mail.message']._get_message_id(  {'no_auto_thread': True} ),
                    'partner_ids': [(4, id) for id in new_follower_ids],
                     
                })


    @api.multi
    def action_taking(self):
        if self.state != 'new': 
            raise Warning(_('Notification is already assigned.'))
        self.message_mark_as_read() 
        self.write({'state':'assigned',
                    'date_assing':fields.Datetime.now(),
                    'user_id':self.env.user.id})

    @api.multi
    def action_start(self):
        self.message_mark_as_read()
        self.write({'state':'progress',
                    'date_start':fields.Datetime.now()})
        

    @api.multi
    def action_order(self):
        context = { 'default_notification_id':self.id,
                    'default_equipment_id':self.equipment_id.id,
                    'default_partner_id':self.partner_id.id,
                    'default_agreement_id':self.agreement_id.id,
                    'default_address_id':self.address_id.id,
                    'default_contact_id':self.contact_id.id,
                   }
        
        if self.order_id:
            domain =  "[('id','=', "+str(self.order_id.id)+")]" 
            res_id = self.order_id.id
        else: 
            domain = '[]'
            res_id = False
        print domain
        return {
            'domain': domain,
            'res_id': res_id,
            'name': _('Services Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'service.order',
            'context': context,
            'type': 'ir.actions.act_window'
        }


       
            
    @api.multi
    def action_done(self):
        self.write({'state':'done',
                    'date_done':fields.Datetime.now()})


    #TODO: De anuntat utilizatorul ca are o sesizare 
    
    
class service_notification_type(models.Model):
    _name = 'service.notification.type'
    _description = "Service Notification Type"     
    name = fields.Char(string='Type', translate=True)      
    
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
