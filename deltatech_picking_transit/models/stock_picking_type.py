# models/stock_picking_type.py

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    two_step_transfer_use = fields.Selection(
        [("reception", "Reception"), ("delivery", "Delivery")], string="Two Step Transfer Use"
    )
    auto_second_transfer = fields.Boolean(
        string="Auto Second Transfer",
        help="If checked, the system will automatically create a second transfer when the first transfer is validated, the contact on the transfer will determine the warehouse for the second transfer.",
    )
    link_second_transfer = fields.Boolean(
        string="Link Second Transfer to First",
        help="If checked, the moves of the second transfer are chained to the moves of the first one: the second "
        "transfer waits for the first, reserves exactly the quantities and lots that were delivered and cannot be "
        "validated before the first transfer is done or for more than it delivered.",
    )
