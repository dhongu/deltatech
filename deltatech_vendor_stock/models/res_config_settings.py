# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stock_color_fulfilled = fields.Char(
        string="Color - Fulfilled",
        default="#28a745",
        help="Color when stock will be fulfilled",
        config_parameter="deltatech_vendor_stock.color_fulfilled",
    )

    stock_color_fulfilled_no_free_qty = fields.Char(
        string="Color - Fulfilled (No Free Qty)",
        default="#17a2b8",
        help="Color when fulfilled but no free qty today",
        config_parameter="deltatech_vendor_stock.color_fulfilled_no_free_qty",
    )

    stock_color_not_fulfilled = fields.Char(
        string="Color - Not Fulfilled",
        default="#dc3545",
        help="Color when not fulfilled",
        config_parameter="deltatech_vendor_stock.color_not_fulfilled",
    )

    stock_color_vendor_available = fields.Char(
        string="Color - Vendor Available",
        default="#ffc107",
        help="Color when vendor qty is available",
        config_parameter="deltatech_vendor_stock.color_vendor_available",
    )

    stock_color_default = fields.Char(
        string="Color - Default",
        default="#007bff",
        help="Default color",
        config_parameter="deltatech_vendor_stock.color_default",
    )
