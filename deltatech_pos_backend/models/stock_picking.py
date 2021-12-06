# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


from itertools import groupby

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        if self.env.context.get("from_pos_order_confirm", False):
            return
        return super(StockPicking, self)._action_done()

    def _create_move_from_pos_order_lines(self, lines):
        if self.env.context.get("from_pos_order_confirm", False):
            self.ensure_one()
            lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda l: l.product_id.id)
            for _product, lines in lines_by_product:
                order_lines = self.env["pos.order.line"].concat(*lines)
                first_line = order_lines[0]
                current_move = self.env["stock.move"].create(self._prepare_stock_move_vals(first_line, order_lines))
                confirmed_moves = current_move._action_confirm()
                for move in confirmed_moves:
                    move._action_assign()
        else:
            super(StockPicking, self)._create_move_from_pos_order_lines(lines)
