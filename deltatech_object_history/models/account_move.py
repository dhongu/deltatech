# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    history_count = fields.Integer(compute="_compute_history_number")

    def open_history(self):
        self.ensure_one()
        res = {
            "res_model": "object.history",
            "target": "current",
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "name": _("History"),
            "domain": [["res_id", "=", self.id], ["res_model", "=", "account.move"]],
            "context": {"default_res_id": self.id, "default_res_model": "account.move"},
        }
        return res

    def _compute_history_number(self):
        for move in self:
            histories = self.env["object.history"].search(
                [("res_id", "=", move.id), ("res_model", "=", "account.move")]
            )
            if histories:
                move.history_count = len(histories)
            else:
                move.history_count = False
