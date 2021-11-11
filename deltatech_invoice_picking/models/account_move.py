# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    from_pickings = fields.Boolean("Created from pickings", default=False)

    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
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
                    invoice_pickings = pickings.filtered(lambda p: p.sale_id in sale_orders)
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
                    invoice_pickings = pickings.filtered(lambda p: p.purchase_id in purchase_orders)
                    invoice_pickings.write(
                        {
                            "account_move_id": move.id,
                            "to_invoice": False,
                        }
                    )
        return res

    def update_pickings(self):
        for move in self:
            for account_move_line in move.line_ids.filtered(lambda l: l.exclude_from_invoice_tab is False):
                if account_move_line.sale_line_ids:
                    sale_line_ids = account_move_line.sale_line_ids
                    for stock_move in sale_line_ids.move_ids.filtered(lambda m: m.state == "done"):
                        if not stock_move.picking_id.account_move_id or (
                            stock_move.picking_id.account_move_id
                            and stock_move.picking_id.to_invoice
                            # picking seems to be partially invoiced
                        ):
                            # Check if qty in invoice is not all the qty in stock move.
                            # If not all the qty in invoice, to_invoice will be set to True
                            if account_move_line.quantity < stock_move.quantity_done:
                                to_invoice = True
                            else:
                                to_invoice = False
                            stock_move.picking_id.write(
                                {
                                    "account_move_id": move.id,
                                    "to_invoice": to_invoice,
                                }
                            )
                if account_move_line.purchase_line_id:
                    purchase_line_ids = account_move_line.purchase_line_id
                    for stock_move in purchase_line_ids.move_ids.filtered(lambda m: m.state == "done"):
                        if not stock_move.picking_id.account_move_id or (
                            stock_move.picking_id.account_move_id
                            and stock_move.picking_id.to_invoice
                            # picking seems to be partially invoiced
                        ):
                            # Check if qty in invoice is not all the qty in stock move.
                            # If not all the qty in invoice, to_invoice will be set to True
                            if account_move_line.quantity < stock_move.quantity_done:
                                to_invoice = True
                            else:
                                to_invoice = False
                            stock_move.picking_id.write(
                                {
                                    "account_move_id": move.id,
                                    "to_invoice": to_invoice,
                                }
                            )

    def unlink(self):
        pickings_to_update = self.env["stock.picking"].search([("account_move_id", "in", self.ids)])
        self = self.with_context(unlink_all=True)
        res = super(AccountMove, self).unlink()
        if res:
            # update linked pickings
            pickings_to_update.write(
                {
                    "to_invoice": True,
                }
            )
        return res

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
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
        self.update_pickings()
        return super(AccountMove, self).button_draft()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange("quantity", "product_id")
    def onchange_qty(self):
        for line in self:
            if (
                line.move_id.from_pickings
                and line.product_id.type == "product"
                and not line.exclude_from_invoice_tab
                and not line.display_type

                and line.move_id.move_type in ["out_invoice", "out_refund", "in_invoice", "in_refund"]
            ):
                raise UserError(_("You cannot change this line, the move was generated from pickings"))


    def unlink(self):
        for line in self:
            if (
                line.move_id.from_pickings
                and line.product_id.type == "product"
                and not line.exclude_from_invoice_tab
                and not line.display_type

                and line.move_id.move_type in ["out_invoice", "out_refund", "in_invoice", "in_refund"]
            ):
                if "unlink_all" not in self.env.context:
                    raise UserError(_("You cannot delete lines, the move was generated from pickings"))

        return super(AccountMoveLine, self).unlink()
