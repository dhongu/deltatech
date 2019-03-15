# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        if self.type == 'in_refund':
            if line.product_id.purchase_method == 'purchase':
                qty = line.qty_invoiced - line.product_qty
            else:
                qty = line.qty_invoiced - line.qty_received
            if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
                qty = 0.0
            res['quantity'] = qty
        return res
