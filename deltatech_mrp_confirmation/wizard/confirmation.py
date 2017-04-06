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
##############################################################################




from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class mrp_production_conf(models.TransientModel):
    _name = 'mrp.production.conf'
    _description = "Production Confirmation"

    scanned_barcode = fields.Char(string="Scanned Bar code")
    production_id = fields.Many2one('mrp.production', string='Production Order')
    product_id = fields.Many2one('product.product', 'Product', related='production_id.product_id', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Operator")
    code = fields.Char('Operation Code')
    operation_id = fields.Many2one('mrp.workorder')

    qty_production = fields.Float('Original Production Quantity', readonly=True, related='production_id.product_qty')
    qty_produced = fields.Float('Quantity', readonly=True, related='operation_id.qty_produced')
    qty_producing = fields.Float('Currently Produced Quantity', related='operation_id.qty_producing')

    operation_ids = fields.Many2many('mrp.workorder', relation="mrp_production_conf_operation_rel", string="Operations",
                                     compute="_get_operation_ids")

    error_message = fields.Char(string="Message", readonly=True)

    """
    @api.onchange('production_id', 'partner_id', 'operation_id')
    def onchange_production_id(self):
        if not self.production_id:
            return
        if self.operation_id:
            operation_ids = self._convert_to_cache({'operation_ids': [[6, 0, [self.operation_id.id]]]}, validate=False)
            self.operation_id = False
            self.production_id = self.production_id
        else:
            operation_ids = self._convert_to_cache({'operation_ids': [[6, 0, self.production_id.workorder_ids.ids]]},
                                                   validate=False)
        self.update(operation_ids)
    """

    @api.depends('production_id', 'partner_id', 'code')
    def _get_operation_ids(self):
        operation_ids = self.env['mrp.workorder']
        if self.production_id:
            for workorder in self.production_id.workorder_ids:
                if self.code:
                    if self.code == workorder.code:
                        operation_ids |= workorder
                else:
                    operation_ids |= workorder
        else:
            if self.code:
                operation_ids = self.env['mrp.workorder'].search([('code', '=', self.code),
                                                                  ('state', 'not in', ['done', 'cancel'])])
        self.operation_ids = operation_ids

    @api.onchange('scanned_barcode')
    def onchange_scanned_barcode(self):
        scanned_barcode = self.scanned_barcode
        self.scanned_barcode = ''
        if not scanned_barcode:
            return
        return self.barcode_scan(scanned_barcode)

    @api.model
    def barcode_scan(self, barcode):

        scanned_barcode = barcode

        domain = [('name', '=', scanned_barcode), ('state', 'in', ['in_production'])]
        production = self.env['mrp.production'].search(domain)
        if production:
            self.production_id = production
            self.partner_id = False
            self.error_message = ''
            return

        if self.production_id:
            domain = [('ref', '=', scanned_barcode)]
            partner = self.env['res.partner'].search(domain)
            if partner and len(partner) == 1:
                self.partner_id = partner
                self.error_message = _('Operator %s was found') % self.partner_id.name
                start_next = False
                for operation in self.production_id.workcenter_lines:
                    if start_next:
                        start_next = False
                        operation.signal_workflow('button_start_working')
                        break
                    if operation.state == 'startworking':
                        self.operation_id = operation.id
                        for operator in operation.workcenter_id.operator_ids:
                            if operator.from_date <= fields.Date.today() <= operator.to_date:
                                if operator.partner_id == self.partner_id:
                                    operation.write({'partner_id': self.partner_id.id})
                                    self.error_message = _('Operation %s was made by %s') % (
                                        operation.name, partner.name)
                                    operation.signal_workflow('button_done')
                                    start_next = True

        if not self.production_id:
            self.error_message = _('Order %s not found') % scanned_barcode
        elif not self.partner_id:
            self.error_message = _('Operator %s not found') % scanned_barcode

        if self.error_message:
            return {'warning': self.error_message}

        return

    @api.model
    def default_get(self, fields):
        defaults = super(mrp_production_conf, self).default_get(fields)

        active_id = self.env.context.get('active_id', False)
        if active_id:
            defaults['production_id'] = active_id
        return defaults

    @api.multi
    def do_confim(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
