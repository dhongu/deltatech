# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "name" not in vals or vals["name"] in ["/", "", False]:
                journal = self.env["account.journal"].browse(vals["journal_id"])
                if journal.statement_sequence_id:
                    vals["name"] = journal.statement_sequence_id.next_by_id()
                else:
                    vals["name"] = fields.Date.to_string(fields.Date.today())
        return super(AccountBankStatement, self).create(vals_list)

    def name_get(self):
        result = super(AccountBankStatement, self).name_get()
        for res in result:
            if res[1] == "/":
                statement = self.filtered(lambda p: p.id == res[0])
                res = (statement.id, fields.Date.to_string(statement.date))
        return result


# class AccountReconciliation(models.AbstractModel):
#     _inherit = "account.reconciliation.widget"
#
#     @api.model
#     def _prepare_move_lines(self, move_lines, target_currency=False, target_date=False, recs_count=0):
#         move_lines = move_lines.sorted(key=lambda r: r.date_maturity)
#         return super(AccountReconciliation, self)._prepare_move_lines(
#             move_lines, target_currency, target_date, recs_count
#         )


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    payment_id = fields.Many2one("account.payment")
