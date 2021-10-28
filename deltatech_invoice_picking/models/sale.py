# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        invoice_line = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if "picking_ids" in self.env.context:
            # search moves from current pickings and current sale order line
            domain = [("sale_line_id", "=", self.id), ("picking_id", "in", self.env.context["picking_ids"])]
            moves = self.env["stock.move"].search(domain)
            if moves:
                # update quantity with move quantity
                qty = 0.0
                for move in moves:
                    if move.picking_id.picking_type_code == "outgoing":
                        qty += move.quantity_done
                    elif move.picking_id.picking_type_code == "incoming":
                        qty -= move.quantity_done
                    else:
                        raise UserError(_("You cannot invoice this type of transfer: %s") % move.picking_id)
                invoice_line.update({"quantity": qty})
                return invoice_line
            else:
                # update quantity with 0 (lines will be deleted)
                invoice_line.update({"quantity": 0})
                return invoice_line
        else:
            return invoice_line


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super(SaleOrder, self)._create_invoices(grouped, final, date)
        # delete qty=0 lines
        if "picking_ids" in self.env.context:
            for line in moves.line_ids.filtered(lambda l: l.exclude_from_invoice_tab is False):
                if line.quantity == 0.0:
                    line.with_context(check_move_validity=False).unlink()
        else:
            moves.update_pickings()
        return moves
