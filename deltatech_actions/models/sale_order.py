# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def force_cancel_order_and_moves(self):
        """
        Cancel sale order, attached pickings, stock moves and stock move lines.
        :return:
        """
        stock_move_lines_to_cancel = self.env["stock.move.line"]
        stock_moves_to_cancel = self.env["stock.move"]
        pickings_to_cancel = self.env["stock.picking"]
        account_moves_to_cancel = self.env["account.move"]
        sale_orders_to_cancel = self
        for order in self:
            if order.state == "sale" and order.picking_ids:
                for picking in order.picking_ids:
                    stock_moves_to_cancel |= picking.move_ids
                    account_moves_to_cancel |= picking.move_ids.account_move_ids
                    stock_move_lines_to_cancel |= picking.move_ids.move_line_ids
                    pickings_to_cancel |= picking

        stock_move_lines_to_cancel.write({"state": "cancel"})
        account_moves_to_cancel.write({"state": "cancel"})
        stock_moves_to_cancel.write({"state": "cancel"})
        pickings_to_cancel.write({"state": "cancel"})
        sale_orders_to_cancel.write({"state": "cancel"})
