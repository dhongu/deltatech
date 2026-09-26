# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_view_stock_valuation_layers(self):
        self = self.with_context(active_test=False)
        return super().action_view_stock_valuation_layers()

    def _prepare_return_move_default_values(self, move_id):
        # In 20.0 wizard-ul stock.return.picking a fost eliminat: returul se creeaza direct
        # (action_return -> _create_return) cu cantitatile pe 0. Pastram comportamentul din
        # 19.0 (fostul override pe _prepare_stock_return_picking_line_vals_from_move):
        # cantitatea propusa = cantitatea miscarii originale minus ce s-a returnat deja.
        vals = super()._prepare_return_move_default_values(move_id)
        if not self.show_return:
            # schimb (action_exchange): standardul preia deja cantitatea miscarii
            return vals
        quantity = move_id.quantity
        for move in move_id.move_dest_ids:
            if (
                not move.origin_returned_move_id
                or move.origin_returned_move_id != move_id
                or move_id.picking_id.picking_type_code == "incoming"
            ):
                continue
            quantity -= move.quantity
        vals["product_uom_qty"] = (move_id.uom_id or move_id.product_id.uom_id).round(quantity)
        return vals
