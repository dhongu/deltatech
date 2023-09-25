# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, models
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_account_move_line(self, move=False):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        if "receipt_picking_ids" in self.env.context:
            domain = [("purchase_line_id", "=", self.id), ("picking_id", "in", self.env.context["receipt_picking_ids"])]
            moves = self.env["stock.move"].search(domain)
            if moves:
                # update quantity with move quantity
                qty = 0.0
                for move in moves:
                    if move.picking_id.picking_type_code == "incoming":
                        qty += move.quantity_done
                    elif move.picking_id.picking_type_code == "outgoing":
                        qty -= move.quantity_done
                    else:
                        raise UserError(_("You cannot invoice this type of transfer: %s") % move.picking_id)
                res.update({"quantity": qty})
                return res
            else:
                # update quantity with 0 (lines will be deleted ?)
                res.update({"quantity": 0})
                return res
        else:
            return res
