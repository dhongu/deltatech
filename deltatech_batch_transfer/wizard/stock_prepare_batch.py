# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPrepareBatch(models.TransientModel):
    _name = "stock.prepare.batch"
    _description = "Prepare Batch"

    partner_id = fields.Many2one("res.partner")
    mode = fields.Selection([("sale", "Sale"), ("purchase", "Purchase")], default="purchase")
    user_id = fields.Many2one("res.users", string="Responsible", help="Person responsible for this batch transfer")

    line_ids = fields.One2many("stock.prepare.batch.line", "wizard_id")

    def default_get(self, fields_list):
        defaults = super(StockPrepareBatch, self).default_get(fields_list)
        model = self.env.context.get("active_model", False)
        active_ids = self.env.context.get("active_ids", [])
        partner = False
        if model == "sale.order":
            defaults["mode"] = "sale"
            orders = self.env[model].browse(active_ids)
            for order in orders:
                if not partner:
                    partner = order.partner_id
                if partner != order.partner_id:
                    raise UserError(_("Please select orders for the same customer."))
            if partner:
                defaults["partner_id"] = partner.id
        return defaults

    def attach_pickings(self):
        pickings = self.env["stock.picking"]
        if self.mode == "sale":
            order_model = "sale.order"
            picking_type_code = "outgoing"
        else:
            order_model = "purchase.order"
            picking_type_code = "incoming"
        active_ids = self.env.context.get("active_ids", [])

        domain = [
            ("partner_id", "=", self.partner_id.id),
            ("picking_ids.state", "in", ["waiting", "confirmed", "assigned"]),
        ]
        if active_ids and self.mode == "sale":
            domain = [("id", "in", active_ids), ("picking_ids.state", "in", ["waiting", "confirmed", "assigned"])]

        orders = self.env[order_model].search(domain)
        for order in orders:
            for order_picking in order.picking_ids:
                if (
                    order_picking.state in ["waiting", "confirmed", "assigned"]
                    and order_picking.picking_type_code == picking_type_code
                ):
                    pickings |= order_picking

        if not pickings:
            action = self.env["ir.actions.actions"]._for_xml_id("deltatech_batch_transfer.action_prepare_batch")
            action["context"] = {}
            action["domain"] = [("id", "=", self.id)]
            return action

        batch = self.env["stock.picking.batch"].create(
            {
                "user_id": self.user_id.id,
                "company_id": pickings[0].company_id.id,
                "picking_type_id": pickings[0].picking_type_id.id,
            }
        )
        pickings.write({"batch_id": batch.id})
        batch.action_confirm()
        if batch.show_check_availability:
            batch.action_assign()

        self.prepare_lines(batch)

        action = self.env["ir.actions.actions"]._for_xml_id("stock_picking_batch.stock_picking_batch_action")
        action["context"] = {}
        action["domain"] = [("id", "=", batch.id)]
        return action

    def prepare_lines(self, batch_id):
        if self.line_ids:
            batch_id.move_line_ids.write({"qty_done": 0})
            # received_move_line_ids = self.env["stock.move.line"]
            for line in self.line_ids:
                qty_error = ""
                quantity = line.quantity
                found = False
                for move_line in batch_id.move_line_ids:
                    if line.product_id == move_line.product_id:
                        found = True
                        if quantity > move_line.product_uom_qty:
                            move_line.qty_done = move_line.product_uom_qty
                            qty_error += _(
                                "Quantity match error for product [%s]%s, quantity ordered: %s, quantity in "
                                "batch: %s."
                            ) % (
                                line.product_id.default_code,
                                line.product_id.name,
                                str(move_line.product_uom_qty),
                                str(quantity),
                            )
                            quantity -= move_line.product_uom_qty
                        else:
                            move_line.qty_done = quantity
                            # received_move_line_ids |= move_line
                            quantity = 0
                if not found:
                    raise UserError(
                        _("The product [%s]%s was not found for this partner.")
                        % (line.product_id.default_code, line.product_id.name)
                    )
                if quantity > 0:
                    line.write({"additional_quantity": quantity})
                if qty_error:
                    raise UserError(qty_error)
                # received_move_line_ids.write({"batch_picking_id": batch_id.id})
        else:
            for move_line in batch_id.move_line_ids:
                move_line.write({"qty_done": move_line.product_uom_qty})


class StockPrepareBatchLine(models.TransientModel):
    _name = "stock.prepare.batch.line"
    _description = "Prepare Batch Line"

    wizard_id = fields.Many2one("stock.prepare.batch", ondelete="cascade")
    product_id = fields.Many2one("product.product", required=True)
    quantity = fields.Float(required=True)
    additional_quantity = fields.Float()
