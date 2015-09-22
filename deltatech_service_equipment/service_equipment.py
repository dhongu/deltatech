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
from dateutil.relativedelta import relativedelta
from datetime import date, datetime



def ean_checksum(eancode):
    """returns the checksum of an ean string of length 13, returns -1 if the string has the wrong length"""
    if len(eancode) != 13:
        return -1
    oddsum=0
    evensum=0
    total=0
    eanvalue=eancode
    reversevalue = eanvalue[::-1]
    finalean=reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total=(oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) %10
    return check

def check_ean(eancode):
    """returns True if eancode is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode) == int(eancode[-1])


class service_equipment_history(models.Model):
    _name = 'service.equipment.history'
    _description = "Equipment History"
    
    
    name =  fields.Char(string='Name', related='equipment_id.name')
    from_date = fields.Date(string="Installation Date",required=True)

    equipment_id = fields.Many2one('service.equipment', string="Equipment",  ondelete='cascade')

    agreement_id = fields.Many2one('service.agreement', string='Service Agreement')   
    partner_id = fields.Many2one('res.partner', string='Owner',help='The owner of the equipment')
    address_id = fields.Many2one('res.partner', string='Location', help='The working point where the equipment was located')
    emplacement = fields.Char(string='Emplacement', help='Detail of location of the equipment in working point')

    equipment_backup_id = fields.Many2one('service.equipment', string="Backup Equipment")    
    
    active = fields.Boolean(default=True)

    # dupa ce se introduce un nou contor se verifica daca are citiri introduse la data din istoric echipament
    #la instalare dezinstalare se citesc automat contorii si se genereaza consumuri !! planificat???

class service_equipment(models.Model):
    _name = 'service.equipment'
    _description = "Equipment"
    _inherit = 'mail.thread'
   

    state = fields.Selection([ ('available','Available'),('installed','Installed'), 
                               ('backuped','Backuped')], default="available", string='Status',  copy=False)

    
    agreement_id = fields.Many2one('service.agreement', string='Contract Service', compute="_compute_agreement_id")
    agreement_type_id = fields.Many2one('service.agreement.type', string='Agreement Type', related='agreement_id.type_id')       
    user_id = fields.Many2one('res.users', string='Responsible', track_visibility='onchange')
    
    
        
    # unde este echipamentul
    equipment_history_id = fields.Many2one('service.equipment.history', string='Equipment actual location',  copy=False)
   
    equipment_history_ids = fields.One2many('service.equipment.history', 'equipment_id', string='Equipment History')
   
    # proprietarul  echipamentului
    partner_id = fields.Many2one('res.partner', string='Owner', related='equipment_history_id.partner_id',
                                    readonly=True,help='The owner of the equipment')
    address_id = fields.Many2one('res.partner', string='Location',  related='equipment_history_id.address_id',readonly=True,
                                 help='The address where the equipment is located')
    emplacement = fields.Char(string='Emplacement', related='equipment_history_id.emplacement',readonly=True,
                              help='Detail of location of the equipment in working point')
    install_date = fields.Date(string='Installation Date', related='equipment_history_id.from_date',readonly=True)
    
    contact_id = fields.Many2one('res.partner', string='Contact Person',  track_visibility='onchange', domain=[('type','=','contact'),('is_company','=',False)])    

    name = fields.Char(string='Name', index=True, default="/" )
    display_name = fields.Char(compute='_compute_display_name')
    
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', domain=[('type', '=', 'product')] )
    serial_id = fields.Many2one('stock.production.lot', string='Serial Number', ondelete="restrict",   copy=False)
    quant_id = fields.Many2one('stock.quant', string='Quant', ondelete="restrict",  copy=False)
    
    note =  fields.Text(String='Notes') 
    start_date = fields.Date(string='Start Date') 

    meter_ids = fields.One2many('service.meter', 'equipment_id', string='Meters' )     
    #meter_reading_ids = fields.One2many('service.meter.reading', 'equipment_id', string='Meter Reading',   copy=False) # mai trebuie ??
    
    ean_code = fields.Char(string="EAN Code")

    vendor_id = fields.Many2one('res.partner', string='Vendor')
    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer')
 
    image_qr_html = fields.Html(string="QR image", compute="_compute_image_qr_html")
    type_id = fields.Many2one('service.equipment.type', string='Type')

    consumable_id =  fields.Many2one('service.consumable', string='Consumable List')    
    consumable_item_ids =  fields.Many2many('service.consumable.item', string='Consumables', compute="_compute_consumable_item_ids", readonly=True)
    readings_status = fields.Selection( [('','N/A'),('unmade','Unmade'),('done','Done')], string="Readings Status", compute="_compute_readings_status" )
    
    _sql_constraints = [
        ('ean_code_uniq', 'unique(ean_code)',
            'EAN Code already exist!'),
    ]  


    @api.model
    def create(self,   vals ):  
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            sequence = self.env.ref('deltatech_service_equipment.sequence_equipment')
            if sequence:
                vals['name'] = self.env['ir.sequence'].next_by_id(sequence.id)    
        #if not vals.get('equipment_history_id',False):
        #    vals['equipment_history_ids'] = [(0,0,{'from_date':  '2000-01-01'})]
        return super(service_equipment, self).create( vals )




    @api.returns('service.equipment.history')
    def get_history_id(self, date): 

        if self.equipment_history_id and date > self.equipment_history_id.from_date:
            res =  self.equipment_history_id
        else:
            res = self.env['service.equipment.history'].search([('equipment_id','=',self.id),
                                                                ('from_date','<=',date)], order='from_date DESC', limit=1)
           
        return res 
    
    
    @api.multi
    def _compute_readings_status(self):
        from_date = date.today() + relativedelta(day=01, months=0, days=0)
        to_date =  date.today() + relativedelta(day=01, months=1, days=-1)
        from_date =  fields.Date.to_string(from_date) 
        to_date =  fields.Date.to_string(to_date) 
        
        current_month  = [('date','>=', from_date  ),  ('date','<=',  to_date ) ] 
        for equi in self:
            equi.readings_status = 'done'
            for meter in equi.meter_ids:
                if not meter.last_meter_reading_id:
                    equi.readings_status = 'unmade'
                    break
                if not ( from_date  <= meter.last_meter_reading_id.date <= to_date ):
                    equi.readings_status = 'unmade'
                    break
        

    @api.one
    @api.depends('name', 'address_id')     # this definition is recursive
    def _compute_display_name(self):
        if self.address_id:
            self.display_name = self.name + ' / ' + self.address_id.name
        else:
            self.display_name = self.name
    
    @api.one
    def _compute_consumable_item_ids(self):
        self.consumable_item_ids = self.env['service.consumable.item'].search([('consumable_id','=',self.consumable_id.id)])
    
    @api.one
    def _compute_image_qr_html(self):
        self.image_qr_html = "<img src='/report/barcode/?type=%s&value=%s&width=%s&height=%s'/>" %   ('QR', self.ean_code or '', 150, 150)
        



    @api.one
    def _compute_agreement_id(self):
        if not isinstance(self.id, models.NewId):
            agreements = self.env['service.agreement']
            agreement_line = self.env['service.agreement.line'].search([('equipment_id','=',self.id)])
            for line in agreement_line:
                if line.agreement_id.state == 'open':
                    agreements = agreements | line.agreement_id  
            if len(agreements) > 1:
                msg = _("Equipment %s assigned to many agreements." )
                self.post_message(msg)
            if len(agreements) > 0:
                self.agreement_id =  agreements[0]
                self.partner_id = agreements[0].partner_id
    
    
    @api.onchange('product_id','partner_id')
    def onchange_product_id(self):
        if self.name == '':
            if self.product_id:
                self.name = self.product_id.name 
            else:
                self.name = ''
            if self.partner_id: 
                self.name += ', ' + self.partner_id.name  
        if self.product_id:
            self.consumable_id =  self.env['service.consumable'].search([('product_id','=',self.product_id.id)])


    
    @api.multi
    def invoice_button(self):
        invoices = self.env['account.invoice']
        for meter_reading in self.meter_reading_ids:
            if meter_reading.consumption_id and meter_reading.consumption_id.invoice_id:
                invoices = invoices | meter_reading.consumption_id.invoice_id
        
        return {
            'domain': "[('id','in', ["+','.join(map(str,invoices.ids))+"])]",
            'name': _('Services Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': False,
            'context': "{'type':'out_invoice', 'journal_type': 'sale'}",
            'type': 'ir.actions.act_window'
        }





    @api.multi
    def picking_button(self):
        pickings = self.env['stock.picking'].search([('equipment_id','in',self.ids)])
        context = {'default_equipment_id':self.id,
                   'default_agreement_id':self.agreement_id.id,
                   'default_picking_type_code':'outgoing',
                   'default_picking_type_id': self.env.ref('stock.picking_type_outgoing_not2binvoiced').id,
                   'default_partner_id':self.address_id.id}     
 
        return {
            'domain': "[('id','in', ["+','.join(map(str,pickings.ids))+"])]",
            'name': _('Delivery for service'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window'
        }       

    @api.multi
    def new_piking_button(self):
        
        # todo: de pus in config daca livrarea se face la adresa din echipamente sau contract
        context = {'default_equipment_id':self.id,
                   'default_agreement_id':self.agreement_id.id,
                   'default_picking_type_code':'outgoing',
                   'default_picking_type_id': self.env.ref('stock.picking_type_outgoing_not2binvoiced').id,
                   'default_partner_id':self.address_id.id}
        if self.consumable_item_ids:
            
            picking = self.env['stock.picking'].with_context(context)
            
            context['default_move_lines'] = []
           
            for item in self.consumable_item_ids:                
                value = picking.move_lines.onchange_product_id(prod_id=item.product_id.id)['value']
                value['location_id'] =  picking.move_lines._default_location_source()
                value['location_dest_id'] =  picking.move_lines._default_location_destination()
                value['date_expected'] = fields.Datetime.now()
                value['product_id'] = item.product_id.id
                context['default_move_lines'] += [(0,0,value)]
        return {
            'name': _('Delivery for service'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'view_id': False,
            'views': [[False, 'form']],
            'context': context,
            'type': 'ir.actions.act_window'
        }        


    @api.one
    @api.constrains('ean_code')
    @api.onchange('ean_code')
    def _check_ean_key(self):
        if not check_ean(self.ean_code):
            raise Warning(_('Error: Invalid EAN code'))
        


class service_equipment_type(models.Model):
    _name = 'service.equipment.type'
    _description = "Service Equipment Type"     
    name = fields.Char(string='Type', translate=True)  
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
