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
