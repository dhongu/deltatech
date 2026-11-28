from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    display_stock = fields.Boolean(string="Display Stock in POS", default=True)
    display_price = fields.Boolean(string="Display Price in POS badge", default=True)
    stock_badge_quantity = fields.Selection(
        [("on_hand", "On hand"), ("available", "Available")],
        string="Quantity on the badge",
        default="on_hand",
        required=True,
        help="On hand shows the physical stock. Available subtracts what is already "
        "reserved for orders that have not left the warehouse yet, which is what you "
        "want when the picking is validated by the warehouse rather than at the till.",
    )
