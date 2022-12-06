# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        if "state" in vals and vals.get("state") == "posted":
            for move in self:
                if (not move.name or move.name == "/") and move.journal_id.journal_sequence_id:
                    new_number = move.journal_id.journal_sequence_id.next_by_id()
                    super(AccountMove, move).write({"name": new_number})
        if "payment_id" in vals and vals.get("payment_id"):
            payment_id = self.env["account.payment"].browse(vals.get("payment_id"))
            for move in self:
                if (not move.name or move.name == "/") and payment_id:
                    payment_id.force_cash_sequence()
        return super(AccountMove, self).write(vals)
