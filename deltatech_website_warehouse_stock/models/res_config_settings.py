# ©  2015-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_warehouse_stock_threshold = fields.Integer(
        string="Website Warehouse Stock Threshold",
        config_parameter="deltatech_website_warehouse_stock.threshold",
        default=10,
    )
    warehouse_stock_position = fields.Selection(related="website_id.warehouse_stock_position", readonly=False)
    warehouse_stock_style = fields.Selection(related="website_id.warehouse_stock_style", readonly=False)
    warehouse_stock_zero_message = fields.Selection(related="website_id.warehouse_stock_zero_message", readonly=False)
    warehouse_stock_zero_note = fields.Char(related="website_id.warehouse_stock_zero_note", readonly=False)
    warehouse_stock_qty_display = fields.Selection(related="website_id.warehouse_stock_qty_display", readonly=False)
    warehouse_stock_theme_colors = fields.Boolean(related="website_id.warehouse_stock_theme_colors", readonly=False)
