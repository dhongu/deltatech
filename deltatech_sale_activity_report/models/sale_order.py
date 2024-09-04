# models/sale_order.py
from datetime import datetime

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def write(self, vals):
        res = super().write(vals)
        if self.env.user.has_group("base.group_user") and self.env.user.login != "__system__":
            today = datetime.now().date()
            if self:
                order_id = self.id
            else:
                # in pro forma e-mail wizard, self is empty
                order_id = self.env.context.get("active_id", False)
            existing_record = self.env["sale.order.activity.record"].search(
                [("sale_order_id", "=", order_id), ("change_date", "=", today), ("user_id", "=", self.env.user.id)],
                limit=1,
            )

            if not existing_record:
                self.env["sale.order.activity.record"].create(
                    {
                        "sale_order_id": order_id,
                        "change_date": today,
                        "user_id": self.env.user.id,
                        "state": self.state,
                        "stage": self.stage,
                    }
                )
            else:
                existing_record.write({"state": self.state})
                existing_record.write({"stage": self.stage})
        return res
