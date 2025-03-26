# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def receipt_to_stock(self):
        for purchase_order in self:
            for picking in purchase_order.picking_ids:
                if picking.state == "confirmed":
                    picking.action_assign()
                    if picking.state != "assigned":
                        raise UserError(_("The stock transfer cannot be validated!"))
                if picking.state == "assigned":
                    picking.write(
                        {
                            "notice": False,
                            "origin": purchase_order.partner_ref or self.name,
                        }
                    )
                    for move in picking.move_ids:
                        if move.product_uom_qty > 0 and move.product_qty == 0:
                            move._set_quantity_done(move.product_uom_qty)
                    picking.move_ids.picked = True
                    # pentru a se prelua data din comanda de achizitie
                    picking.with_context(force_period_date=purchase_order.date_order)._action_done()

    def action_button_confirm_to_invoice(self):
        if self.state == "draft":
            self.button_confirm()  # confirma comanda

        self.receipt_to_stock()

        action = self.action_create_invoice()

        return action

    def action_button_confirm_notice(self):
        picking_ids = self.env["stock.picking"]
        for picking in self.picking_ids:
            if picking.state == "assigned":
                picking.write({"notice": True})
                picking_ids |= picking

        if not picking_ids:
            return

        result = self.action_view_picking()

        return result
