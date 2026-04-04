# © 2025 Deltatech/Terrabit
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_show_manual_location_fields = fields.Boolean(
        string="Show manual location fields (Rack/Row/Shelf/Case)",
        implied_group="deltatech_stock_inventory.group_show_manual_location_fields",
        help=(
            "Display manual location fields on products and inventory (Rack/Row/Shelf/Case).\n"
            "Recommended when you are NOT using putaway rules."
        ),
    )
