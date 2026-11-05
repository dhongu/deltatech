# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # Avansuri de trezorerie
    # account_cash_advances_id = fields.Many2one("account.account", string="Cash advances")

    expenses_no_payment_moves = fields.Boolean(
        string="Advance and Settlement via Bank Statement / Cash Register",
        help="Expense reports paid through this journal (cash register, bank or company card) book only the "
        "expenses on 542, with the employee as partner. The money handed to the employee and the refunds are "
        "recorded from the cash register or the bank statement of this journal, reconciled on 542; the balance "
        "is followed per employee on the 542 ledger, not per expense report.",
    )

    def write(self, vals):
        res = super().write(vals)
        if "expenses_no_payment_moves" in vals:
            # doar deconturile în Ciornă preiau noua variantă; cele avansate sau finalizate o păstrează
            deductions = (
                self.env["deltatech.expenses.deduction"]
                .sudo()
                .search(
                    [
                        ("state", "=", "draft"),
                        "|",
                        "&",
                        ("settlement_mode", "=", "company_card"),
                        ("card_journal_id", "in", self.ids),
                        "&",
                        ("settlement_mode", "!=", "company_card"),
                        ("journal_id", "in", self.ids),
                    ]
                )
            )
            if deductions:
                self.env.add_to_compute(deductions._fields["no_payment_moves"], deductions)
        return res
