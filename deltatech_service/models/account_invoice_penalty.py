# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from datetime import datetime

from odoo import api, fields, models

import odoo.addons.decimal_precision as dp


class Invoice(models.Model):
    _inherit = "account.invoice"

    penalty = fields.Float(string="Penalty", digits=dp.get_precision("Account"), compute="_compute_penalty")

    @api.depends("payment_term", "date_invoice", "amount_untaxed")
    def _compute_penalty(self):
        for invoice in self:
            invoice.penalty = 0.0
            if invoice.date_due:
                if invoice.payment_ids:
                    effective_date_due = min(payment.date for payment in invoice.payment_ids)
                else:
                    effective_date_due = fields.Date.today()
                if invoice.date_due < effective_date_due:
                    days = (
                        datetime.strptime(effective_date_due, "%Y-%m-%d") - datetime.strptime(self.date_due, "%Y-%m-%d")
                    ).days
                    invoice.penalty = invoice.amount_untaxed * days * 0.01
