from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_display_shop_stock = fields.Boolean(related="pos_config_id.display_shop_stock", readonly=False)
    pos_stock_shop_warehouse_ids = fields.Many2many(related="pos_config_id.stock_shop_warehouse_ids", readonly=False)
