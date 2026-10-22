# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    warehouse_stock_position = fields.Selection(
        [("details", "In the product details"), ("after_price", "After the price")],
        string="Warehouse Stock Position",
        default="details",
        required=True,
        help="Where the stock per warehouse is shown on the product page. After the price "
        "needs the price above the Add to Cart button: with the boxed call to action the "
        "block stays in the product details.",
    )
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

    # Fields the website editor may write, from the options of the block
    _WAREHOUSE_STOCK_EDITOR_FIELDS = (
        "warehouse_stock_position",
        "warehouse_stock_style",
        "warehouse_stock_zero_message",
        "warehouse_stock_qty_display",
        "warehouse_stock_theme_colors",
    )

    def _warehouse_stock_editor_write(self, field, value):
        """Write one design option from the website editor, with the value checked
        against the field (selection key or boolean)."""
        self.ensure_one()
        if field not in self._WAREHOUSE_STOCK_EDITOR_FIELDS:
            raise ValueError(self.env._("Unknown warehouse stock option: %s", field))
        definition = self._fields[field]
        if definition.type == "boolean":
            value = value in (True, "1", "true", "True")
        elif value not in dict(definition._description_selection(self.env)):
            raise ValueError(self.env._("Invalid value %(value)s for %(field)s", value=value, field=field))
        self.write({field: value})
