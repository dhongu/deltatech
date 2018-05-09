# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    # @api.model
    # def _default_journal(self):
    #
    #     if self._context.get('default_journal_id', False):
    #         return self.env['account.journal'].browse(self._context.get('default_journal_id'))
    #
    #     if not self._context.get('active_ids'):
    #         return False
    #
    #     company_id = self._context.get('company_id', self.env.user.company_id.id)
    #     domain = [('type', '=', 'sale'), ('company_id', '=', company_id)]
    #
    #     sale_obj = self.env['sale.order']
    #     order = sale_obj.browse(self._context.get('active_ids'))[0]
    #     if order and order.pricelist_id and order.pricelist_id.currency_id:
    #         if order.pricelist_id.currency_id != self.env.user.company_id.currency_id:
    #             domain += [('currency_id', '=', order.pricelist_id.currency_id.id)]
    #
    #     return self.env['account.journal'].search(domain, limit=1)

    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type', '=', 'sale')]")
    order_id = fields.Many2one('sale.order')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')

    @api.model
    def default_get(self, fields):
        defaults = super(SaleAdvancePaymentInv, self).default_get(fields)
        if self._context.get('active_ids'):

            order = self.env['sale.order'].browse(self._context.get('active_ids'))[0]
            defaults['order_id'] = order.id
            defaults['payment_term_id'] = order.payment_term_id.id
            defaults['advance_payment_method'] = self._get_advance_payment_method()

            if order.payment_term_id and order.payment_term_id.line_ids[0].value == 'percent':
                defaults['payment_term_id'] = self.env.ref('account.account_payment_term_immediate').id
                if order.invoice_count == 0:
                    defaults['advance_payment_method'] = 'percentage'
                    defaults['amount'] = order.payment_term_id.line_ids[0].value_amount

            company_id = self._context.get('company_id', self.env.user.company_id.id)
            domain = [('type', '=', 'sale'), ('company_id', '=', company_id)]
            if order and order.pricelist_id and order.pricelist_id.currency_id:
                if order.pricelist_id.currency_id != self.env.user.company_id.currency_id:
                    domain += [('currency_id', '=', order.pricelist_id.currency_id.id)]
            journal = self.env['account.journal'].search(domain, limit=1)
            if journal:
                defaults['journal_id'] = journal.id
        return defaults

    @api.multi
    def create_invoices(self):
        new_self = self.with_context(default_journal_id=self.journal_id)
        return super(SaleAdvancePaymentInv, new_self).create_invoices()

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        new_self = self.with_context(default_journal_id=self.journal_id)
        invoice = super(SaleAdvancePaymentInv, new_self)._create_invoice(order, so_line, amount)

        to_currency = self.journal_id.currency_id or self.env.user.company_id.currency_id
        date_eval = invoice.date_invoice or fields.Date.context_today(self)
        from_currency = invoice.currency_id.with_context(date=date_eval)

        if from_currency != to_currency:
            invoice.write({'currency_id': to_currency.id, 'date_invoice': date_eval})
            for line in invoice.invoice_line_ids:
                price_unit = from_currency.compute(line.price_unit, to_currency, round=False)
                line.write({'price_unit': price_unit})
            invoice.compute_taxes()
        if self.advance_payment_method == 'percentage':
            invoice.write({'payment_term_id': False})
        else:
            invoice.write({'payment_term_id': self.payment_term_id.id})

        return invoice

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == 'percentage':
            amount = 0.0
            order = self.order_id
            if order.payment_term_id and order.payment_term_id.line_ids[0].value == 'percent':
                amount = order.payment_term_id.line_ids[0].value_amount
            return {'value': {'amount': amount}}
        return {}
