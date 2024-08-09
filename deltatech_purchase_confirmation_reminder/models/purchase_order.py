from datetime import datetime, timedelta

from odoo import _, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_send_reminder(self):
        draft_orders = self.env["purchase.order"].search([("state", "=", "draft")])
        datetime_field = datetime.now()
        date_now = datetime_field.date()
        for order in draft_orders:
            days_for_delivery = 1
            for line in order.order_line:
                for seller in line.product_id.product_tmpl_id.seller_ids:
                    if seller.name.id == order.partner_id.id:
                        if seller.delay > days_for_delivery:
                            days_for_delivery = seller.delay

            param = self.env["ir.config_parameter"].sudo()
            safety_days = int(param.get_param("deltatech_purchase_confirmation_reminder.safety_days", default=0))
            reminder_date = order.date_planned - timedelta(days=days_for_delivery + safety_days)
            if reminder_date.date() <= date_now:
                settings = self.env["res.config.settings"].get_values()

                # Get the activity type from the settings
                activity_type = settings["purchase_order_reminder_activity_type_id"]
                activity_exists = self.env["mail.activity"].search(
                    [
                        ("res_id", "=", order.id),
                        ("res_model_id", "=", self.env["ir.model"]._get("purchase.order").id),
                        ("summary", "=", _("Purchase Order Reminder")),
                    ],
                    limit=1,
                )
                if order.user_id and activity_type and not activity_exists:
                    # Create the activity
                    self.env["mail.activity"].create(
                        {
                            "activity_type_id": activity_type,
                            "user_id": order.user_id.id,
                            "summary": _("Purchase Order Reminder"),
                            "note": _("This is a reminder to confirm the purchase order."),
                            "date_deadline": date_now,
                            "res_id": order.id,
                            "res_model_id": self.env["ir.model"]._get("purchase.order").id,
                        }
                    )
