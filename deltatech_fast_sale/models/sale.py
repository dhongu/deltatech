# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_open_pickings(self):
        return self.picking_ids.filtered(lambda p: p.state not in ["done", "cancel"])

    def _prepare_pickings(self):
        """Reserve the open transfers and return the ones that can be validated now.

        A move waiting for an upstream move that is not done yet (multi-step routes)
        is accepted: it is reserved after the upstream transfer is validated.
        """
        ready = self.env["stock.picking"]
        pickings = self._get_open_pickings()
        if not pickings:
            return ready
        pickings.action_assign()  # verifica disponibilitate
        for picking in pickings:
            moves = picking.move_ids.filtered(lambda m: m.state not in ["done", "cancel"])
            if all(move.state == "assigned" for move in moves):
                ready |= picking
                continue
            for move in moves:
                if move.state == "assigned":
                    continue
                upstream = move.move_orig_ids.filtered(lambda m: m.state not in ["done", "cancel"])
                if not upstream:
                    raise UserError(self.env._("Not all products are available."))
        return ready

    def action_button_confirm_to_invoice(self):
        if self.state in ["draft", "sent"]:
            self.action_confirm()  # confirma comanda

        # route steps are validated in their dependency order; the next step
        # (e.g. the delivery after the pick) is created/reserved by the previous one
        processed = self.env["stock.picking"]
        pickings = self._prepare_pickings()
        while pickings:
            for picking in pickings:
                for move in picking.move_ids:
                    if move.product_uom_qty > 0 and move.product_qty == 0:
                        move._set_quantity_done(move.product_uom_qty)
                picking.move_ids.picked = True
                picking.with_context(force_period_date=self.date_order)._action_done()
            processed |= pickings
            pickings = self._prepare_pickings() - processed
        if self._get_open_pickings():
            raise UserError(self.env._("Not all products are available."))

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

        # choose the view_mode accordingly
        if len(picking_ids) > 1:
            action["domain"] = [("id", "in", picking_ids.ids)]
        else:
            res = self.env.ref("stock.view_picking_form", False)
            action["views"] = [(res and res.id or False, "form")]
            action["res_id"] = picking_ids.id
        return action
