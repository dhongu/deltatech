from odoo import models
from odoo.tools.float_utils import float_round


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        super()._prepare_stock_return_picking_line_vals_from_move(stock_move)
        quantity = stock_move.quantity
        for move in stock_move.move_dest_ids:
            if (
                not move.origin_returned_move_id
                or move.origin_returned_move_id != stock_move
                or stock_move.picking_id.picking_type_code == "incoming"
            ):
                continue
            quantity -= move.quantity
        quantity = float_round(quantity, precision_rounding=stock_move.product_id.uom_id.rounding)
        return {
            "product_id": stock_move.product_id.id,
            "quantity": quantity,
            "move_id": stock_move.id,
            "uom_id": stock_move.product_id.uom_id.id,
        }
