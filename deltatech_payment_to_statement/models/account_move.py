# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        if "state" in vals and vals.get("state") == "posted":
            for move in self:
                if move.journal_id.journal_sequence_id:
                    new_number = move.journal_id.journal_sequence_id.next_by_id()
                    super(AccountMove, move).write({"name": new_number})

        return super(AccountMove, self).write(vals)
