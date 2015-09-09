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
import math

 

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
    
    equipment_id = fields.Many2one('service.equipment', string='Equipment',index=True)
    meter_id = fields.Many2one('service.meter', string='Meter')  
    


    # de adaugat constringerea ca unitatea de masura de la linie sa fi la fel ca si cea de la meter
    
    @api.onchange('equipment_id')
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.meter_id = self.equipment_id.meter_ids[0]
 
 
    @api.onchange('meter_id')
    def onchange_meter_id(self):
        if self.meter_id:
            self.equipment_id = self.meter_id.equipment_id
            self.uom_id = self.meter_id.uom_id                    

    @api.model
    def after_create_consumption(self, consumption):
        #readings = self.env['service.meter.reading']
        if self.equipment_id: 
            if self.meter_id:
                readings =  self.meter_id.meter_reading_ids.filtered(lambda r: not r.consumption_id)
                readings = readings.filtered(lambda r:  r.date <= consumption.period_id.date_stop )
                quantity = 0
               
                for reading in readings:   
                    from_uom = reading.meter_id.uom_id
                    to_uom =  consumption.agreement_line_id.uom_id
                    
                    amount = reading.difference/from_uom.factor
                    if to_uom:
                        amount = amount * to_uom.factor
                               
                    quantity += amount
                
                name = self.equipment_id.display_name + '\n'
                if readings:
                    first_reading = readings[-1]
                    last_reading = readings[0]
                    name +=  _('Old index: %s, New index:%s') % (first_reading.previous_counter_value, last_reading.counter_value)  
                    
                    readings.write({'consumption_id':consumption.id})
                    
                consumption.write({'quantity':quantity, 'name':name})
            else:
                consumption.write({'name':self.equipment_id.display_name})
                
                
                
            




    
    
    
    
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
