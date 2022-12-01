# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _default_warehouse_id(self):
        warehouse_id = super(SaleOrder, self)._default_warehouse_id()
        default_team_id = self.env.context.get("default_team_id")
        if default_team_id:
            team_id = self.env["crm.team"].browse(default_team_id)
        else:
            team_id = self.env["crm.team"]._get_default_team_id()
        if team_id and team_id.warehouse_id:
            warehouse_id = team_id.warehouse_id
        return warehouse_id

    warehouse_id = fields.Many2one("stock.warehouse", default=_default_warehouse_id)
