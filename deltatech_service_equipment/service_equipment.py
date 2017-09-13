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
    oddsum = 0
    evensum = 0
    total = 0
    eanvalue = eancode
    reversevalue = eanvalue[::-1]
    finalean = reversevalue[1:]

    for i in range(len(finalean)):
        if i % 2 == 0:
            oddsum += int(finalean[i])
        else:
            evensum += int(finalean[i])
    total = (oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) % 10
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
    _order = 'equipment_id, from_date DESC'

    name = fields.Char(string='Name', related='equipment_id.name')
    from_date = fields.Date(string="Installation Date", required=True, index=True)

    equipment_id = fields.Many2one('service.equipment', string="Equipment", ondelete='cascade', index=True)

    # cind se actulizeaza  agreement_id?
    agreement_id = fields.Many2one('service.agreement', string='Service Agreement')
    partner_id = fields.Many2one('res.partner', string='Customer', help='The customer where the equipment is installed')
    address_id = fields.Many2one('res.partner', string='Location',
                                 help='The working point where the equipment was located')
    emplacement = fields.Char(string='Emplacement', help='Detail of location of the equipment in working point')

    equipment_backup_id = fields.Many2one('service.equipment', string="Backup Equipment")

    active = fields.Boolean(default=True)

    # dupa ce se introduce un nou contor se verifica daca are citiri introduse la data din istoric echipament
    # la instalare dezinstalare se citesc automat contorii si se genereaza consumuri !! planificat???


class service_equipment(models.Model):
    _name = 'service.equipment'
    _description = "Equipment"
    _inherit = 'mail.thread'
    _order = "id desc"
    _rec_name = "display_name"

    state = fields.Selection([('available', 'Available'), ('installed', 'Installed'), ('inactive', 'Inactive'),
                              ('backuped', 'Backuped')], default="available", string='Status', copy=False)

    agreement_id = fields.Many2one('service.agreement', string='Contract Service', compute="_compute_agreement_id",
                                   store=True, readonly=True, default=False)
    agreement_type_id = fields.Many2one('service.agreement.type', string='Agreement Type', store=True,
                                        related='agreement_id.type_id')
    user_id = fields.Many2one('res.users', string='Responsible', track_visibility='onchange')

    # unde este echipamentul
    equipment_history_id = fields.Many2one('service.equipment.history', string='Equipment actual location', copy=False)

    equipment_history_ids = fields.One2many('service.equipment.history', 'equipment_id', string='Equipment History')

    # proprietarul  echipamentului
    partner_id = fields.Many2one('res.partner', string='Customer', related='equipment_history_id.partner_id',
                                 store=True,
                                 readonly=True, help='The owner of the equipment')
    address_id = fields.Many2one('res.partner', string='Location', related='equipment_history_id.address_id',
                                 readonly=True,
                                 help='The address where the equipment is located')
    emplacement = fields.Char(string='Emplacement', related='equipment_history_id.emplacement', readonly=True,
                              help='Detail of location of the equipment in working point')
    install_date = fields.Date(string='Installation Date', related='equipment_history_id.from_date', readonly=True)
    equipment_backup_id = fields.Many2one('service.equipment', string="Backup Equipment",
                                          related='equipment_history_id.equipment_backup_id', readonly=True)

    contact_id = fields.Many2one('res.partner', string='Contact Person', track_visibility='onchange',
                                 domain=[('type', '=', 'contact'), ('is_company', '=', False)])

    name = fields.Char(string='Name', index=True, default="/", copy=False)
    display_name = fields.Char(compute='_compute_display_name')

    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict',
                                 domain=[('type', '=', 'product')])
    serial_id = fields.Many2one('stock.production.lot', string='Serial Number', ondelete="restrict", copy=False)
    quant_id = fields.Many2one('stock.quant', string='Quant', ondelete="restrict", copy=False)
    inventory_value = fields.Float(string="Inventory value",
                                   related="quant_id.inventory_value")  # se determina din Quant

    total_revenues = fields.Float(string="Total Revenues",
                                  readonly=True)  # se va calcula din suma consumurilor de servicii
    total_costs = fields.Float(string="Total Cost", readonly=True)  # se va calcula din suma avizelor

    note = fields.Text(String='Notes')
    start_date = fields.Date(string='Start Date')

    meter_ids = fields.One2many('service.meter', 'equipment_id', string='Meters', copy=True)
    # meter_reading_ids = fields.One2many('service.meter.reading', 'equipment_id', string='Meter Reading',   copy=False) # mai trebuie ??

    ean_code = fields.Char(string="EAN Code")

    vendor_id = fields.Many2one('res.partner', string='Vendor')
    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer')

    image_qr_html = fields.Html(string="QR image", compute="_compute_image_qr_html")
    type_id = fields.Many2one('service.equipment.type', required=True, string='Type')
    categ_id = fields.Many2one('service.equipment.category', related="type_id.categ_id", string="Category")

    # consumable_id = fields.Many2one('service.consumable', string='Consumable List')
    consumable_item_ids = fields.Many2many('service.consumable.item', string='Consumables',
                                           compute="_compute_consumable_item_ids", readonly=True)
    readings_status = fields.Selection([('', 'N/A'), ('unmade', 'Unmade'), ('done', 'Done')], string="Readings Status",
                                       compute="_compute_readings_status", store=True)

    reading_day = fields.Integer(string='Reading Day', default=-1,
                                 help="""Day of the month, set -1 for the last day of the month.
                                     If it's positive, it gives the day of the month. Set 0 for net days .""")
    last_reading = fields.Date("Last Reading Date", readonly=True, default="2000-01-01")

    _sql_constraints = [
        ('ean_code_uniq', 'unique(ean_code)',
         'EAN Code already exist!'),
    ]

    @api.model
    def create(self, vals):
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            sequence = self.env.ref('deltatech_service_equipment.sequence_equipment')
            if sequence:
                vals['name'] = self.env['ir.sequence'].next_by_id(sequence.id)
                # if not vals.get('equipment_history_id',False):
        # vals['equipment_history_ids'] = [(0,0,{'from_date':  '2000-01-01'})]
        return super(service_equipment, self).create(vals)

    @api.multi
    def write(self, vals):
        if ('name' in vals) and (vals.get('name') in ('/', False)):
            self.ensure_one()
            sequence = self.env.ref('deltatech_service_equipment.sequence_equipment')
            if sequence:
                vals['name'] = self.env['ir.sequence'].next_by_id(sequence.id)
        return super(service_equipment, self).write(vals)

    @api.returns('service.equipment.history')
    def get_history_id(self, date):

        if self.equipment_history_id and date > self.equipment_history_id.from_date:
            res = self.equipment_history_id
        else:
            res = self.env['service.equipment.history'].search([('equipment_id', '=', self.id),
                                                                ('from_date', '<=', date)], order='from_date DESC',
                                                               limit=1)

        return res

    @api.multi
    def costs_and_revenues(self):
        for equi in self:
            cost = 0.0
            pickings = self.env['stock.picking'].search([('equipment_id', '=', equi.id), ('state', '=', 'done')])
            for picking in pickings:
                for move in picking.move_lines:
                    move_value = 0.0
                    for quant in move.quant_ids:
                        move_value += quant.cost * quant.qty
                    if move.location_id.usage == 'internal':
                        cost += move_value
                    else:
                        cost -= move_value
            revenues = 0.0
            consumptions = self.env['service.consumption'].search([('equipment_id', '=', equi.id)])
            for consumption in consumptions:
                if consumption.state == 'done':
                    revenues += consumption.currency_id.compute(consumption.price_unit * consumption.quantity,
                                                                self.env.user.company_id.currency_id)

            equi.write({'total_costs': cost,
                        'total_revenues': revenues})

    @api.multi
    def _compute_readings_status(self):
        for equi in self:
            next_date = date.today()
            if equi.reading_day < 0:
                next_first_date = next_date + relativedelta(day=1, months=0)
                next_date = next_first_date + relativedelta(days=equi.reading_day)
            if equi.reading_day > 0:
                next_date += relativedelta(day=equi.reading_day, months=0)

            if next_date > date.today():
                next_date += relativedelta(months=-1)

            next_date = fields.Date.to_string(next_date)

            equi.readings_status = 'done'
            for meter in equi.meter_ids:

                if not meter.last_meter_reading_id:
                    equi.readings_status = 'unmade'
                    break
                else:
                    equi.last_reading = meter.last_meter_reading_id.date
                if not (meter.last_meter_reading_id.date >= next_date):
                    equi.readings_status = 'unmade'
                    break

    @api.one
    @api.depends('name', 'address_id', 'serial_id')
    def _compute_display_name(self):
        if self.address_id:
            self.display_name = self.name + ' / ' + self.address_id.name
        else:
            self.display_name = self.name
        if self.serial_id:
            self.display_name = self.display_name + ' / ' + self.serial_id.name

    @api.multi
    def name_get(self):
        res = super(service_equipment, self).name_get()
        return res

    @api.one
    def _compute_consumable_item_ids(self):
        self.consumable_item_ids = self.env['service.consumable.item'].search(
            [('type_id', '=', self.type_id.id)])

    @api.one
    def _compute_image_qr_html(self):
        self.image_qr_html = "<img src='/report/barcode/?type=%s&value=%s&width=%s&height=%s'/>" % (
        'QR', self.ean_code or '', 150, 150)

    @api.one
    def _compute_agreement_id(self):
        if not isinstance(self.id, models.NewId):
            agreements = self.env['service.agreement']
            agreement_line = self.env['service.agreement.line'].search([('equipment_id', '=', self.id)])
            for line in agreement_line:
                if line.agreement_id.state == 'open':
                    agreements = agreements | line.agreement_id
            if len(agreements) > 1:
                msg = _("Equipment %s assigned to many agreements.")
                self.message_post(msg)

            # daca nu e activ intr-un contract poate se gaseste pe un contract ciorna
            if not agreements:
                for line in agreement_line:
                    if line.agreement_id.state == 'draft':
                        agreements = agreements | line.agreement_id

            if len(agreements) > 0:
                self.agreement_id = agreements[0]
                self.partner_id = agreements[0].partner_id

    # @api.onchange('type_id')
    # def onchange_type_id(self):
    #    self.product_id = self.type_id.product_id 

    """
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
            consumable_id =  self.env['service.consumable'].search([('product_id','=',self.product_id.id)])
            if not consumable_id:
                consumable_id =  self.env['service.consumable'].search([('type_id','=',self.type_id.id)])
            self.consumable_id    
    """

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            domain = [('product_id', '=', self.product_id.id)]
        else:
            domain = []
        return {'domain': {'serial_id': domain}}

    @api.onchange('serial_id')
    def onchange_serial_id(self):
        self.product_id = self.serial_id.product_id
        if self.serial_id.quant_ids:
            self.quant_id = self.serial_id.quant_ids[0]

    """"
    @api.onchange('type_id', 'product_id')
    def onchange_type_id(self):
        consumable_id = False
        if self.product_id:
            consumable_id = self.env['service.consumable'].search([('product_id', '=', self.product_id.id)], limit=1)
        if not consumable_id:
            consumable_id = self.env['service.consumable'].search([('type_id', '=', self.type_id.id)], limit=1)
        self.consumable_id = consumable_id
        #sunt definite contoare ?
    """

    @api.onchange('quant_id')
    def onchange_quant_id(self):
        if self.quant_id:
            self.inventory_value = self.quant_id.inventory_value
            try:
                self.vendor_id = self.quant_id.supplier_id
            except:
                pass


    @api.multi
    def invoice_button(self):
        invoices = self.env['account.invoice']
        for meter in self.meter_ids:
            for meter_reading in meter.meter_reading_ids:
                if meter_reading.consumption_id and meter_reading.consumption_id.invoice_id:
                    invoices = invoices | meter_reading.consumption_id.invoice_id

        return {
            'domain': "[('id','in', [" + ','.join(map(str, invoices.ids)) + "])]",
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
        pickings = self.env['stock.picking'].search([('equipment_id', 'in', self.ids)])
        context = {'default_equipment_id': self.id,
                   'default_agreement_id': self.agreement_id.id,
                   'default_picking_type_code': 'outgoing',
                   'default_picking_type_id': self.env.ref('stock.picking_type_outgoing_not2binvoiced').id,
                   'default_partner_id': self.address_id.id}

        return {
            'domain': "[('id','in', [" + ','.join(map(str, pickings.ids)) + "])]",
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
        context = {'default_equipment_id': self.id,
                   'default_agreement_id': self.agreement_id.id,
                   'default_picking_type_code': 'outgoing',
                   'default_picking_type_id': self.env.ref('stock.picking_type_outgoing_not2binvoiced').id,
                   'default_partner_id': self.address_id.id}

        if self.consumable_item_ids:

            picking = self.env['stock.picking'].with_context(context)

            context['default_move_lines'] = []

            for item in self.consumable_item_ids:
                value = picking.move_lines.onchange_product_id(prod_id=item.product_id.id)['value']
                value['location_id'] = picking.move_lines._default_location_source()
                value['location_dest_id'] = picking.move_lines._default_location_destination()
                value['date_expected'] = fields.Datetime.now()
                value['product_id'] = item.product_id.id
                context['default_move_lines'] += [(0, 0, value)]

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

    @api.multi
    def create_meters_button(self):
        for equi in self:
            categs = self.env['service.meter.category']
            for template in equi.categ_id.template_meter_ids:
                categs |= template.meter_categ_id
            for categ in categs:
                equi.meter_ids.create({'equipment_id': equi.id,
                                       'meter_categ_id': categ.id,
                                       'uom_id': categ.uom_id.id})

    @api.multi
    def update_meter_status(self):
        self._compute_readings_status()

    # o fi ok sa elimin echipmanetul din contract ?
    @api.multi
    def remove_from_agreement_button(self):
        self.ensure_one()
        if self.agreement_id.state == 'draft':
            lines = self.env['service.agreement.line'].search(
                [('agreement_id', '=', self.agreement_id.id), ('equipment_id', '=', self.id)])
            lines.unlink()
            if not self.agreement_id.agreement_line:
                self.agreement_id.unlink()
        else:
            raise Warning(_('The agreement %s is in state %s') % (self.agreement_id.name, self.agreement_id.state))


class service_equipment_category(models.Model):
    _name = 'service.equipment.category'
    _description = "Service Equipment Category"
    name = fields.Char(string='Category', translate=True)

    out_type_id = fields.Many2one('stock.picking.type', string='Out Type')
    in_type_id = fields.Many2one('stock.picking.type', string='In Type')

    template_meter_ids = fields.One2many('service.template.meter', 'categ_id')


class service_equipment_type(models.Model):
    _name = 'service.equipment.type'
    _description = "Service Equipment Type"
    name = fields.Char(string='Type', translate=True)
    categ_id = fields.Many2one('service.equipment.category', string="Category")

    # template_meter_ids = fields.One2many('service.template.meter', 'type_id')

    # consumable_id = fields.Many2one('service.consumable', string='Consumable List')
    consumable_item_ids = fields.One2many('service.consumable.item', 'type_id', string='Consumable')



# este utilizat pentru generare de pozitii noi in contract si pentru adugare contori noi
class service_template_meter(models.Model):
    _name = 'service.template.meter'
    _description = "Service Template Meter"

    type_id = fields.Many2one('service.equipment.type', string="Type")
    categ_id = fields.Many2one('service.equipment.category', string="Category")
    product_id = fields.Many2one('product.product', string='Service', ondelete='set null',
                                 domain=[('type', '=', 'service')])
    meter_categ_id = fields.Many2one('service.meter.category', string="Meter category")
    bill_uom_id = fields.Many2one('product.uom', string='Billing Unit of Measure')
    currency_id = fields.Many2one('res.currency', string="Currency", required=True,
                                  domain=[('name', 'in', ['RON', 'EUR'])])


    @api.onchange('meter_categ_id')
    def onchange_meter_categ_id(self):
        self.bill_uom_id = self.meter_categ_id.bill_uom_id

        # product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', domain=[('type', '=', 'product')] )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
