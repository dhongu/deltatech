# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class account_invoice(models.Model):
    _inherit = "account.invoice"

    base_rate = fields.Float(string='Rate', digits=(12, 4), readonly=True, default=0.0,
                             store=False, compute="_compute_base_rate")

    last_currency_rate = fields.Float(string='Currency Rate', digits=(12, 4), default=0.0)
    currency_rate = fields.Float(string='Currency Rate', digits=(12, 4), default=0.0)
    price_currency_id = fields.Many2one('res.currency', string='Price currency', help="Price currency")

    @api.one
    def _compute_base_rate(self):
        if self.price_currency_id and self.price_currency_id != self.currency_id:
            self.base_rate = 1.0
        else:
            self.base_rate = 0.0

    @api.onchange('price_currency_id', 'invoice_date')
    def onchange_price_currency_id(self):
        date_eval = self.env.context.get('date', False) or self.invoice_date or fields.Date.context_today(self)
        to_currency = self.currency_id or self.env.user.company_id.currency_id
        # from_currency = self.env.user.company_id.parallel_currency_id
        from_currency = self.price_currency_id
        if not from_currency:
            if self.type in ['out_invoice', 'out_refund'] and self.partner_id.property_product_pricelist:
                from_currency = self.partner_id.property_product_pricelist.currency_id
            if self.type in ['in_invoice', 'in_refund'] and self.partner_id.property_purchase_currency_id:
                from_currency = self.partner_id.property_purchase_currency_id

        if self.price_currency_id and self.price_currency_id != self.currency_id:
            self.base_rate = 1.0
        else:
            self.base_rate = 0.0

        if to_currency and from_currency:
            from_currency = from_currency.with_context(date=date_eval)
            self.currency_rate = from_currency.compute(self.base_rate, to_currency, round=False)
        else:
            self.currency_rate = self.base_rate
        if not self.last_currency_rate:
            self.last_currency_rate = self.currency_rate

    def get_currency_rate(self):
        ''' La apasarea butonului de actualizare curs valutat'''
        for invoice in self:
            '''
            date_eval = invoice.date_invoice or fields.Date.context_today(self)
            to_currency = invoice.currency_id or self.env.user.company_id.currency_id
            from_currency = invoice.price_currency_id


            if to_currency and from_currency:
                invoice.currency_rate = from_currency.with_context(date=date_eval).compute(1, to_currency, round=False)
            else:
                invoice.currency_rate = 1.0
            '''
            if not invoice.last_currency_rate:
                last_rate = invoice.currency_rate or 1.0
            else:
                last_rate = invoice.last_currency_rate
            advance_payment_product_id = self.env['ir.config_parameter'].sudo(
            ).get_param('sale.default_deposit_product_id', False)
            for line in invoice.invoice_line_ids:
                if advance_payment_product_id and line.product_id.id != int(advance_payment_product_id):
                    line.price_unit = line.price_unit * invoice.currency_rate / last_rate

            invoice.last_currency_rate = invoice.currency_rate

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(account_invoice, self)._onchange_partner_id()

        partner = self.partner_id
        if partner:
            price_currency_id = self.currency_id

            if self.type in ['out_invoice', 'out_refund'] and partner.property_product_pricelist:
                price_currency_id = partner.property_product_pricelist.currency_id
            if self.type in ['in_invoice', 'in_refund'] and partner.property_purchase_currency_id:
                price_currency_id = partner.property_purchase_currency_id
            self.price_currency_id = price_currency_id

        return res


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(account_invoice_line, self)._onchange_product_id()
        invoice = self.invoice_id
        if self.invoice_id.currency_rate:
            currency = self.invoice_id.currency_id.with_context(fix_rate=self.invoice_id.currency_rate)
        else:
            currency = self.invoice_id.currency_id

        partner = self.invoice_id.partner_id
        if self.product_id:
            product = self.product_id
            qty = self.quantity

            price_unit = self.price_unit
            if invoice.type == 'out_invoice' and partner.property_product_pricelist:
                pricelist = partner.property_product_pricelist
                price_unit = pricelist.get_product_price(product, qty, partner,
                                                         date=invoice.date or fields.Date.today())
                from_currency = partner.property_product_pricelist.currency_id or self.env.user.company_id.currency_id

                if currency and from_currency:
                    price_unit = from_currency.compute(price_unit, currency)
                self.price_unit = price_unit

            if invoice.type == 'in_invoice' and partner.property_purchase_currency_id:
                from_currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id
                if currency and from_currency:
                    price_unit = from_currency.compute(price_unit, currency)
                self.price_unit = price_unit

            if product.type == 'product':
                raise UserError(_("Please not edit stock products here"))
        return res
