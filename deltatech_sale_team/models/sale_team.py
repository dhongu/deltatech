# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    warehouse_id = fields.Many2one("stock.warehouse", string="Default Warehouse")

    def action_primary_channel_button(self):
        action = super(CrmTeam, self).action_primary_channel_button()
        if action and "context" in action:
            action["context"]["default_warehouse_id "] = self.warehouse_id.id
        return action

    def show_products(self):
        self.ensure_one()
        action = self.env.ref("stock.product_template_action_product").read()[0]

        action["context"] = {"warehouse": self.warehouse_id.id, "search_default_real_stock_available": 1}
        return action

    def show_validated_quotations(self):
        self.ensure_one()
        action = self.env.ref("sale.action_quotations_salesteams").read()[0]
        action["domain"] = [("state", "=", "sent")]
        action["context"] = {
            "search_default_team_id": [self.id],
            "default_team_id": self.id,
            "show_address": 1,
            "search_default_draft": False,
            "search_default_sent": True,
        }
        return action
