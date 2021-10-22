# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        if "picking_ids" in self.env.context:
            pickings = self.env["stock.picking"].browse(self.env.context["picking_ids"])
            for move in res:  # if multiple invoices from multiple SO are created
                sale_orders = self.env["sale.order"]
                for line in move.invoice_line_ids:
                    if line.sale_line_ids:
                        for sale_line in line.sale_line_ids:
                            if sale_line.order_id not in sale_orders:
                                sale_orders |= sale_line.order_id
                    invoice_pickings = pickings.filtered(lambda p: p.sale_id in sale_orders)
                    invoice_pickings.update(
                        {
                            "account_move_id": move.id,
                            "to_invoice": False,
                        }
                    )
        return res

    def update_pickings(self):
        for move in self:
            for account_move_line in move.line_ids.filtered(lambda l: l.exclude_from_invoice_tab is False):
                sale_line_ids = account_move_line.sale_line_ids
                for stock_move in sale_line_ids.move_ids.filtered(lambda m: m.state == "done"):
                    if not stock_move.picking_id.account_move_id or (
                        stock_move.picking_id.account_move_id and stock_move.picking_id.to_invoice
                        # picking seems to be partially invoiced
                    ):
                        # Check if qty in invoice is not all the qty in stock move.
                        # If not all the qty in invoice, to_invoice will be set to True
                        if account_move_line.quantity < stock_move.quantity_done:
                            to_invoice = True
                        else:
                            to_invoice = False
                        stock_move.picking_id.update(
                            {
                                "account_move_id": move.id,
                                "to_invoice": to_invoice,
                            }
                        )

    def unlink(self):
        pickings_to_update = self.env["stock.picking"].search([("account_move_id", "in", self.ids)])
        res = super(AccountMove, self).unlink()
        if res:
            # update linked pickings
            pickings_to_update.update(
                {
                    "to_invoice": True,
                }
            )
        return res

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        # update linked pickings
        pickings_to_update = self.env["stock.picking"].search([("account_move_id", "in", self.ids)])
        pickings_to_update.update(
            {
                "to_invoice": True,
                "account_move_id": False,
            }
        )
        return res

    def button_draft(self):
        self.update_pickings()
        return super(AccountMove, self).button_draft()
