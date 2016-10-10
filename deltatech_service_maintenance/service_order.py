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
import uuid

## raport de activitate
## nota de constatare

class service_order(models.Model):
    _name = 'service.order'
    _description = "Service Order"
    _inherit = 'mail.thread' 

    name = fields.Char(string='Reference', readonly=True, default='/')    
    date = fields.Date(string='Date', default=lambda * a:fields.Date.today(), readonly=True, states={'draft': [('readonly', False)]})

    access_token = fields.Char(string='Security Token', required=True, copy=False,default=str(uuid.uuid4()))
    
    state = fields.Selection([  ('draft','Draft'), 
                                ('progress','In Progress'), 
                                ('work_done','Work Done'),
                                ('rejected','Rejected'),
                                ('cancel','Cancel'),
                                ('done','Done')], default='draft', string='Status')

    date_start = fields.Datetime('Start Date', readonly=True, copy=False)
    date_done = fields.Datetime('Done Date', readonly=True, copy=False) 



    equipment_history_id = fields.Many2one('service.equipment.history', required=True, string='Equipment history')         
    equipment_id = fields.Many2one('service.equipment', string='Equipment',index=True , readonly=True, states={'draft': [('readonly', False)]})
 
    partner_id = fields.Many2one('res.partner', string='Partner', related='equipment_history_id.partner_id', readonly=True)
    address_id = fields.Many2one('res.partner', string='Location',   related='equipment_history_id.address_id', readonly=True)
    emplacement = fields.Char(string='Emplacement', related='equipment_history_id.emplacement', readonly=True)
    agreement_id = fields.Many2one('service.agreement', string='Service Agreement', related='equipment_history_id.agreement_id',readonly=True)     


    contact_id = fields.Many2one('res.partner', string='Contact person',  track_visibility='onchange')  
    
    city = fields.Char(string='City',related='address_id.city')  
   


    # raportul poate sa fie legat de o sesizre
    notification_id = fields.Many2one('service.notification', string='Notification', readonly=True,  states={'draft': [('readonly', False)]}, domain=[('order_id','=',False)])
    plan_call_id = fields.Many2one('service.plan.call', string='Plan Call',readonly=True,)

    reason_id = fields.Many2one('service.order.reason', string='Reason',  readonly=False,  states={'done': [('readonly', True)]})
    type_id = fields.Many2one('service.order.type', string='Type',  readonly=False,  states={'done': [('readonly', True)]}) 

    parameter_ids = fields.Many2many('service.operating.parameter', 'service_order_agreement', 'order_id','parameter_id', string='Parameter',
                                     readonly=False,  states={'done': [('readonly', True)]})

    #index introdus la constatare
    meter_reading_ids = fields.Many2many('service.meter.reading', 'service_order_meter_reading', 'order_id','meter_reading_id', string='Meter Readings',
                                            readonly=False,  
                                            states={'done': [('readonly', True)]} )
    
    # semantura client !!    
    signature = fields.Binary(string="Signature", readonly=True)
    
    ## am predat ??
    ## am primit ??


    ## timp alocat pt rezolvarea unei sesizari ???
    

    # alt obiect trebuie pentru procesul verbal de instalare / dezinstalare 


    @api.model
    def create(self,   vals ):  
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            sequence_order = self.env.ref('deltatech_service_maintenance.sequence_order')
            if sequence_order:
                vals['name'] = self.env['ir.sequence'].next_by_id(sequence_order.id)         
        return super(service_order, self).create( vals )
    
    

    @api.onchange('equipment_id','date')
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.equipment_history_id = self.equipment_id.get_history_id(self.date)
        else: 
            self.equipment_history_id = False    


    @api.onchange('notification_id')
    def onchange_notification_id(self):
        if self.notification_id:
            self.equipment_id = self.notification_id.equipment_id
            self.equipment_history_id = self.notification_id.equipment_history_id
            self.notification_id.order_id = self  # oare e bine ?


    @api.multi
    def action_cancel(self):
        self.write({'state':'cancel'})

 
    @api.multi
    def action_rejected(self):
        self.write({'state':'rejected'})

    @api.multi
    def action_start(self):
        self.write({'state':'progress',
                    'date_start':fields.Datetime.now()})

    @api.multi
    def action_work_again(self):
        self.write({'state':'progress'})


    @api.multi
    def action_work_done(self):
        if self.signature:
            self.write({'date_done':fields.Datetime.now()}) 
            self.action_done()
        else:
            self.write({'state':'work_done',
                        'date_done':fields.Datetime.now()})

        
    @api.multi
    def action_done(self):
        if not self.parameter_ids and not self.signature:
            raise Warning(_('Please select a parameter.')) 
        self.write({'state':'done'})
        if self.plan_call_id:
            self.plan_call_id.write(  {'completion_date': self.date_done })
            self.plan_call_id.action_complete()


    @api.multi
    def new_piking_button(self):
        if self.equipment_id:
            return self.equipment_id.new_piking_button()

    @api.multi
    def unlink(self):
        unlink_ids = []
        for order  in self:
            if not order.state in ['draft', 'cancel']:
                raise Warning(_('Can not delete order in status %s') %  order.state) 
        return super(service_order,self).unlink()



    @api.multi
    def open_order_on_website(self):        
        url =  "/service/order/"+str(self.id)       
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
            }

class service_order_reason(models.Model):
    _name = 'service.order.reason'
    _description = "Service Order Reason"
    name = fields.Char(string='Reason', translate=True) 


class service_operating_parameter(models.Model):
    _name = 'service.operating.parameter'
    _description = "Service Operating Parameter" 
    name = fields.Char(string='Parameter', translate=True) 
    
    
class service_order_type(models.Model):
    _name = 'service.order.type'
    _description = "Service Order Type"     
    name = fields.Char(string='Type', translate=True) 
    category = fields.Selection([('cor','Corrective'),('pre','Preventive')])


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: