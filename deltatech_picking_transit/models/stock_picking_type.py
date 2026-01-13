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
