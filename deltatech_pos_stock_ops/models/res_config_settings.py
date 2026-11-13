from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_stock_ops_receipt = fields.Boolean(related="pos_config_id.stock_ops_receipt", readonly=False)
    pos_stock_ops_delivery = fields.Boolean(related="pos_config_id.stock_ops_delivery", readonly=False)
    pos_stock_ops_receipt_type_id = fields.Many2one(related="pos_config_id.stock_ops_receipt_type_id", readonly=False)
    pos_stock_ops_delivery_type_id = fields.Many2one(related="pos_config_id.stock_ops_delivery_type_id", readonly=False)
