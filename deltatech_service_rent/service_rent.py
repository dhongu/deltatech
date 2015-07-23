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



class service_equipment(models.Model):
    _name = 'service.equipment'
    _description = "Equipment"
    _inherit = 'mail.thread'
    
    # la cine e inchirat echipamentul
    partner_id = fields.Many2one('res.partner', string='Location',  required=True) 
    work_location = fields.Char(string='Work Location')    
    # numele echipamentului care se va completa automat cu nume produs + nume partener
    name = fields.Char(string='Name', index=True, default="/" )
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', domain=[('type', '=', 'product')] )
    serial_id = fields.Many2one('stock.production.lot', string='Serial Number', ondelete="restrict")
    quant_id = fields.Many2one('stock.quant', string='Quant', ondelete="restrict")
    note =  fields.Text(String='Notes') 
    start_date = fields.Date(string='Start Date') 

    meter_ids = fields.One2many('service.meter', 'equipment_id', string='Meters' )     
    meter_reading_ids = fields.One2many('service.meter.reading', 'equipment_id', string='Meter Reading')


    @api.onchange('product_id','partner_id')
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name 
        else:
            self.name = ''
        if self.partner_id: 
            self.name += ', ' + self.partner_id.name  


    @api.multi
    def invoice_button(self):
        invoices = self.env['account.invoice']
        for meter_reading in self.meter_reading_ids:
            if meter_reading.consumption_id and meter_reading.consumption_id.invoice_id:
                invoices = invoices | meter_reading.consumption_id.invoice_id
        
        res = []
        for invoices in invoices:
            res.append(invoice.id)
        return {
            'domain': "[('id','in', ["+','.join(map(str,res))+"])]",
            'name': _('Services Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': False,
            'context': "{'type':'out_invoice', 'journal_type': 'sale'}",
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def agreement_button(self):
        agreements = self.env['service.agreement']
        agreement_line = self.env['service.agreement.line'].search([('equipment_id','in',self.ids)])
        for line in agreement_line:
            agreements = agreements | line.agreement_id
        
        res = []
        for agreement in agreements:
            res.append(agreement.id)
        return {
            'domain': "[('id','in', ["+','.join(map(str,res))+"])]",
            'name': _('Services Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'service.agreement',
            'view_id': False,
            'context': "{'type':'out_invoice', 'journal_type': 'sale'}",
            'type': 'ir.actions.act_window'
        }



class service_meter(models.Model):
    _name = 'service.meter'
    _description = "Meter"

    name = fields.Char(string='Name')
    equipment_id = fields.Many2one('service.equipment', string='Equipment',required=True,  ondelete='cascade' ) 
    meter_reading_ids = fields.One2many('service.meter.reading', 'meter_id', string='Meter Reading')
    last_meter_reading_id = fields.Many2one('service.meter.reading', string='Last Meter Reading',compute='_compute_last_meter_reading' )
    total_counter_value = fields.Float(string='Total Counter Value', readonly=True)

    @api.one
    def _compute_last_meter_reading(self ):
        if self.meter_reading_ids:
            self.last_meter_reading_id =  self.meter_reading_ids[0]
 

class service_meter_reading(models.Model):
    _name = 'service.meter.reading'
    _description = "Meter Reading"
    _order = "meter_id, date desc"   
    _rec_name = "counter_value"
    
    meter_id = fields.Many2one('service.meter', string='Meter',required=True, ondelete='restrict',) 
    equipment_id = fields.Many2one('service.equipment', string='Equipment',required=True, ondelete='cascade',) 
    
    date = fields.Date(string='Date') 
    previous_counter_value = fields.Float(string='Previous Counter Value',readonly=True, compute='_compute_previous_counter_value',store=True)
    counter_value = fields.Float(string='Counter Value', group_operator="max")
    estimated = fields.Boolean(string='Estimated')
    difference = fields.Float(string='Difference', readonly=True, compute='_compute_difference',store=True)
    consumption_id = fields.Many2one('service.consumption', string='Consumption',readonly=True) 

    @api.one
    @api.depends('date','meter_id')
    def _compute_previous_counter_value(self ):
        self.previous_counter_value = 0
        if self.date and self.meter_id:
            previous = self.env['service.meter.reading'].search([('meter_id','=',self.meter_id.id),
                                                                 ('date','<',self.date)],limit=1, order='date desc')
            if previous:
                self.previous_counter_value = previous.counter_value
                self.difference = self.counter_value - self.previous_counter_value
                
            
    @api.one
    @api.depends('counter_value')
    def _compute_difference(self):
        self.difference = self.counter_value - self.previous_counter_value
        next = self.env['service.meter.reading'].search([('meter_id','=',self.meter_id.id),
                                                         ('date','>',self.date)],limit=1, order='date')
        if next and next.previous_counter_value <>  self.counter_value:
            next.write({'previous_counter_value': self.counter_value,
                        'difference' : (next.counter_value - self.counter_value)})       
            
    @api.onchange('equipment_id')
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.meter_id = self.equipment_id.meter_ids[0]
            self.previous_counter_value = self.meter_id.last_meter_reading_id.counter_value
            self.counter_value = self.previous_counter_value 

    @api.onchange('meter_id')
    def onchange_meter_id(self):
        if self.meter_id:
            self.equipment_id = self.meter_id.equipment_id
        


class service_agreement(models.Model):
    _inherit = 'service.agreement' 
    
    @api.multi
    def service_equipment(self):
        equipments = self.env['service.equipment']
        
        for item in self.agreement_line:
            if item.equipment_id:
                equipments = equipments + item.equipment_id
        
        res = []
        for equipment in equipments:
            res.append(equipment.id)
            
        return {
            'domain': "[('id','in', ["+','.join(map(str,res))+"])]",
            'name': _('Services Equipment'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'service.equipment',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }        
   
class service_agreement_line(models.Model):
    _inherit = 'service.agreement.line'  
    
    equipment_id = fields.Many2one('service.equipment', string='Equipment')
    meter_id = fields.Many2one('service.meter', string='Meter')  
    
    
    @api.onchange('equipment_id')
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.meter_id = self.equipment_id.meter_ids[0]
 
 
    @api.onchange('meter_id')
    def onchange_equipment_id(self):
        if self.meter_id:
            self.equipment_id = self.meter_id.equipment_id
                                

    @api.model
    def get_value_for_consumption(self):
        res = super(service_agreement_line,self).get_value_for_consumption()
        if self.meter_id:
            if self.meter_id.last_meter_reading_id:
                if self.meter_id.last_meter_reading_id.consumption_id:
                    return  None
                else:
                    res['quantity'] = self.meter_id.last_meter_reading_id.difference
                    res['name'] = _('Old index: %s, New index:%s') % (self.meter_id.last_meter_reading_id.previous_counter_value, 
                                                                      self.meter_id.last_meter_reading_id.counter_value)
                    res['meter_reading_id'] = self.meter_id.last_meter_reading_id.id
        return res


  
    
class service_consumption(models.Model):
    _inherit = 'service.consumption'
    
    meter_reading_id = fields.Many2one('service.meter.reading', string='Meter Reading', readonly = True)

    @api.model
    def create(self, vals):
        consumption = super(service_consumption,self).create(vals) 
        if consumption.meter_reading_id:
            consumption.meter_reading_id.consumption_id = consumption
        return consumption
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
