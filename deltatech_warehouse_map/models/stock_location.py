from odoo import models


class StockLocation(models.Model):
    _inherit = "stock.location"

    def action_open_map(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "name": "Warehouse Map",
            "target": "self",
            "url": f"/deltatech/warehouse_map/location/{self.id}",
        }
