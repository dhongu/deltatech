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
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_TIME_FORMAT
import time
from datetime import datetime


class account_invoice(models.Model):
    _inherit = "account.invoice"

    # camp pt a indica din ce factura se face stornarea
    origin_refund_invoice_id = fields.Many2one('account.invoice', string='Origin Invoice', copy=False)
    # camp prin care se indica prin ce factura se face stornarea
    refund_invoice_id = fields.Many2one('account.invoice', string='Refund Invoice', copy=False)

    with_refund = fields.Boolean(string="With refund", help="Invoice with refund or is an refund",
                                 compute="_compute_with_refund", store=False)

    # daca in configurare se completeaza ca listele de ridicare trebuie revocate automat

    @api.multi
    def action_cancel(self):
        res = super(account_invoice, self).action_cancel()
        for invoice in self:
            if invoice.company_id.invoice_picking_refund:
                invoice.action_cancel_pickings()

        return res

    @api.one
    @api.depends('origin_refund_invoice_id', 'refund_invoice_id')
    def _compute_with_refund(self):
        for invoice in self:
            if invoice.origin_refund_invoice_id or invoice.refund_invoice_id:
                invoice.with_refund = True
            else:
                invoice.with_refund = False

    @api.model
    def get_link(self, model):
        for model_id, model_name in model.name_get():
            # link = "<a href='#id=%s&model=%s'>%s</a>" % (str(model_id), model._name, model_name )
            link = "<a href=# data-oe-model=%s data-oe-id=%d>%s</a>" % (model._name, model.id, model.name)
        return link

    @api.multi
    @api.returns('self')
    def refund(self, date=None, period_id=None, description=None, journal_id=None):
        new_invoices = super(account_invoice, self).refund(date, period_id, description, journal_id)
        new_invoices.write({'origin_refund_invoice_id': self.id})
        self.write({'refund_invoice_id': new_invoices.id})
        msg = _('Invoice %s was refunded by %s') % (self.get_link(self), self.get_link(new_invoices))
        self.message_post(body=msg)
        new_invoices.message_post(body=msg)
        return new_invoices

    @api.multi
    def unlink(self):
        for invoice in self:
            for picking in invoice.picking_ids:
                picking.write({'invoice_state': '2binvoiced'})

        res = super(account_invoice, self).unlink()
        return res

    @api.multi
    def action_cancel_pickings(self):
        for invoice in self:
            for picking in invoice.picking_ids:
                if picking.refund_picking_id or picking.origin_refund_picking_id:
                    continue

                return_obj = self.env['stock.return.picking'].with_context({'active_id': picking.id,
                                                                            'default_make_new_picking': False,
                                                                            'default_do_transfer': True}).create({})

                new_picking_id, pick_type_id = return_obj._create_returns()

                new_picking = self.env['stock.picking'].browse(new_picking_id)
                new_picking.write({'invoice_id': invoice.id,
                                   'invoice_state': 'invoiced', })
                if new_picking.sale_id:
                    new_picking.sale_id.write({'invoice_ids': [(4, invoice.id)]})

                purchase = self.env['purchase.order']
                for move in new_picking.move_lines:
                    if move.purchase_line_id and move.purchase_line_id.order_id:
                        purchase = purchase | move.purchase_line_id.order_id
                if purchase:
                    purchase.write({'invoice_ids': [(4, invoice.id)]})

                # de vazut cum pun referinta facturii si in comanda de achizitie!
                msg = _('Picking list %s was refunded by %s') % (self.get_link(picking), self.get_link(new_picking))
                invoice.message_post(body=msg)

    # poate ca nu trebuie sa se permita anularea nu modificarea starii din anulat in validat
    """    
    @api.multi
    def action_cancel_draft(self):
        for invoice in self:
            for picking in invoice.picking_ids:
                if  picking.with_refund:
                    raise Warning(_('Picking list %s was refunded') % picking.name)
            
        return super(account_invoice,self).action_cancel_draft()
     """

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
