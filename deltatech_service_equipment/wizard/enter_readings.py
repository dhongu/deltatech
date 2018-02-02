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
import openerp.addons.decimal_precision as dp
from openerp.api import Environment
import threading


class service_enter_reading(models.TransientModel):
    _name = 'service.enter.reading'
    _description = "Enter Meter Readings"

    date = fields.Date(string='Date', index=True, required=True, default = fields.Date.today()  ) 
   
    read_by = fields.Many2one('res.partner', string='Read by', domain=[('is_company','=',False)])
    note =  fields.Text(String='Notes')
    items = fields.One2many('service.enter.reading.item','enter_reading_id')
    error = fields.Text(compute="_compute_error")

    @api.one
    @api.depends('items.counter_value')
    def _compute_error(self):
        self.error = ''
        for item in self.items:
            if item.counter_value <= item.meter_id.total_counter_value and item.meter_id.total_counter_value > 0:
                self.error += _('The counter %s value must be greater than %s') % (
                item.meter_id.name, item.meter_id.total_counter_value)




    @api.model
    def default_get(self, fields):
        defaults = super(service_enter_reading, self).default_get(fields)
      
        active_ids = self.env.context.get('active_ids', False)       
        domain = [('equipment_id','in',active_ids)] 
        meters = self.env['service.meter'].search(domain)
        defaults['items'] = []
        for meter in meters:
            if meter.type == 'counter':
                defaults['items'] += [(0,0,{'meter_id':meter.id,
                                            'equipment_id':meter.equipment_id.id,
                                            'counter_value': meter.total_counter_value,
                                            'prev_value': meter.total_counter_value})]

        return defaults


    @api.onchange('date')
    def onchange_date(self):
        meters = self.env['service.meter']
        for item in self.items:
            meters |=  item.meter_id
        items = []
        for meter in meters:
            if meter.type == 'counter':
                meter = meter.with_context({'date':self.date})
                items += [(0,0,{'meter_id':meter.id,
                                'equipment_id':meter.equipment_id.id,
                                'counter_value': meter.total_counter_value,
                                'prev_value': meter.total_counter_value})]

        items =  self._convert_to_cache({'items': items }, validate=False)
        self.update(items) 

    @api.multi
    def do_enter(self):
        for enter_reading in self:
            for item in enter_reading.items:
                self.env['service.meter.reading'].create({'meter_id':item.meter_id.id,
                                                          'equipment_id':item.meter_id.equipment_id.id,
                                                          'date':enter_reading.date,
                                                          'read_by':enter_reading.read_by.id,
                                                          'note':enter_reading.note,
                                                          'counter_value': item.counter_value,
                                                          'estimated': item.estimated})
        
    
class service_enter_reading_item(models.TransientModel):
    _name = 'service.enter.reading.item'
    _description = "Enter Meter Reading Item"

    enter_reading_id = fields.Many2one('service.enter.reading', string='Enter Reading') 
    meter_id = fields.Many2one('service.meter', string='Meter',  readonly=True ) 
    equipment_id = fields.Many2one('service.equipment', string="Equipment", readonly=True)
    counter_value = fields.Float(string='Counter Value', digits= dp.get_precision('Meter Value'), required=True)
    prev_value = fields.Float(string='Previous Value', digits= dp.get_precision('Meter Value'), required=False)
    estimated = fields.Boolean(string='Estimated')
