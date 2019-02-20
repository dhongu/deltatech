# -*- coding: utf-8 -*-
# ©  2017-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_TIME_FORMAT
import time
from datetime import datetime


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    purchase_price = fields.Float(string='Cost Price',
                                  compute="_compute_purchase_price", store=True,
                                  digits=dp.get_precision('Product Price'))  # valoare stocului in moneda companiei
    commission = fields.Float(string="Commission", default=0.0)


    @api.one
    @api.depends('product_id')
    def _compute_purchase_price(self):
        if not self.product_id:
            return
        to_cur = self.invoice_id.currency_id
        product_uom = self.uom_id
        date_invoice = self.invoice_id.date_invoice
        if self.sale_line_ids:
            purchase_price = 0
            for line in self.sale_line_ids:
                frm_cur = line.order_id.currency_id
                price = line.product_uom._compute_price(line.purchase_price, product_uom)
                price = frm_cur.with_context(date=date_invoice).compute(price, to_cur, round=False)
                purchase_price += price
            purchase_price = purchase_price / len(self.sale_line_ids)
        else:
            frm_cur = self.env.user.company_id.currency_id

            purchase_price = self.product_id.standard_price
            purchase_price = self.product_id.uom_id._compute_price(purchase_price, product_uom)

            purchase_price = frm_cur.with_context(date=date_invoice).compute(purchase_price, to_cur, round=False)

        self.purchase_price = purchase_price




    @api.one
    @api.constrains('price_unit', 'purchase_price')
    def _check_sale_price(self):
        if self.invoice_id.type == 'out_invoice':
            if not self.env['res.users'].has_group('deltatech_sale_margin.group_sale_below_purchase_price'):
                date_eval = self.invoice_id.date_invoice or fields.Date.context_today(self)
                if self.invoice_id.currency_id and self.invoice_id.currency_id.id != self.env.user.company_id.currency_id.id:
                    from_currency = self.invoice_id.currency_id.with_context(date=date_eval)
                    price_unit = from_currency.compute(self.price_unit, self.env.user.company_id.currency_id)
                else:
                    price_unit = self.price_unit
                if price_unit < self.purchase_price and self.purchase_price > 0 and self.invoice_id.state in ['draft']:
                    raise Warning(_('You can not sell below the purchase price.'))


