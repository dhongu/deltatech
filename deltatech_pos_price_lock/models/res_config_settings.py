from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_lock_price_for_managers = fields.Boolean(related="pos_config_id.lock_price_for_managers", readonly=False)
