# ©  2023-now Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, models


class Partner(models.Model):
    _inherit = "res.partner"

    def open_history(self):
        self.ensure_one()
        res = {
            "res_model": "object.history",
            "target": "current",
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "name": _("History"),
            "domain": [["res_id", "=", self.id], ["res_model", "=", "res.partner"]],
        }
        return res
