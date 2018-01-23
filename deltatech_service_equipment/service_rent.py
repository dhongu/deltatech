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

    equipment_count = fields.Integer(compute="_compute_equipment_count")
    equipment_inv_value = fields.Float(compute="_compute_equipment_inv_value")
    equipment_init_value = fields.Float(compute="_compute_equipment_init_value")

    @api.multi
    @api.depends('agreement_line')
    def _compute_equipment_count(self):
        for agreement in self:
            equipments = self.env['service.equipment']

            for item in self.agreement_line:
                if item.equipment_id:
                    equipments |= item.equipment_id

            self.equipment_count = len(equipments)

    @api.multi
    @api.depends('agreement_line')
    def _compute_equipment_inv_value(self):
        value = 0.0
        for agreement in self:
            equipments = self.env['service.equipment']

            for item in self.agreement_line:
                if item.equipment_id:
                    if item.equipment_id not in equipments:
                        equipments |= item.equipment_id
                        value += item.equipment_id.inventory_value

            self.equipment_inv_value = round(value,2)

    @api.multi
    @api.depends('agreement_line')
    def _compute_equipment_init_value(self):
        value = 0.0
        for agreement in self:
            equipments = self.env['service.equipment']

            for item in self.agreement_line:
                if item.equipment_id:
                    if item.equipment_id not in equipments:
                        if item.equipment_id.quant_id:
                            equipments |= item.equipment_id
                            value += item.equipment_id.quant_id.init_value

            self.equipment_init_value = round(value,2)


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

    @api.multi
    def update_hist(self):
        for agreement in self:
            for line in agreement.agreement_line:
                if line.equipment_id:
                    line.write({'equipment_history_id': line.equipment_id.equipment_history_id.id})


class service_agreement_line(models.Model):
    _inherit = 'service.agreement.line'  
    
    equipment_id = fields.Many2one('service.equipment', string='Equipment',index=True)
    equipment_history_id = fields.Many2one('service.equipment.history', string='Equipment history',
                                           copy=False)  # id de istoric la care a fost instalat echipamentul
    meter_id = fields.Many2one('service.meter', string='Meter')


    lock_edit = fields.Boolean()
    
    # de adaugat constringerea ca unitatea de masura de la linie sa fi la fel ca si cea de la meter
    
    @api.onchange('equipment_id')
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.meter_id = self.equipment_id.meter_ids[0]
            self.equipment_history_id = self.equipment_id.equipment_history_id

 
    @api.onchange('meter_id')
    def onchange_meter_id(self):
        if self.meter_id:
            self.equipment_id = self.meter_id.equipment_id
            self.quantity = 0.0
            #self.uom_id = self.meter_id.uom_id                    


    @api.model
    def create(self,   vals ):         
        if 'equipment_id'  in vals:
            if vals['equipment_id']:
                equipment =  self.env['service.equipment'].browse(vals['equipment_id'])
                if equipment.agreement_id  and equipment.agreement_id.state == 'open':
                    if equipment.agreement_id.id != vals['agreement_id']:
                        raise Warning(_("Equipment %s assigned to many agreements." ) % equipment.name)
                else:
                    equipment.write({'agreement_id':vals['agreement_id']})
        return super(service_agreement_line, self).create( vals )

    @api.multi
    def write(self, vals):
        if 'equipment_id'  in vals:
            if vals['equipment_id']:
                for line in self:
                    equipment =  self.env['service.equipment'].browse(vals['equipment_id'])
                    if equipment.agreement_id and equipment.agreement_id.state == 'open':
                        if equipment.agreement_id != line.agreement_id:
                            raise Warning(_("Equipment %s assigned to many agreements." ) % equipment.name)
                    else:
                        equipment.write({'agreement_id':vals['agreement_id']})
                        
        return super(service_agreement_line, self).write( vals)




    @api.model
    def after_create_consumption(self, consumption, backup_equipment=False ):
        #readings = self.env['service.meter.reading']
        # la data citirii echipamentul functiona in baza contractului???\\
        # daca echipamentul a fost inlocuit de unul de rezeva ?
        
        self.ensure_one()
        res = [consumption.id]   # trebuie musai fa folosesc super ???
        if self.equipment_id: 
            
            # echipamentul are instalari dezintalari in perioada  ?
            if self.meter_id and backup_equipment :
                meter = backup_equipment.meter_ids.filtered(lambda r: r.uom_id.id == self.meter_id.uom_id.id)
            else:
                meter = self.meter_id
                
            if backup_equipment:
                equipment = backup_equipment
            else:
                equipment = self.equipment_id

            de_la_data = self.equipment_history_id.from_date
            readings = meter.meter_reading_ids.filtered(lambda r: r.consumption_id)
            if readings:
                de_la_data = max([readings[0].date, de_la_data])

            if meter:
                # se selecteaza citirile care nu sunt facturate
                # se selecteaza citirile care sunt anterioare sfarsitului de perioada, e pozibil ca sa mai fie citiri in perioada anterioara nefacturate   
                
                readings =  meter.meter_reading_ids.filtered(lambda r: not r.consumption_id and  
                                                                        r.date <= consumption.period_id.date_stop and
                                                                       r.date >= de_la_data)  # sa fie dupa data de instalare si dupa ultima citire facturata
                # se selecteaza citirile pentru intervalul in care echipamentul era instalat la client
                
                if readings:
                    end_date = max( readings[0].date, consumption.period_id.date_stop)
                    start_date = min( readings[-1].date, consumption.period_id.date_start)
                else:
                    end_date =  consumption.period_id.date_start 
                    start_date =  consumption.period_id.date_stop

                # print start_date, end_date, readings
                # de ce mai determin citirile cand : pentru a scoate citirile care au facuta cand echipamentul era dezinstalat sau backup
                domain = [('id','in',readings.ids ),('equipment_history_id.address_id','child_of',self.agreement_id.partner_id.id)]
                
                readings = self.env['service.meter.reading'].search(domain)
                quantity = 0
                #print start_date, end_date, readings
                for reading in readings:   
                    from_uom = reading.meter_id.uom_id
                    to_uom =  consumption.agreement_line_id.uom_id
                    
                    amount = reading.difference/from_uom.factor
                    if to_uom:
                        amount = amount * to_uom.factor
                               
                    quantity += amount
                
                name = self.equipment_id.display_name + '\n'
                if backup_equipment:
                    name  +=  _('Backup') + backup_equipment.display_name + '\n'
                if readings:
                    first_reading = readings[-1]
                    last_reading = readings[0]
                    name +=  _('Old index: %s, New index:%s') % (first_reading.previous_counter_value, last_reading.counter_value)  
                    
                    readings.write({'consumption_id':consumption.id})
                if quantity != 0 or consumption.agreement_line_id.active:
                    consumption.write({'quantity': quantity,
                                       'name': name,
                                       'equipment_id': equipment.id})
                
                # determin daca in interval echipamentul a fost inlcuit de altul
                domain = [('equipment_id','=',equipment.id),('from_date','>=',start_date),('from_date','<=',end_date)]
                
                equipment_hist_ids =  self.env['service.equipment.history'].search(domain)
                equipments = self.env['service.equipment']
                for equi_hist in equipment_hist_ids:
                    equipments |= equi_hist.equipment_backup_id
                for equi in equipments:
                    cons_value = self.get_value_for_consumption()
                    if cons_value:
                        cons_value.update({
                              'partner_id' : consumption.partner_id.id,
                              'period_id':   consumption.period_id.id,   
                              'agreement_id': consumption.agreement_id.id,
                              'agreement_line_id': consumption.agreement_line_id.id,
                              'date_invoice':consumption.date_invoice,
                        }) 
                        new_consumption = self.env['service.consumption'].create(cons_value) 
                         
                        res = res.extend( self.after_create_consumption(new_consumption, equi) )                   
                
            else:  # echipament fara contor
                cons_value = {'name': self.equipment_id.display_name, 'equipment_id': equipment.id}
                if not consumption.agreement_line_id.active:
                    cons_value['quantity'] = 0
                consumption.write(cons_value)
        return res        
                

class service_consumption(models.Model):
    _inherit = 'service.consumption'                

    equipment_id = fields.Many2one('service.equipment', string='Equipment',index=True)
    address_id = fields.Many2one('res.partner', string='Location', related='equipment_id.address_id',
                                 readonly=True,
                                 help='The address where the equipment is located', store=True)


    _sql_constraints = [
        ('agreement_line_period_uniq', 'unique(period_id,agreement_line_id,equipment_id)',
            'Agreement line in period already exist!'),
    ]  


    
    
    
    
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
