# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payment_date = fields.Date(string="Payment Date", compute="_compute_payment_days", store=True)
    payment_days = fields.Integer(string="Payment Days", compute="_compute_payment_days", store=True)
    payment_days_simple = fields.Float(string="Plain payment days", compute="_compute_payment_days_simple", store=True)

    @api.depends("date", "full_reconcile_id")
    def _compute_payment_days(self):
        for aml in self:
            if aml.full_reconcile_id and aml.journal_id.type in ["sale", "purchase", "sale_refund", "purchase_refund"]:
                payment_date = False
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

    @api.depends("date", "full_reconcile_id")
    def _compute_payment_days_simple(self):
        for aml in self:
            try:
                if aml.full_reconcile_id:
                    if aml.move_id.move_type in ["out_invoice", "in_invoice"] and aml.parent_state == "posted":
                        payment_date = False
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
                        if payment_date:
                            diff = payment_date - aml.date
                            aml.payment_days_simple = diff.days
            except Exception as e:
                _logger.info(f"Compute payment days failed for id {aml.move_id.id}: {e}")
