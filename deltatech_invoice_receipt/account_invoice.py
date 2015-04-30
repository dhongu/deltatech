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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_TIME_FORMAT
import time 
from datetime import datetime

class account_invoice(models.Model):
    _inherit = "account.invoice"

    # camp pt a indica din ce factura se face stornarea
    origin_refund_invoice_id = fields.Many2one('account.invoice', string='Origin Invoice',   copy=False)
    # camp prin care se indica prin ce factura se face stornarea 
    refund_invoice_id = fields.Many2one('account.invoice', string='Refund Invoice',    copy=False)

    @api.multi
    def onchange_journal_id(self, journal_id=False):
        res = super(account_invoice,self).onchange_journal_id(journal_id)
        msg = self.check_data(journal_id=journal_id, date_invoice=self.date_invoice)
        if msg != '': 
            res['warning'] = {'title':_('Warning'),'message':msg}          
        return res
    
    @api.multi
    def onchange_payment_term_date_invoice(self, payment_term_id, date_invoice):    
        res = super(account_invoice,self).onchange_payment_term_date_invoice(payment_term_id, date_invoice)
        msg =  self.check_data(journal_id=self.journal_id.id, date_invoice=date_invoice)
        if msg != '':
            res['warning'] = {'title':_('Warning'),'message':msg}
        return res

    @api.multi    
    def check_data(self, journal_id=None, date_invoice=None):
        
        for obj_inv in self:
            inv_type = obj_inv.type
            number = obj_inv.number
            date_invoice = date_invoice or obj_inv.date_invoice
            journal_id = journal_id or obj_inv.journal_id.id
         
            if inv_type == 'out_invoice' or inv_type == 'out_refund':
                res = self.search(  [('type','=',inv_type),
                                     ('date_invoice','>',date_invoice), 
                                     ('journal_id', '=', journal_id)  ],
                                  limit = 1,
                                  order = 'date_invoice desc')
                if res:                
                    lang = self.env['res.lang'].search([('code','=',self.env.user.lang)])                       
                    date_invoice = datetime.strptime(res.date_invoice, DEFAULT_SERVER_DATE_FORMAT).strftime(lang.date_format.encode('utf-8'))
                    return  _('Post the invoice with a greater date than %s') % date_invoice
        return ''
    
       
    @api.multi
    def action_number(self):
        msg = self.check_data()
        if msg != '':
            raise except_orm(_('Date Inconsistency'), msg )            
        super(account_invoice, self).action_number()
        return True

    @api.multi
    @api.returns('self')
    def refund(self, date=None, period_id=None, description=None, journal_id=None):
        new_invoices = super(account_invoice, self).refund(date, period_id, description,journal_id )
        new_invoices.write({'origin_refund_invoice_id':self.id})
        self.write({'refund_invoice_id':new_invoices.id})
        return new_invoices        
        
    @api.multi
    def invoice_create_receipt(self):
        
        #trebuie sa verific ca factura nu este generata dintr-un flux normal de achiztie !!
        if self.type != 'in_invoice': 
            return
        
        if self.amount_total < 0: 
            if self.origin_refund_invoice_id:
                for picking in self.origin_refund_invoice_id.picking_ids:
                    return_obj = self.env['stock.return.picking'].with_context({'active_id':picking.id}).create({})
                    new_picking_id, pick_type_id  = return_obj._create_returns()
                    new_picking = self.env['stock.picking'].browse(new_picking_id)
                    new_picking.write({'invoice_id':self.id,
                                       'invoice_state':'invoiced',})   
                    #TODO: si la fiecare miscare trebuie sa trec care este linia din factura ....
            return             
        
        date_eval = self.date_invoice or fields.Date.context_today(self) 
        date_receipt = date_eval + ' ' + time.strftime(DEFAULT_SERVER_TIME_FORMAT)
        from_currency = self.currency_id.with_context(date=date_eval)
         
        # trebuie definita o matrice in care sa salvez liniile din factura impreuna cu cantitatile aferente.
        lines = []
        for line in self.invoice_line:
            if line.product_id.type == 'product': 
                purchase_line_ids = self.env['purchase.order.line'].search([('invoice_lines','=', line.id)])
                ok = True
                if purchase_line_ids:
                    # oare sunt facute receptii de aceste  comenzi (factura generata din comanda sau din linii de comanda)
                    for move in purchase_line_ids.move_ids:
                        if move.state == 'done':                       # dar daca am receptii partiale pe aceasta linie ???
                            ok = False
                if ok:             
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    lines.append({'invoice_line': line,
                                  'product_id':line.product_id,
                                  'quantity':  line.quantity,
                                  'price_unit':  from_currency.compute(price, self.env.user.company_id.currency_id )
                                   })                  # pretul trebuie convertit in moneda codului de companie!!     
        
        if not lines:
            return
 
        # se va completa la produsele stocabile contul 408
        account_id = self.company_id and self.company_id.property_stock_picking_payable_account_id and self.company_id.property_stock_picking_payable_account_id.id 
        if account_id:
            for line in lines:
                line['invoice_line'].write({'account_id':account_id})
 
         # caut  picking listurile pregatite pt receptie de la acest furnizor
        domain=[('state', '=', 'assigned'),('partner_id','=',self.partner_id.id)]
        pickings = self.env['stock.picking'].search(domain, order='date ASC',) 
        if not pickings:
            raise except_orm(_('Picking not found!'),
                             _('No purchase orders from this supplier'))
        
        # caut liniile care au cantitate zero si nu sunt anulate si le anulez
        for picking in pickings:
            for move in picking.move_lines:
                if move.product_uom_qty == 0 and move.state == 'assigned':
                    move.write({'state':'cancel'})
 
        # pregatire picking list pentru receptii partiale
        for picking in pickings:
            if not picking.pack_operation_exist:
                picking.do_prepare_partial()
            
        # memorez intr-o lista operatiile pregatite de receptie
        operations = []
        for picking in pickings:
            if picking.picking_type_id.code == 'incoming':
                for op in picking.pack_operation_ids:
                    operations.append({'picking':picking,
                                       'op':op,
                                       'product_qty':op.product_qty,})
    
    
        new_picking_line = []
        
        is_ok = True
        while is_ok:                     
            is_ok = False
            for line in lines:
                if line['quantity'] > 0 :
                    for operation in operations:
                        op = operation['op']
                        if operation['product_qty'] > 0 and line['quantity'] > 0 and op.product_id.id == line['product_id'].id:
                            # am gasit o line de comanda din care se poate scade o cantitate  
                            is_ok = True                                                                   
                            if operation['product_qty'] >= line['quantity']:
                                new_picking_line.append({'picking':operation['picking'],
                                                         'operation':op,
                                                         'product_id':op.product_id, 
                                                         'product_qty':line['quantity'],
                                                         'price_unit':line['price_unit'],
                                                         'invoice_line': line['invoice_line']})
                                 
                                qty = line['quantity']
                                line['quantity'] = 0 
                            else:
                                new_picking_line.append({'picking':operation['picking'],
                                                         'operation':op,
                                                         'product_id':op.product_id, 
                                                         'product_qty':operation['product_qty'],
                                                         'price_unit':line['price_unit'],
                                                         'invoice_line': line['invoice_line']})
                                qty = operation['product_qty']
                                line['quantity'] =  line['quantity'] - operation['product_qty']
                            operation['product_qty'] = operation['product_qty'] - qty
        
        for line in lines:
           if line['quantity'] > 0:
               raise except_orm(_('Picking not found!'),
                                _('No purchase orders line from product %s in quantity of %s ') % (line['product_id'].name, line['quantity'] )  )
            
        # sa incepem receptia
        processed_ids = []
        purchase_line_ids = []
        for line in new_picking_line:
            op = line['operation']
            op.write({'product_qty': line['product_qty'],
                      'date':date_receipt}) 
            processed_ids.append(op.id)    
            for link in op.linked_move_operation_ids:
                purchase_line_ids.append(link.move_id.purchase_line_id)
                link.move_id.write({
                                    'price_unit': line['price_unit'],
                                    'date_expected': date_receipt ,
                                    'invoice_line_id':line['invoice_line'].id,
                                    })
                
                if line['product_id'].cost_method == 'real' and  line['product_id'].standard_price <> line['price_unit']:
                    line['product_id'].write({'standard_price':line['price_unit']})   # actualizare pret cu ultimul pret din factura!!
                    
                link.move_id.purchase_line_id.write({'invoice_lines': [(4, line['invoice_line'].id)]})
                link.move_id.purchase_line_id.order_id.write({'invoice_ids': [(4, line['invoice_line'].invoice_id.id)]}) 

        for line in new_picking_line:
            if line['picking'].state == 'assigned':
                # Delete the others
                packops = self.env['stock.pack.operation'].search(['&', ('picking_id', '=', line['picking'].id), '!', ('id', 'in', processed_ids)])
                for packop in packops:
                    packop.unlink()                
        origin = ''
        for line in new_picking_line:
            if line['picking'].state == 'assigned': 
                line['picking'].write({'notice': True})                 
                line['picking'].do_transfer()
                line['picking'].write({'date_done': date_receipt,  
                                       'invoice_state':'invoiced',
                                       'invoice_id':self.id,
                                       #'reception_to_invoice':False, 
                                       'origin':self.supplier_invoice_number or line['picking'].origin })
                msg = _('Picking list %s was receipted') % line['picking'].name
                origin = origin + ' '+ line['picking'].name
                self.message_post(body=msg)
        if not self.origin:
            self.write({'origin':origin.strip()})

    @api.model
    def create(self, vals):
        journal_id = vals.get('journal_id',self.default_get(['journal_id'])['journal_id'])
        currency_id = vals.get('currency_id',self.default_get(['currency_id'])['currency_id'])
        
        
        if journal_id  and currency_id:
            journal = self.env['account.journal'].browse(journal_id)
            to_currency = journal.currency or self.env.user.company_id.currency_id
            if  to_currency.id != currency_id:
                date_invoice = vals.get('date_invoice', fields.Date.context_today(self))  
                vals['date_invoice'] = date_invoice
                from_currency = self.env['res.currency'].with_context(date=date_invoice).browse(currency_id)
                invoice_line = vals.get('invoice_line',False)
                if invoice_line:
                    for a,b,line in invoice_line:
                        line_obj = self.env['account.invoice.line'].browse(line)
                        if line_obj:
                            line_obj.price_unit  = from_currency.compute( line_obj.price_unit,to_currency)
                        
                    vals['currency_id'] = to_currency.id
        inv_id = super(account_invoice,self).create(vals)
         
        return inv_id
              
class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"


    @api.multi
    def unlink(self):
        # de verificat daca sunt miscari din liste de ridicare care au statusul Facturat!
        res = super(account_invoice_line, self).unlink()
        return res

        
    @api.multi
    # pretul din factura se determina in functie de cursul de schimb din data facturii  
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None):
 
        res = super(account_invoice_line, self).product_id_change(  product, uom_id, qty, name, type,
            partner_id, fposition_id, price_unit, currency_id, company_id)
        
        if product:
            product_obj = self.env['product.product'].browse(product)
            currency = self.env['res.currency'].browse(currency_id)
            part = self.env['res.partner'].browse(partner_id)
            
            if type == 'out_invoice' and  part.property_product_pricelist:
                pricelist_id = part.property_product_pricelist.id
                price_unit = part.property_product_pricelist.price_get(product,qty, partner_id)[pricelist_id]
                from_currency = part.property_product_pricelist.currency_id or self.env.user.company_id.currency_id
                if currency and  from_currency:
                    res['value']['price_unit'] = from_currency.compute(price_unit, currency)
    
            if type == 'in_invoice' and part.property_product_pricelist_purchase:
                pricelist_id = part.property_product_pricelist_purchase.id
                price_unit = part.property_product_pricelist_purchase.price_get(product,qty, partner_id )[pricelist_id]
                from_currency = part.property_product_pricelist_purchase.currency_id or self.env.user.company_id.currency_id
                if currency and  from_currency:
                    res['value']['price_unit'] = from_currency.compute(price_unit, currency)

            # oare e bine sa las asa ?????
            # cred ca mai trebuie pus un camp in produs prin care sa se specifice clar care din produse intra prin 408
            if type == 'in_invoice':
                account_id = self.env.user.company_id and self.env.user.company_id.property_stock_picking_payable_account_id and self.env.user.company_id.property_stock_picking_payable_account_id.id
                if  product_obj.type == 'product' and account_id: 
                    res['value']['account_id'] = account_id
                  
        
        return res     

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:



 