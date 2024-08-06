from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    purchase_order_reminder_activity_type_id = fields.Many2one(
        "mail.activity.type",
        string="Purchase Order Reminder Activity Type",
        config_parameter="deltatech_purchase_confirmation_reminder.purchase_order_reminder_activity_type_id",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        ICPSudo = self.env["ir.config_parameter"].sudo()
        activity_type_id = ICPSudo.get_param(
            "deltatech_purchase_confirmation_reminder.purchase_order_reminder_activity_type_id", default=False
        )
        if activity_type_id:
            res.update(purchase_order_reminder_activity_type_id=int(activity_type_id))
        return res
