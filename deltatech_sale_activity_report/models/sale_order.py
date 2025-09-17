# models/sale_order.py
from datetime import datetime

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def write(self, vals):
        res = super().write(vals)
        if self.env.user.has_group("base.group_user") and self.env.user.login != "__system__":
            today = datetime.now().date()
            for order in self:
                order_id = order.id
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
                            "state": order.state,
                            "stage": order.stage,
                        }
                    )
                else:
                    existing_record.write({"state": order.state})
                    existing_record.write({"stage": order.stage})

        return res

    def message_post(self, **kwargs):
        res = super().message_post(**kwargs)
        if self.env.user.has_group("base.group_user") and self.env.user.login != "__system__":
            today = datetime.now().date()
            for order in self:
                existing_record = self.env["sale.order.activity.record"].search(
                    [
                        ("sale_order_id", "=", order.id),
                        ("change_date", "=", today),
                        ("user_id", "=", self.env.user.id),
                    ],
                    limit=1,
                )

                if not existing_record:
                    self.env["sale.order.activity.record"].create(
                        {
                            "sale_order_id": order.id,
                            "change_date": today,
                            "user_id": self.env.user.id,
                            "state": order.state,
                            "stage": order.stage,
                        }
                    )
                else:
                    existing_record.write(
                        {
                            "state": order.state,
                        }
                    )
                    existing_record.write(
                        {
                            "stage": order.stage,
                        }
                    )
        return res
