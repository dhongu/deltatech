# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    history_count = fields.Integer(compute="_compute_history_number")

    def open_history(self):
        self.ensure_one()
        res = {
            "res_model": "object.history",
            "target": "current",
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "name": _("History"),
            "domain": [["res_id", "=", self.id], ["res_model", "=", "service.equipment"]],
            "context": {"default_res_id": self.id, "default_res_model": "service.equipment"},
        }
        return res

    def _compute_history_number(self):
        for equipment in self:
            histories = self.env["object.history"].search(
                [("res_id", "=", equipment.id), ("res_model", "=", "service.equipment")]
            )
            if histories:
                equipment.history_count = len(histories)
            else:
                equipment.history_count = False
