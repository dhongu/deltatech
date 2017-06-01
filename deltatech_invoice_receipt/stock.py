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

from datetime import date, datetime
from dateutil import relativedelta

import time
from openerp.exceptions import except_orm, Warning, RedirectWarning
 
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import SUPERUSER_ID, api

import openerp.addons.decimal_precision as dp


class stock_move(models.Model):
    _inherit = 'stock.move' 

    # metoda standard copiata si am comentat actualizarea pretului
    def _store_average_cost_price(self, cr, uid, move, context=None):
        ''' move is a browe record '''
        product_obj = self.pool.get('product.product')
        if any([q.qty <= 0 for q in move.quant_ids]) or move.product_qty == 0:
            #if there is a negative quant, the standard price shouldn't be updated
            return
        #Note: here we can't store a quant.cost directly as we may have moved out 2 units (1 unit to 5€ and 1 unit to 7€) and in case of a product return of 1 unit, we can't know which of the 2 costs has to be used (5€ or 7€?). So at that time, thanks to the average valuation price we are storing we will svaluate it at 6€
        average_valuation_price = 0.0
        for q in move.quant_ids:
            average_valuation_price += q.qty * q.cost
        average_valuation_price = average_valuation_price / move.product_qty
        # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
        ctx = dict(context or {}, force_company=move.company_id.id)
        #product_obj.write(cr, SUPERUSER_ID, [move.product_id.id], {'standard_price': average_valuation_price}, context=ctx)
        product = product_obj.browse(cr, SUPERUSER_ID, [move.product_id.id] )
        if average_valuation_price <> product.standard_price:
            msg = _('Computed price must to be:  %s') %  str(average_valuation_price)
            product_obj.message_post(cr, uid, [move.product_id.id], body=msg)
        
        self.write(cr, uid, [move.id], {'price_unit': average_valuation_price}, context=context) 

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    # ajustare automata a monedei de facturare in conformitate cu moneda din jurnal
    @api.multi
    def action_invoice_create(self,  journal_id, group=False, type='out_invoice' ): 
        for picking in self:
            if picking.state != 'done':
                raise Warning(_("The picking list %s isn't transferred.") % picking.name   )
        invoices = super(stock_picking,self).action_invoice_create( journal_id, group, type )
        
 
        #this = self.with_context(inv_type=type)  # foarte important pt a determina corect moneda
        
        #self = this

        journal = self.env['account.journal'].browse(journal_id)
        obj_invoices = self.env['account.invoice'].browse(invoices)

        to_currency = journal.currency or self.env.user.company_id.currency_id

        for obj_inv in obj_invoices:
            if to_currency == obj_inv.currency_id:
                continue
            from_currency = obj_inv.currency_id.with_context(date=obj_inv.date_invoice)
            if type in ['out_invoice', 'in_invoice']:
                for line in obj_inv.invoice_line:
                    new_price = from_currency.compute(line.price_unit, to_currency)
                    line.write({'price_unit': new_price})

            obj_inv.write(  {'currency_id': to_currency.id} )
            obj_inv.button_compute()

        return invoices


    @api.model 
    def _create_invoice_from_picking(self,  picking, vals):        
        invoice_id = super(stock_picking, self)._create_invoice_from_picking( picking, vals)
        if picking.sale_id:
            picking.sale_id.write( {'invoice_ids': [(4, invoice_id)]})
        picking.write({'invoice_id':invoice_id})
         
        return invoice_id

 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
