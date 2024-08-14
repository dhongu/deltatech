# models/sale_order.py
from datetime import datetime

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def write(self, vals):
        res = super().write(vals)
        today = datetime.now().date()
        existing_record = self.env["sale.order.activity.record"].search(
            [("sale_order_id", "=", self.id), ("change_date", "=", today), ("user_id", "=", self.env.user.id)], limit=1
        )

        if not existing_record:
            self.env["sale.order.activity.record"].create(
                {
                    "sale_order_id": self.id,
                    "change_date": today,
                    "user_id": self.env.user.id,
                    "state": self.state,
                }
            )
        else:
            existing_record.write({"state": self.state})
        return res
