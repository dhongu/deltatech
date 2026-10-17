# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    from_pickings = fields.Boolean("Created from pickings", default=False, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if "picking_ids" in self.env.context:
            res.write({"from_pickings": True})
            pickings = self.env["stock.picking"].browse(self.env.context["picking_ids"])
            for move in res:  # if multiple invoices from multiple SO are created
                sale_orders = self.env["sale.order"]
                for line in move.invoice_line_ids:
                    if line.sale_line_ids:
                        for sale_line in line.sale_line_ids:
                            if sale_line.order_id not in sale_orders:
                                sale_orders |= sale_line.order_id
                    invoice_pickings = pickings.filtered(lambda p: p.sale_id in sale_orders)  # noqa B023
                    invoice_pickings.write(
                        {
                            "account_move_id": move.id,
                            "to_invoice": False,
                        }
                    )
        if "receipt_picking_ids" in self.env.context:
            res.write({"from_pickings": True})
            pickings = self.env["stock.picking"].browse(self.env.context["receipt_picking_ids"])
            for move in res:  # if multiple invoices from multiple SO are created
                purchase_orders = self.env["purchase.order"]
                for line in move.invoice_line_ids:
                    if line.purchase_line_id:
                        for purchase_line in line.purchase_line_id:
                            if purchase_line.order_id not in purchase_orders:
                                purchase_orders |= purchase_line.order_id
                    invoice_pickings = pickings.filtered(lambda p: p.purchase_id in purchase_orders)  # noqa B023
                    invoice_pickings.write(
                        {
                            "account_move_id": move.id,
                            "to_invoice": False,
                        }
                    )
            for line in res.invoice_line_ids:
                if line.quantity == 0.0:
                    line.with_context(unlink_all=True).unlink()
        return res

    def update_pickings(self):
        """Link the transfers of the invoiced order lines to the invoice and flag the ones still to invoice.

        The flag of a transfer is derived once from all its done moves, using the cumulative invoiced
        quantity of each order line (all its non-cancelled invoices and refunds), not from a single
        invoice line. The quantity not invoiced yet is attributed to the most recent open transfers.
        Transfers already invoiced explicitly (linked and not to invoice) are left unchanged.
        """
        for invoice in self:
            lines = invoice.invoice_line_ids.filtered(lambda ml: ml.display_type == "product")
            if lines.sale_line_ids:
                invoice._update_order_pickings(lines.sale_line_ids, "sale_line_id", "outgoing")
            if lines.purchase_line_id:
                invoice._update_order_pickings(lines.purchase_line_id, "purchase_line_id", "incoming")

    @staticmethod
    def _picking_is_open(picking):
        # not invoiced yet, or only partially invoiced
        return not picking.account_move_id or picking.to_invoice

    @staticmethod
    def _stock_move_qty(stock_move, order_line):
        # move quantities are in the move unit; invoiced quantities are in the order line unit
        return stock_move.product_uom._compute_quantity(stock_move.quantity, order_line.product_uom_id, round=False)

    def _update_order_pickings(self, order_lines, line_field, forward_code):
        self.ensure_one()
        precision = self.env["decimal.precision"].precision_get("Product Unit")
        pickings = order_lines.move_ids.filtered(lambda m: m.state == "done").picking_id.filtered(self._picking_is_open)
        if not pickings:
            return
        stock_moves = pickings.move_ids.filtered(lambda m: m.state == "done" and m[line_field])
        # quantity not invoiced yet, per stock move, in the order line unit
        uncovered = {}
        for order_line in stock_moves[line_field]:
            line_moves = order_line.move_ids.filtered(lambda m: m.state == "done" and m.picking_id)
            forward = line_moves.filtered(lambda m: m.picking_id.picking_type_code == forward_code)
            backward = line_moves - forward
            to_bill = (
                sum(self._stock_move_qty(m, order_line) for m in forward)
                - sum(self._stock_move_qty(m, order_line) for m in backward)
                - order_line.qty_invoiced
            )
            # > 0: deliveries/receipts not invoiced yet; < 0: returns not refunded yet
            candidates = (forward if to_bill > 0 else backward).filtered(lambda m: self._picking_is_open(m.picking_id))
            remaining = abs(to_bill)
            for stock_move in candidates.sorted(lambda m: (m.date, m.id), reverse=True):
                if float_compare(remaining, 0.0, precision_digits=precision) <= 0:
                    break
                part = min(remaining, self._stock_move_qty(stock_move, order_line))
                uncovered[stock_move] = part
                remaining -= part

        refund = self.move_type in ("out_refund", "in_refund")
        for picking in pickings:
            picking_moves = stock_moves.filtered(lambda m, p=picking: m.picking_id == p)
            to_invoice = any(
                float_compare(uncovered.get(m, 0.0), 0.0, precision_digits=precision) > 0 for m in picking_moves
            )
            vals = {"to_invoice": to_invoice}
            # link the transfer to this document when the document covers (part of) it
            same_direction = (picking.picking_type_code == forward_code) != refund
            invoiced_moves = picking_moves.filtered(lambda m: m[line_field] in order_lines)
            if same_direction and any(
                float_compare(
                    self._stock_move_qty(m, m[line_field]) - uncovered.get(m, 0.0), 0.0, precision_digits=precision
                )
                > 0
                for m in invoiced_moves
            ):
                vals["account_move_id"] = self.id
            picking.write(vals)

    def unlink(self):
        pickings_to_update = self.env["stock.picking"].search([("account_move_id", "in", self.ids)])
        self = self.with_context(unlink_all=True)
        res = super().unlink()
        if res:
            # update linked pickings
            pickings_to_update.write(
                {
                    "to_invoice": True,
                }
            )
        return res

    def button_cancel(self):
        res = super().button_cancel()
        # update linked pickings
        pickings_to_update = self.env["stock.picking"].search([("account_move_id", "in", self.ids)])
        pickings_to_update.write(
            {
                "to_invoice": True,
                "account_move_id": False,
            }
        )
        return res

    def button_draft(self):
        res = super().button_draft()
        # after the reset, the invoice counts again in the invoiced quantities of the order lines
        self.update_pickings()
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange("quantity", "product_id")
    def onchange_qty(self):
        for line in self:
            if (
                line.move_id.from_pickings
                and line.product_id.type == "consu"
                and line.product_id.is_storable is True
                and line.display_type == "product"
                and line.move_id.move_type in ["out_invoice", "out_refund", "in_invoice", "in_refund"]
            ):
                raise UserError(self.env._("You cannot change this line, the move was generated from pickings"))

    def unlink(self):
        for line in self:
            if (
                line.move_id.from_pickings
                and line.product_id.type == "consu"
                and line.product_id.is_storable is True
                and line.display_type == "product"
                and line.move_id.move_type in ["out_invoice", "out_refund", "in_invoice", "in_refund"]
                and line.quantity > 0.0
            ):
                if "unlink_all" not in self.env.context:
                    raise UserError(self.env._("You cannot delete lines, the move was generated from pickings"))
        return super().unlink()
