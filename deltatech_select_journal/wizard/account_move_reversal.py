# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def default_get(self, fields):
        res = super().default_get(fields)
        move_ids = (
            self.env["account.move"].browse(self.env.context["active_ids"])
            if self.env.context.get("active_model") == "account.move"
            else self.env["account.move"]
        )
        if len(move_ids) == 1:
            journal_id = move_ids.journal_id
            if journal_id.refund_sequence and journal_id.refund_journal_id:
                res.update({"journal_id": journal_id.refund_journal_id.id})
        return res
