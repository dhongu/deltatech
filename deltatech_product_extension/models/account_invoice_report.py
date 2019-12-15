# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    manufacturer = fields.Many2one('res.partner', string='Manufacturer', readonly=True)

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select() + ', sub.manufacturer'
        return select_str

    def _sub_select(self):
        select_str = super(AccountInvoiceReport, self)._sub_select() + ', pt.manufacturer'
        return select_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by() + ', pt.manufacturer'
        return group_by_str
