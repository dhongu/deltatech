# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models
from odoo.tools.misc import formatLang


class AccountJournal(models.Model):
    _inherit = "account.journal"

    statement_sequence_id = fields.Many2one("ir.sequence", string="Statement Sequence", copy=False)
    auto_statement = fields.Boolean("Auto Statement")

    journal_sequence_id = fields.Many2one("ir.sequence", string="Sequence", copy=False)
    cash_in_sequence_id = fields.Many2one("ir.sequence", string="Sequence for cash in")
    cash_out_sequence_id = fields.Many2one("ir.sequence", string="Sequence for cash out")
    supplier_cash_out_sequence_id = fields.Many2one("ir.sequence", string="Sequence for supplier cash out")

    def get_journal_dashboard_datas(self):
        currency = self.currency_id or self.company_id.currency_id
        amount_field = (
            "balance"
            if (not self.currency_id or self.currency_id == self.company_id.currency_id)
            else "amount_currency"
        )
        account_transfer_sum = 0.0
        if self.company_id.transfer_account_id:
            query = """
            SELECT sum(balance) as balance, sum(amount_currency)  as amount_currency
            FROM account_move_line
            WHERE
             parent_state = 'posted' AND account_id = %s AND date <= %s;
            """
            self.env.cr.execute(query, (self.company_id.transfer_account_id.id, fields.Date.today()))
            query_results = self.env.cr.dictfetchall()
            if query_results and query_results[0].get(amount_field) is not None:
                account_transfer_sum = query_results[0].get(amount_field)

        datas = super().get_journal_dashboard_datas()
        datas["account_transfer_balance"] = formatLang(
            self.env, currency.round(account_transfer_sum) + 0.0, currency_obj=currency
        )
        return datas
