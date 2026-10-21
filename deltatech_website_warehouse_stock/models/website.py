# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    warehouse_stock_style = fields.Selection(
        [
            ("badges", "Badges"),
            ("list", "List with icons"),
            ("card", "Card"),
            ("selector", "Warehouse selector"),
        ],
        string="Warehouse Stock Style",
        default="badges",
        required=True,
        help="How the stock per warehouse is shown on the product page.",
    )
    warehouse_stock_zero_message = fields.Selection(
        [("out_of_stock", "Out of stock"), ("on_order", "On order")],
        string="Message at Zero Stock",
        default="out_of_stock",
        required=True,
        help="Text shown for a warehouse without stock. 'On order' tells the customer that the "
        "product can still be ordered.",
    )
    warehouse_stock_zero_note = fields.Char(
        string="Note at Zero Stock",
        translate=True,
        help="Short text shown after 'On order', for example the delivery time.",
    )
    warehouse_stock_qty_display = fields.Selection(
        [("exact", "Exact quantity below the threshold"), ("status_only", "Status only")],
        string="Quantity Display",
        default="exact",
        required=True,
        help="Status only shows 'In stock' instead of the quantity, whatever the stock is.",
    )
    warehouse_stock_theme_colors = fields.Boolean(
        string="Theme Colors for Stock",
        help="Badges tinted on the theme colors, readable on dark themes, instead of the "
        "solid green, grey and red badges.",
    )
