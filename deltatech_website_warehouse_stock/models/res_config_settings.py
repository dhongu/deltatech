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
