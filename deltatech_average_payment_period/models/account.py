# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payment_date = fields.Date(string="Payment Date", compute="_compute_payment_days", store=True)
    payment_days = fields.Integer(string="Payment Days", compute="_compute_payment_days", store=True)
    payment_days_simple = fields.Float(string="Plain payment days", compute="_compute_payment_days_simple", store=True)

    def _get_counterpart_payment_date(self):
        self.ensure_one()
        lines = self.full_reconcile_id.reconciled_line_ids - self
        if self.debit > 0:
            lines = lines.filtered(lambda l: l.credit > 0)
        elif self.credit > 0:
            lines = lines.filtered(lambda l: l.debit > 0)
        else:
            return False
        return max(lines.mapped("date"), default=False)

    @api.depends(
        "date",
        "debit",
        "credit",
        "journal_id.type",
        "full_reconcile_id",
        "full_reconcile_id.reconciled_line_ids.date",
        "full_reconcile_id.reconciled_line_ids.debit",
        "full_reconcile_id.reconciled_line_ids.credit",
    )
    def _compute_payment_days(self):
        for aml in self:
            payment_date = False
            if aml.full_reconcile_id and aml.journal_id.type in ("sale", "purchase"):
                payment_date = aml._get_counterpart_payment_date()
            aml.payment_date = payment_date
            aml.payment_days = (payment_date - aml.date).days if payment_date and aml.date else 0

    @api.depends(
        "date",
        "full_reconcile_id",
        "move_id.payment_state",
        "debit",
        "credit",
        "move_id.move_type",
        "parent_state",
        "full_reconcile_id.reconciled_line_ids.date",
        "full_reconcile_id.reconciled_line_ids.debit",
        "full_reconcile_id.reconciled_line_ids.credit",
    )
    def _compute_payment_days_simple(self):
        for aml in self:
            aml.payment_days_simple = 0.0
            if aml.full_reconcile_id:
                if aml.move_id.move_type in ["out_invoice", "in_invoice"] and aml.parent_state == "posted":
                    payment_date = aml._get_counterpart_payment_date()
                    if payment_date and aml.date:
                        diff = payment_date - aml.date
                        aml.payment_days_simple = diff.days


class AccountFullReconcile(models.Model):
    _inherit = "account.full.reconcile"

    @api.model_create_multi
    def create(self, vals_list):
        fulls = super().create(vals_list)
        # nucleul setează full_reconcile_id prin SQL; marcăm câmpurile dependente pentru recalculare
        fulls.reconciled_line_ids.modified(["full_reconcile_id"])
        return fulls
