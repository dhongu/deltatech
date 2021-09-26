# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def invoice_print_delivery(self):

        # result = self.env.ref("stock.action_picking_tree_all")[0]

        # compute the number of delivery orders to display
        pickings = self.env["stock.picking"]
        for invoice in self:
            # pick_ids += [picking.id for picking in invoice.picking_ids]
            for line in invoice.invoice_line_ids:
                for sale_line in line.sale_line_ids:
                    for move in sale_line.move_ids:
                        if move.picking_id.state == "done":
                            pickings |= move.picking_id
                if line.purchase_line_id:
                    for move in line.purchase_line_id.move_ids:
                        if move.picking_id.state == "done":
                            pickings |= move.picking_id

        if not pickings:
            raise UserError(_("This invoice has no deliveries"))

        action = self.env.ref("stock.action_picking_tree_all").read()[0]

        if len(pickings) > 1:
            action["domain"] = [("id", "in", pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref("stock.view_picking_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
            else:
                action["views"] = form_view
            action["res_id"] = pickings.id
        return action
