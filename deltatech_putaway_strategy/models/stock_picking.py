from odoo import fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    avoid_putaway_rules = fields.Boolean(string="Avoid Putaway Rules")
    avoid_root_location_on_reservation = fields.Boolean(
        string="Avoid Root Location on Reservation",
        help="When enabled, reservation/allocation should never take stock from the warehouse root "
        "(lot_stock) location for this operation type. Stock not yet put away on a shelf is therefore "
        "not allocated automatically to deliveries.",
        default=False,
    )
