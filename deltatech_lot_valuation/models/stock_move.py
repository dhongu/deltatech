# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    # def _create_out_svl(self, forced_quantity=None):
    #     lots = self.env["stock.production.lot"]
    #     for move in self:
    #         move = move.with_company(move.company_id)
    #         valued_move_lines = move._get_out_move_lines()
    #         for line in valued_move_lines:
    #             lots |= line.lot_id
    #     if lots:
    #         return super(StockMove, self.with_context(lot_ids=lots))._create_out_svl(forced_quantity)
    #     else:
    #         return super(StockMove, self)._create_out_svl(forced_quantity)

    def _action_done(self, cancel_backorder=False):
        lots = self.env["stock.production.lot"]
        move_lines = self.env["stock.move.line"]
        for move in self:
            for line in move.move_line_ids:
                lots |= line.lot_id
                move_lines |= line
        if lots:
            return super(StockMove, self.with_context(lot_ids=lots, move_lines=move_lines))._action_done(
                cancel_backorder
            )
        else:
            return super(StockMove, self)._action_done(cancel_backorder)
