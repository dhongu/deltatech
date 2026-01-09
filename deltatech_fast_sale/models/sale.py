# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_pickings(self):
        for picking in self.picking_ids:
            if picking.state not in ["done", "cancel"]:
                picking.action_assign()  # verifica disponibilitate
                if not all(move.state == "assigned" for move in picking.move_ids):
                    raise UserError(self.env._("Not all products are available."))

    def action_button_confirm_to_invoice(self):
        if self.state in ["draft", "sent"]:
            self.action_confirm()  # confirma comanda

        self._prepare_pickings()
        for picking in self.picking_ids:
            if picking.state not in ["done", "cancel"]:
                for move in picking.move_ids:
                    if move.product_uom_qty > 0 and move.product_qty == 0:
                        move._set_quantity_done(move.product_uom_qty)
                picking.move_ids.picked = True
                picking.with_context(force_period_date=self.date_order)._action_done()

        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_view_sale_advance_payment_inv")
        action["context"] = {"force_period_date": self.date_order}
        return action

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        # invoice_vals["invoice_date"] = self.date_order.date()
        invoice_vals["invoice_date"] = fields.Date.today()
        return invoice_vals

    def action_button_confirm_notice(self):
        self._prepare_pickings()

        picking_ids = self.env["stock.picking"]
        for picking in self.picking_ids:
            if picking.state == "assigned":
                picking.write({"notice": True})
                picking_ids |= picking

        if not picking_ids:
            return

        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")

        action["context"] = {}

        pick_ids = picking_ids.ids
        # choose the view_mode accordingly
        if len(pick_ids) > 1:
            action["domain"] = f"[('id','in',{pick_ids.ids})]"
        elif len(pick_ids) == 1:
            res = self.env.ref("stock.view_picking_form", False)
            action["views"] = [(res and res.id or False, "form")]
            action["res_id"] = picking_ids.id
        return action
