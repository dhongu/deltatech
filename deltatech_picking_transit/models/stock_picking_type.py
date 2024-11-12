# models/stock_picking_type.py

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    two_step_transfer_use = fields.Selection(
        [("reception", "Reception"), ("delivery", "Delivery")], string="Two Step Transfer Use"
    )
