from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_confirm_order_without_record_type = fields.Boolean(
        string="Confirmed without record type",
        implied_group="deltatech_record_type.group_confirm_order_without_record_type",
        default=True,
    )
