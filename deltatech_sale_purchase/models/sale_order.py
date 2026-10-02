# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details


from odoo import Command, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_cancel(self):
        """Drop the generated purchase lines instead of leaving them behind.

        Only lines of a draft purchase order are touched, a confirmed order is
        left to the buyer. A line that also supplies moves of other sale orders
        (vendor grouping Daily/Weekly/Always) is kept: the cancelled moves are
        detached from it and their quantity is subtracted.
        """
        cancelled_moves = self.order_line.move_ids
        purchase_lines = cancelled_moves.created_purchase_line_ids.filtered(lambda line: line.order_id.state == "draft")
        lines_to_unlink = self.env["purchase.order.line"]
        for line in purchase_lines:
            other_moves = line.move_dest_ids.filtered(lambda m: m.state != "cancel") - cancelled_moves
            if not other_moves:
                lines_to_unlink |= line
                continue
            moves_to_detach = line.move_dest_ids & cancelled_moves
            cancelled_qty = sum(
                move.uom_id._compute_quantity(move.product_uom_qty, line.uom_id) for move in moves_to_detach
            )
            moves_to_detach.write({"created_purchase_line_ids": [Command.unlink(line.id)]})
            line.product_qty = max(line.product_qty - cancelled_qty, 0.0)
        lines_to_unlink.unlink()
        return super()._action_cancel()
