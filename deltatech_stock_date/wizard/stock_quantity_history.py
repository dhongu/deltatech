# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class StockQuantityHistory(models.TransientModel):
    _inherit = "stock.quantity.history"

    def open_at_date(self):
        action = super(StockQuantityHistory, self).open_at_date()
        active_model = self.env.context.get("active_model")
        if active_model == "stock.valuation.layer":
            action["domain"] = [("date", "<=", self.inventory_datetime), ("product_id.type", "=", "product")]
            return action

        return action
