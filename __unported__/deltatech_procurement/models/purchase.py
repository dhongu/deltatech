# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
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


from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    procurement_count = fields.Integer(string='Procurements', compute='_compute_procurement_count')
    invoiced_rate = fields.Float(compute='_compute_invoiced_rate')  # string='Invoiced Ratio',
    invoiced = fields.Boolean(compute='_compute_invoiced')

    @api.one
    @api.depends('order_line.procurement_ids')
    def _compute_procurement_count(self):
        value = 0
        procurements = self.env['procurement.order']
        for po in self:
            for line in po.order_line:
                for procurement in line.procurement_ids:
                    procurements = procurements | procurement
        self.procurement_count = len(procurements)

    @api.one
    @api.depends('invoice_ids.amount_untaxed', 'amount_untaxed')
    def _compute_invoiced_rate(self):

        if self.currency_id:
            to_currency = self.currency_id
        else:
            to_currency = self.env.user.company_id.currency_id

        if self.amount_untaxed:
            invoice_tot = 0.0
            for invoice in self.invoice_ids:
                if invoice.state not in ('draft', 'cancel'):
                    if invoice.currency_id:
                        from_currency = invoice.currency_id.with_context(date=invoice.date_invoice)
                    else:
                        from_currency = self.env.user.company_id.currency_id.with_context(date=invoice.date_invoice)

                    value = invoice.amount_untaxed
                    if invoice.type == 'in_refund':
                        value = -value
                    invoice_tot += from_currency.compute(value, to_currency)

            self.invoiced_rate = min(100.00, invoice_tot * 100.0 / (self.amount_untaxed or 1.00))
        else:
            self.invoiced_rate = 0.0

    # todo: sa tina cont si de facturile rambursate
    @api.one
    @api.depends('invoice_ids')
    def _compute_invoiced(self):
        self.invoiced = False
        for invoice in self.invoice_ids:
            if invoice.state == 'paid' and not (invoice.origin_refund_invoice_id or invoice.refund_invoice_id):
                self.invoiced = True

    @api.multi
    def view_procurement(self):
        '''
        This function returns an action that display existing procurement of given purchase order ids.
        '''
        action = self.env.ref('procurement.procurement_action')
        result = action.read()[0]

        procurement_ids = self.env['procurement.order']
        for order in self:
            for line in order.order_line:
                procurement_ids |= line.procurement_ids

        result['context'] = {}

        if len(procurement_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, procurement_ids.ids)) + "])]"
        else:
            res = self.env.ref('procurement.procurement_form_view')
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = procurement_ids.id
        return result

    @api.multi
    def view_to_be_received(self):
        '''
        This function returns an action that display existing move  .
        '''
        action = self.env.ref('stock.stock_move_action')
        result = action.read()[0]

        move_ids = []

        for order in self:
            for line in order.order_line:
                for procurement in line.procurement_ids:
                    move_ids += [move.id for move in procurement.move_ids if move.state in ['assigned', 'waiting', 'confirmed']]

        result['context'] = {}

        if len(move_ids) >= 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, move_ids)) + "])]"
        else:
            res = self.env.ref('stock.view_move_picking_form')
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = move_ids and move_ids[0] or False
        return result

    """ Cod mutat in show_quant
    @api.multi
    def view_current_stock(self):
        action = self.env.ref('stock.product_open_quants').read()[0]
        product_ids = []
        for order in self:
            product_ids += [line.product_id.id for line in order.order_line]
        action['context'] = {'search_default_internal_loc': 1,
                             'search_default_locationgroup': 1}

        action['domain'] = "[('product_id','in',[" + ','.join(map(str, product_ids)) + "])]"
        return action
    """


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
