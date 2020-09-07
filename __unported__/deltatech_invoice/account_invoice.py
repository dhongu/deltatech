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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_TIME_FORMAT
import time
from datetime import datetime


class account_invoice(models.Model):
    _inherit = "account.invoice"

    # nr de facura se poate edita!!
    internal_number = fields.Char(string='Invoice Number', readonly=False)

    base_rate = fields.Float(string='Rate', digits=(12, 4), readonly=True,
                             default=0.0, store=False, compute="_compute_base_rate")
    currency_rate = fields.Float(string='Currency Rate', digits=(12, 4), readonly=True, default=0.0)
    price_currency_id = fields.Many2one('res.currency', string='Price currency', help="Price currency")

    @api.one
    def _compute_base_rate(self):
        if self.price_currency_id and self.price_currency_id != self.currency_id:
            self.base_rate = 1.0
        else:
            self.base_rate = 0.0

    @api.onchange('price_currency_id')
    def onchange_price_currency_id(self):
        date_eval = self.env.context.get('date', False) or self.invoice_date or fields.Date.context_today(self)
        to_currency = self.currency_id or self.env.user.company_id.currency_id
        #from_currency = self.env.user.company_id.parallel_currency_id
        from_currency = self.price_currency_id
        if not from_currency:
            if self.type in ['out_invoice', 'out_refund'] and self.partner_id.property_product_pricelist:
                from_currency = self.partner_id.property_product_pricelist.currency_id
            if self.type in ['in_invoice', 'in_refund'] and self.partner_id.property_product_pricelist_purchase:
                from_currency = self.partner_id.property_product_pricelist_purchase.currency_id

        if to_currency and from_currency:
            self.currency_rate = from_currency.with_context(
                date=date_eval).compute(self.base_rate, to_currency, round=False)
        else:
            self.currency_rate = self.base_rate

    def get_currency_rate(self):
        for invoice in self:
            date_eval = invoice.invoice_date or fields.Date.context_today(self)
            to_currency = invoice.currency_id or self.env.user.company_id.currency_id
            from_currency = invoice.price_currency_id

            if invoice.type in ['out_invoice', 'out_refund'] and invoice.partner_id.property_product_pricelist:
                from_currency = invoice.partner_id.property_product_pricelist.currency_id
            if invoice.type in ['in_invoice', 'in_refund'] and v.partner_id.property_product_pricelist_purchase:
                from_currency = invoice.partner_id.property_product_pricelist_purchase.currency_id
            invoice.price_currency_id = from_currency

            if to_currency and from_currency:
                invoice.currency_rate = from_currency.with_context(date=date_eval).compute(1, to_currency, round=False)
            else:
                invoice.currency_rate = 1

    def onchange_partner_id(self, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        res = super(account_invoice, self).onchange_partner_id(
            type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)

            if type in ['out_invoice', 'out_refund'] and partner.property_product_pricelist:
                price_currency_id = partner.property_product_pricelist.currency_id
            if type in ['in_invoice', 'in_refund'] and partner.property_product_pricelist_purchase:
                price_currency_id = partner.property_product_pricelist_purchase.currency_id
            res['value']['price_currency_id'] = price_currency_id

        return res

    def onchange_journal_id(self, journal_id=False):
        res = super(account_invoice, self).onchange_journal_id(journal_id)
        msg = self.check_data(journal_id=journal_id, date_invoice=self.date_invoice)
        if msg != '':
            res['warning'] = {'title': _('Warning'), 'message': msg}
        return res

    def onchange_payment_term_date_invoice(self, payment_term_id, date_invoice):
        res = super(account_invoice, self).onchange_payment_term_date_invoice(payment_term_id, date_invoice)
        msg = self.check_data(journal_id=self.journal_id.id, date_invoice=date_invoice)
        if msg != '':
            res['warning'] = {'title': _('Warning'), 'message': msg}
        return res

    def check_data(self, journal_id=None, date_invoice=None):

        for obj_inv in self:
            inv_type = obj_inv.type
            number = obj_inv.number
            date_invoice = date_invoice or obj_inv.date_invoice
            journal_id = journal_id or obj_inv.journal_id.id

            if (inv_type == 'out_invoice' or inv_type == 'out_refund') and not obj_inv.internal_number:
                res = self.search([('type', '=', inv_type),
                                   ('date_invoice', '>', date_invoice),
                                   ('journal_id', '=', journal_id),
                                   ('state', 'in', ['open', 'paid'])],
                                  limit=1,
                                  order='date_invoice desc')
                if res:
                    lang = self.env['res.lang'].search([('code', '=', self.env.user.lang)])
                    date_invoice = datetime.strptime(res.date_invoice, DEFAULT_SERVER_DATE_FORMAT).strftime(
                        lang.date_format.encode('utf-8'))
                    return _('Post the invoice with a greater date than %s') % date_invoice
        return ''


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    # pretul din factura se determina in functie de cursul de schimb din data facturii

    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
                          partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
                          company_id=None):

        res = super(account_invoice_line, self).product_id_change(product, uom_id, qty, name, type,
                                                                  partner_id, fposition_id, price_unit, currency_id, company_id)

        if product:
            product_obj = self.env['product.product'].browse(product)
            currency = self.env['res.currency'].browse(currency_id)
            part = self.env['res.partner'].browse(partner_id)

            if type == 'out_invoice' and part.property_product_pricelist:
                pricelist_id = part.property_product_pricelist.id
                price_unit = part.property_product_pricelist.price_get(product, qty, partner_id)[pricelist_id]
                from_currency = part.property_product_pricelist.currency_id or self.env.user.company_id.currency_id

                if currency and from_currency:
                    price_unit = from_currency.compute(price_unit, currency)
                res['value']['price_unit'] = price_unit

            if type == 'in_invoice' and part.property_product_pricelist_purchase:
                pricelist_id = part.property_product_pricelist_purchase.id
                price_unit = part.property_product_pricelist_purchase.price_get(product, qty, partner_id)[pricelist_id]
                from_currency = part.property_product_pricelist_purchase.currency_id or self.env.user.company_id.currency_id

                if currency and from_currency:
                    price_unit = from_currency.compute(price_unit, currency)
                res['value']['price_unit'] = price_unit

            # oare e bine sa las asa ?????
            # cred ca mai trebuie pus un camp in produs prin care sa se specifice clar care din produse intra prin 408
            if type == 'in_invoice':
                if product_obj.type == 'product':
                    account_id = self.env.user.company_id and self.env.user.company_id.property_stock_picking_payable_account_id and self.env.user.company_id.property_stock_picking_payable_account_id.id
                    if not account_id:
                        account_id = product_obj.property_stock_account_input and product_obj.property_stock_account_input.id or False
                        if not account_id:
                            account_id = product_obj.categ_id.property_stock_account_input_categ and product_obj.categ_id.property_stock_account_input_categ.id or False

                    res['value']['account_id'] = account_id

        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
