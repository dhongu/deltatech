# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _

from odoo.exceptions import Warning, RedirectWarning


class account_move_line(models.Model):
    _inherit = "account.move.line"

    payment_date = fields.Date(string="Payment Date", compute="_compute_payment_days", store=True)
    payment_days = fields.Integer(string="Payment Days", compute="_compute_payment_days", store=True)

    @api.depends('date', 'full_reconcile_id') #   reconcile_id in 8, full_reconcile_id in 12
    def _compute_payment_days(self):
        for aml in self:
            if aml.full_reconcile_id and aml.journal_id.type in ['sale', 'purchase', 'sale_refund', 'purchase_refund']:
                if aml.debit > 0:
                    for line in aml.full_reconcile_id.reconciled_line_ids:
                        if line.credit > 0:
                            payment_date = line.date
                            break
                if aml.credit > 0:
                    for line in aml.full_reconcile_id.reconciled_line_ids:
                        if line.debit > 0:
                            payment_date = line.date
                            break
                aml.payment_date = payment_date
            if aml.payment_date:
                diff = fields.Date.from_string(aml.payment_date) - fields.Date.from_string(aml.date)
                aml.payment_days = diff.days
