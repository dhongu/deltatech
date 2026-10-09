from datetime import datetime

from odoo import api, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if (
                record.res_model == "sale.order"
                and record.res_id
                and not self.env.context.get("mail_activity_automation")
            ):
                if self.env.user.has_group("base.group_user") and self.env.user.login != "__system__":
                    sale_order = self.env["sale.order"].browse(record.res_id)
                    today = datetime.now().date()
                    # Jurnalul e scris de sistem: utilizatorii de vânzări îl pot
                    # doar citi (ACTIVITY-002), deci căutarea și scrierea merg pe sudo.
                    Record = self.env["sale.order.activity.record"].sudo()
                    existing_record = Record.search(
                        [
                            ("sale_order_id", "=", sale_order.id),
                            ("change_date", "=", today),
                            ("user_id", "=", self.env.user.id),
                        ],
                        limit=1,
                    )

                    if not existing_record:
                        vals = {
                            "sale_order_id": sale_order.id,
                            "change_date": today,
                            "user_id": self.env.user.id,
                            "state": sale_order.state,
                        }
                        # `stage` vine din deltatech_website_sale_status, care nu e
                        # dependență: îl preluăm doar dacă modulul e instalat.
                        if "stage" in sale_order._fields:
                            vals["stage"] = sale_order.stage
                        Record.create(vals)
                    else:
                        existing_record.write({"state": sale_order.state})
        return records
