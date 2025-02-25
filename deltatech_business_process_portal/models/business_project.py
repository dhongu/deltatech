# ©  2023 Deltatech
# ©  2025 NextERP Romania
# See README.rst file on addons root folder for license details

from odoo import models


class BusinessProject(models.Model):
    _name = "business.project"
    _inherit = ["portal.mixin", "business.project"]

    # pentru portal
    def action_open_bp(self):
        context = self._context.copy()
        if "binary_field_real_user" in context:
            del context["binary_field_real_user"]
        return {
            "view_mode": "form",
            "res_model": "business.project",
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "context": context,
        }

    def action_business_project_sharing_open(self):
        action = self.action_open_bp()

        action["views"] = [
            [
                self.env.ref("deltatech_business_process.view_business_project_form").id,
                "form",
            ]
        ]
        return action
