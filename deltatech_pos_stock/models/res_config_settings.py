from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_display_stock = fields.Boolean(related="pos_config_id.display_stock", readonly=False)
    pos_display_price = fields.Boolean(related="pos_config_id.display_price", readonly=False)
