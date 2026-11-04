# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    expenses_no_payment_moves = fields.Boolean(
        string="Expense Reports without Payments",
        help="The expense report books only the expenses on 542 (employee as partner). The money handed to "
        "the employee and the refunds are recorded from the cash register or the bank statement, reconciled "
        "on 542; the balance is followed per employee on the 542 ledger, not per expense report.",
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    expenses_no_payment_moves = fields.Boolean(related="company_id.expenses_no_payment_moves", readonly=False)
