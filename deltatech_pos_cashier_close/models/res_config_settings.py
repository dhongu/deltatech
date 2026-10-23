from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_cashier_can_close = fields.Boolean(related="pos_config_id.cashier_can_close", readonly=False)
