# models/stock_picking_type.py

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    next_operation_id = fields.Many2one("stock.picking.type", string="Next Operation")
