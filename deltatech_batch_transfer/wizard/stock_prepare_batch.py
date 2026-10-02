# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPrepareBatch(models.TransientModel):
    _name = "stock.prepare.batch"
    _description = "Prepare Batch"

    partner_id = fields.Many2one("res.partner")
    mode = fields.Selection([("sale", "Sale"), ("purchase", "Purchase")], default="purchase")
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        help="Person responsible for this batch transfer",
    )
    reference = fields.Char("Reference")
    set_done_qty = fields.Boolean()
    line_ids = fields.One2many("stock.prepare.batch.line", "wizard_id")

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
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
                    raise UserError(self.env._("Please select orders for the same customer."))
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
            domain = [
                ("id", "in", active_ids),
                ("picking_ids.state", "in", ["waiting", "confirmed", "assigned"]),
            ]

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
                "direction": picking_type_code,
                "reference": self.reference,
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
        if self.set_done_qty:
            self.prepare_lines_and_set_quantity(batch_id)
        else:
            self.prepare_lines_and_wo_quantity(batch_id)

    def _allocate_line_quantities(self, batch_id):
        """Distribute the wizard quantities over the batch move lines.

        In Odoo 19 a move line has a single ``quantity`` field (reserved / picked quantity, in the
        move line unit) and no ``product_uom_qty``. The capacity of every move line is its current
        quantity, read before any change, so it is never replaced with the demand of the parent
        move. Wizard quantities are expressed in the product unit and are converted to the unit
        of every move line. Whatever cannot be allocated is stored as ``additional_quantity``.

        :return: dict {stock.move.line: allocated quantity in the move line unit}
        """
        move_lines = batch_id.move_line_ids
        capacity = {move_line: move_line.quantity for move_line in move_lines}
        allocation = dict.fromkeys(move_lines, 0.0)
        for line in self.line_ids:
            product = line.product_id
            product_move_lines = move_lines.filtered(lambda ml, product=product: ml.product_id == product)
            if not product_move_lines:
                raise UserError(
                    self.env._(
                        "The product [%(product_code)s]%(product_name)s was not found for this partner.",
                        product_code=product.default_code,
                        product_name=product.name,
                    )
                )
            quantity = line.quantity
            for move_line in product_move_lines:
                if float_compare(quantity, 0.0, precision_rounding=product.uom_id.rounding) <= 0:
                    break
                free = capacity[move_line] - allocation[move_line]
                free_product_uom = move_line.product_uom_id._compute_quantity(free, product.uom_id)
                if float_compare(free_product_uom, 0.0, precision_rounding=product.uom_id.rounding) <= 0:
                    continue
                if float_compare(quantity, free_product_uom, precision_rounding=product.uom_id.rounding) >= 0:
                    allocation[move_line] += free
                    quantity -= free_product_uom
                else:
                    allocation[move_line] += product.uom_id._compute_quantity(quantity, move_line.product_uom_id)
                    quantity = 0.0
            if float_compare(quantity, 0.0, precision_rounding=product.uom_id.rounding) > 0:
                line.write({"additional_quantity": quantity})
        return allocation

    def prepare_lines_and_set_quantity(self, batch_id):
        if self.line_ids:
            allocation = self._allocate_line_quantities(batch_id)
            for move_line, quantity in allocation.items():
                picked = float_compare(quantity, 0.0, precision_rounding=move_line.product_uom_id.rounding) > 0
                move_line.write({"quantity": quantity, "picked": picked})
        else:
            # the reserved quantity becomes the done quantity
            batch_id.move_line_ids.write({"picked": True})

    def prepare_lines_and_wo_quantity(self, batch_id):
        if self.line_ids:
            # reserve only the requested quantities, nothing is marked as done
            allocation = self._allocate_line_quantities(batch_id)
            for move_line, quantity in allocation.items():
                move_line.write({"quantity": quantity, "picked": False})


class StockPrepareBatchLine(models.TransientModel):
    _name = "stock.prepare.batch.line"
    _description = "Prepare Batch Line"

    wizard_id = fields.Many2one("stock.prepare.batch", ondelete="cascade")
    product_id = fields.Many2one("product.product", required=True)
    quantity = fields.Float(required=True)
    additional_quantity = fields.Float()
