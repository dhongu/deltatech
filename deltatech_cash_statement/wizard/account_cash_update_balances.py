# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountCashUpdateBalances(models.TransientModel):
    _name = "account.cash.update.balances"
    _description = "Account Cash Update Balances"

    balance_start = fields.Float(string="Starting Balance", digits="Account")

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids", False)
        statement = False
        if active_ids:
            statement = self.env["account.bank.statement"].search(
                [("id", "in", active_ids), ("state", "in", ["open", "posted"])], order="date", limit=1
            )
            if statement:
                defaults["balance_start"] = statement.balance_start
        if not statement:
            raise UserError(_("Please select only Open or Posted statements"))
        return defaults

    def do_update_balance(self):
        active_ids = self.env.context.get("active_ids", False)

        if active_ids:
            statements = self.env["account.bank.statement"].search(
                [("id", "in", active_ids), ("state", "in", ["open", "posted"])], order="date"
            )
            balance_start = self.balance_start
            for statement in statements:
                statement.write({"balance_start": balance_start})
                statement.write({"balance_end_real": statement.balance_end})
                balance_start = statement.balance_end
