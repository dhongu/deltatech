# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move)
        if "receipt_picking_ids" in self.env.context:
            domain = [
                ("purchase_line_id", "=", self.id),
                ("picking_id", "in", self.env.context["receipt_picking_ids"]),
            ]
            moves = self.env["stock.move"].search(domain)
            if moves:
                # update quantity with move quantity
                # move quantities are in the move unit; the bill line keeps the order line unit
                qty = 0.0
                for move in moves:
                    move_qty = move.product_uom._compute_quantity(
                        move.quantity, self.product_uom_id, rounding_method="HALF-UP"
                    )
                    if move.picking_id.picking_type_code == "incoming":
                        qty += move_qty
                    elif move.picking_id.picking_type_code == "outgoing":
                        qty -= move_qty
                    else:
                        raise UserError(self.env._("You cannot invoice this type of transfer: %s") % move.picking_id)
                res.update({"quantity": qty})
                return res
            else:
                # update quantity with 0 (lines will be deleted ?)
                res.update({"quantity": 0})
                return res
        else:
            return res
