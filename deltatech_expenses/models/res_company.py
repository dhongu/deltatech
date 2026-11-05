# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    expenses_no_payment_moves = fields.Boolean(
        string="Advance and Settlement via Bank Statement / Cash Register",
        help="The expense report books only the expenses on 542 (employee as partner). The money handed to "
        "the employee and the refunds are recorded from the cash register or the bank statement, reconciled "
        "on 542; the balance is followed per employee on the 542 ledger, not per expense report.",
    )

    @api.constrains("expenses_no_payment_moves")
    def _check_expenses_no_payment_moves(self):
        # un decont în starea Avans are nota de avans pe decont: fără note de plată nu s-ar mai putea finaliza
        for company in self.filtered("expenses_no_payment_moves"):
            pending = (
                self.env["deltatech.expenses.deduction"]
                .sudo()
                .search([("company_id", "=", company.id), ("state", "=", "advance")])
            )
            if pending:
                raise ValidationError(
                    self.env._(
                        "The option Advance and Settlement via Bank Statement / Cash Register cannot be enabled "
                        "for %(company)s while expense reports are in the Advance state: finalize them first "
                        "(%(numbers)s).",
                        company=company.name,
                        numbers=", ".join(pending.mapped("number")[:10]),
                    )
                )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    expenses_no_payment_moves = fields.Boolean(related="company_id.expenses_no_payment_moves", readonly=False)
