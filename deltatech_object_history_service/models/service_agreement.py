# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models


class ServiceAgreement(models.Model):
    _inherit = "service.agreement"

    history_count = fields.Integer(compute="_compute_history_number")

    def open_history(self):
        self.ensure_one()
        res = {
            "res_model": "object.history",
            "target": "current",
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "name": _("History"),
            "domain": [["res_id", "=", self.id], ["res_model", "=", "service.agreement"]],
            "context": {"default_res_id": self.id, "default_res_model": "service.agreement"},
        }
        return res

    def _compute_history_number(self):
        for agreement in self:
            histories = self.env["object.history"].search(
                [("res_id", "=", agreement.id), ("res_model", "=", "service.agreement")]
            )
            if histories:
                agreement.history_count = len(histories)
            else:
                agreement.history_count = False
