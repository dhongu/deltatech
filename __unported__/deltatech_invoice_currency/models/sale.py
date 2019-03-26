# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        journal = self.env['account.journal'].browse(invoice_vals['journal_id'])
        currency_id = journal.currency_id or self.env.user.company_id.currency_id
        invoice_vals['price_currency_id'] = self.pricelist_id.currency_id.id
        invoice_vals['currency_id'] = currency_id.id

        date_invoice = False
        for picking in self.picking_ids:
            if picking.state == 'done':
                if not date_invoice or date_invoice < picking.scheduled_date:
                    date_invoice = picking.scheduled_date

        date_invoice = date_invoice or fields.Date.context_today(self)
        from_currency = self.pricelist_id.currency_id.with_context(date=date_invoice)
        invoice_vals['currency_rate'] = from_currency.compute(1,  currency_id, round=False)
        invoice_vals['last_currency_rate'] = invoice_vals['currency_rate']
        invoice_vals['date_invoice'] = date_invoice
        # cu obtin data ultimului aviz ?
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # se convertesc facturile in moneda jurnalului
    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        invoice_lines = super(SaleOrderLine, self).invoice_line_create(invoice_id, qty)

        invoice = self.env['account.invoice'].browse(invoice_id)

        to_currency = invoice.journal_id.currency_id or self.env.user.company_id.currency_id
        from_currency = self.order_id.pricelist_id.currency_id


        date_invoice = invoice.date_invoice or fields.Date.context_today(self)
        for line in invoice_lines:
            price_unit = from_currency.with_context(date=date_invoice).compute(line.price_unit, to_currency)
            line.write({'price_unit': price_unit})

        return invoice_lines

