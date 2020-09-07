# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)

        if line.order_id.invoice_after_sale:
            if line.product_id.purchase_method != 'purchase':
                remaining_qty = 0.0
                for move in line.move_ids:
                    remaining_qty += move.remaining_qty

                # todo: de covertit in unitatea de achizitie

                qty = line.qty_received - remaining_qty - line.qty_invoiced
                if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
                    qty = 0.0

                data['price_unit'] = line.order_id.currency_id.with_context(date=self.invoice_date).compute(
                    line.price_unit, self.currency_id, round=False)
                data['quantity'] = qty

        return data

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        res = super(AccountInvoice, self).purchase_order_change()
        for line in self.invoice_line_ids:
            if line.quantity == 0:
                self.invoice_line_ids -= line
