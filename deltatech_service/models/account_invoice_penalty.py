# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from datetime import datetime

from odoo import api, fields, models


class Invoice(models.Model):
    _inherit = "account.move"

    penalty = fields.Float(string="Penalty", digits="Account", compute="_compute_penalty")

    @api.depends("payment_term", "date_move", "amount_untaxed")
    def _compute_penalty(self):
        self.penalty = 0.0
        if self.date_due:
            if self.payment_ids:
                effective_date_due = min(payment.date for payment in self.payment_ids)
            else:
                effective_date_due = fields.Date.today()
            if self.date_due < effective_date_due:
                days = (
                    datetime.strptime(effective_date_due, "%Y-%m-%d") - datetime.strptime(self.date_due, "%Y-%m-%d")
                ).days
                self.penalty = self.amount_untaxed * days * 0.01
