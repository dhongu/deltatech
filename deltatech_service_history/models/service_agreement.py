# ©  2015-2021 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ServiceAgreement(models.Model):
    _inherit = "service.agreement"

    common_history_ids = fields.One2many("common.history", "agreement_id", string="Agreement History")

    def common_history_button(self):
        common_histories = self.common_history_ids
        return {
            "domain": "[('id','in', [" + ",".join(map(str, common_histories.ids)) + "])]",
            "name": "History",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "common.history",
            "view_id": False,
            "type": "ir.actions.act_window",
        }
