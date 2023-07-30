# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        if "state" in vals and vals.get("state") == "posted":
            for move in self:
                if (not move.name or move.name == "/" or move.name == _("New")) and move.journal_id.journal_sequence_id:
                    if move.payment_id:
                        payment_id = self.env["account.payment"].browse(move.payment_id.id)
                        payment_id.force_cash_sequence()
                    else:
                        new_number = move.journal_id.journal_sequence_id.next_by_id()
                        super(AccountMove, move).write({"name": new_number})
            if "payment_id" in vals and vals.get("payment_id"):
                payment_id = self.env["account.payment"].browse(vals.get("payment_id"))
                for move in self:
                    if (not move.name or move.name == "/" or move.name == _("New")) and payment_id:
                        payment_id.force_cash_sequence()
        return super(AccountMove, self).write(vals)

    @api.depends("posted_before", "state", "journal_id", "date")
    def _compute_name(self):
        for move in self:
            if (
                not move.journal_id.journal_sequence_id
                or move.posted_before
                or (move.name and move.name != "/" and move.name != _("New"))
            ):
                super(AccountMove, move)._compute_name()
            else:
                move.name = _("New")

    @api.ondelete(at_uninstall=False)
    def _unlink_forbid_parts_of_chain(self):
        moves = self.filtered(lambda move: move.name != _("New"))
        return super(AccountMove, moves)._unlink_forbid_parts_of_chain()
