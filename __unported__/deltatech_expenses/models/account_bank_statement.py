from odoo import api, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    expenses_deduction_id = fields.Many2one("deltatech.expenses.deduction")
    # daca se anuleaza redeschide un registru de casa se va utiliz acest cont
    backup_counterpart_account_id = fields.Many2one("account.account", string="Account")

    @api.model
    def _prepare_counterpart_move_line_vals(self, counterpart_vals, move_line=None):
        if self.backup_counterpart_account_id:
            counterpart_vals["account_id"] = self.backup_counterpart_account_id.id
        res = super(AccountBankStatementLine, self)._prepare_counterpart_move_line_vals(counterpart_vals, move_line)

        return res
