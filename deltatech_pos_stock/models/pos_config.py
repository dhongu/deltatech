from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    display_stock = fields.Boolean(string="Display Stock in POS", default=True)
    display_price = fields.Boolean(string="Display Price in POS badge", default=True)
