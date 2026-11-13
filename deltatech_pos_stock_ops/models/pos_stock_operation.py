from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class PosStockOperation(models.Model):
    _name = "pos.stock.operation"
    _description = "POS Stock Operation"
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(related="picking_id.name", store=True)
    config_id = fields.Many2one("pos.config", required=True, index=True, ondelete="cascade")
    session_id = fields.Many2one("pos.session", index=True, ondelete="set null")
    company_id = fields.Many2one("res.company", related="config_id.company_id", store=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, required=True)
    operation_type = fields.Selection([("receipt", "Receipt"), ("delivery", "Delivery")], required=True, index=True)
    partner_id = fields.Many2one("res.partner", check_company=True)
    purchase_id = fields.Many2one("purchase.order", string="Purchase Order", check_company=True)
    picking_id = fields.Many2one("stock.picking", required=True, index=True, ondelete="cascade")
    state = fields.Selection(
        [("done", "Done"), ("pending", "Needs confirmation")],
        required=True,
        default="done",
        help="Pending: the transfer was created but Odoo asked for a manual step "
        "(for example a backorder), so it must be finished in Inventory.",
    )
    note = fields.Char()

    # ------------------------------------------------------------------
    # Checks shared by every entry point
    # ------------------------------------------------------------------
    @api.model
    def _pos_get_config(self, config_id, operation_type):
        config = self.env["pos.config"].browse(config_id).exists()
        if not config:
            raise UserError(self.env._("The point of sale does not exist."))
        if not self.env.user.has_group("deltatech_pos_stock_ops.group_pos_stock_ops"):
            raise AccessError(self.env._("You are not allowed to do stock operations from the POS."))
        if operation_type not in ("receipt", "delivery"):
            raise UserError(self.env._("Unknown operation type."))
        # Rights of the current user on the register, before anything runs with sudo().
        config.check_access("read")
        if config.company_id not in self.env.companies:
            raise AccessError(self.env._("You are not allowed to do stock operations from the POS."))
        if not getattr(config, f"stock_ops_{operation_type}"):
            raise UserError(self.env._("This operation is not enabled on this point of sale."))
        return config.sudo().with_company(config.company_id)

    @api.model
    def _pos_finish_picking(self, config, operation_type, picking, partner, purchase=None, allow_backorder=False):
        """Validate ``picking`` and log the operation; a wizard from Odoo leaves it pending."""
        picking = picking.with_context(skip_sms=True)
        if allow_backorder:
            picking = picking.with_context(skip_backorder=True)
        result = picking.button_validate()
        pending = isinstance(result, dict)
        operation = self.sudo().create(
            {
                "config_id": config.id,
                "session_id": config.current_session_id.id,
                "operation_type": operation_type,
                "partner_id": partner.id,
                "purchase_id": purchase.id if purchase else False,
                "picking_id": picking.id,
                "state": "pending" if pending else "done",
            }
        )
        message = (
            self.env._("Transfer %s created, but it needs a manual step in Inventory.", picking.name)
            if pending
            else self.env._("Transfer %s validated.", picking.name)
        )
        return {
            "operation_id": operation.id,
            "picking_id": picking.id,
            "picking_name": picking.name,
            "state": operation.state,
            "message": message,
        }

    # ------------------------------------------------------------------
    # Receipts: only against a purchase order
    # ------------------------------------------------------------------
    @api.model
    def pos_search_receipts(self, config_id, term=""):
        """Transfers still to receive for a confirmed purchase order, in this register's receipt type."""
        config = self._pos_get_config(config_id, "receipt")
        domain = [
            ("picking_type_id", "=", config.stock_ops_receipt_type_id.id),
            ("purchase_id.state", "=", "purchase"),
            ("state", "in", ("confirmed", "waiting", "assigned")),
        ]
        term = (term or "").strip()
        if term:
            domain += [
                "|",
                "|",
                ("purchase_id.name", "ilike", term),
                ("partner_id.name", "ilike", term),
                ("name", "ilike", term),
            ]
        pickings = self.env["stock.picking"].sudo().search(domain, limit=10, order="scheduled_date, id")
        return [
            {
                "id": picking.id,
                "name": picking.name,
                "purchase_id": picking.purchase_id.id,
                "purchase_name": picking.purchase_id.name,
                "partner_name": picking.partner_id.name or "",
                "moves": [
                    {
                        "id": move.id,
                        "product_id": move.product_id.id,
                        "name": move.product_id.display_name,
                        "qty": move.product_uom_qty,
                        "uom_name": move.product_uom.name,
                    }
                    for move in picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))
                ],
            }
            for picking in pickings
        ]

    @api.model
    def pos_receive_picking(self, config_id, picking_id, lines):
        """Receive what arrived against a purchase order's transfer; the rest becomes a backorder.

        :param lines: list of dicts ``{"move_id", "qty"}`` — the quantity actually received
        """
        config = self._pos_get_config(config_id, "receipt")
        picking = self.env["stock.picking"].sudo().browse(picking_id).exists()
        if (
            not picking
            or not picking.purchase_id
            or picking.picking_type_id != config.stock_ops_receipt_type_id
            or picking.state not in ("confirmed", "waiting", "assigned")
        ):
            raise UserError(self.env._("Receipts can only be made against a confirmed purchase order."))
        received = {int(line["move_id"]): float(line.get("qty") or 0) for line in lines or []}
        open_moves = picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))
        if set(received) - set(open_moves.ids):
            raise UserError(self.env._("A line does not belong to this transfer."))
        if not any(qty > 0 for qty in received.values()):
            raise UserError(self.env._("Enter the received quantity for at least one product."))
        for move in open_moves:
            qty = received.get(move.id, 0.0)
            if qty < 0:
                raise UserError(self.env._("Each line needs a product and a positive quantity."))
            if qty > move.product_uom_qty:
                raise UserError(
                    self.env._(
                        "You cannot receive more than ordered: %(product)s, ordered %(ordered)s.",
                        product=move.product_id.display_name,
                        ordered=move.product_uom_qty,
                    )
                )
            move.quantity = qty
        return self._pos_finish_picking(
            config, "receipt", picking, picking.partner_id, purchase=picking.purchase_id, allow_backorder=True
        )

    # ------------------------------------------------------------------
    # Deliveries
    # ------------------------------------------------------------------
    @api.model
    def pos_create_operation(self, config_id, operation_type, partner_id, lines):
        """Create and validate a standard transfer on behalf of the POS cashier.

        This only drives the standard stock flow: any accounting (delivery notes, valuation
        entries) comes from the installed localization, not from here. Receipts are not made
        here: they go through ``pos_receive_picking``, against a purchase order.

        :param lines: list of dicts ``{"product_id", "qty", "uom_id"?}``
        """
        if operation_type == "receipt":
            raise UserError(self.env._("Receipts can only be made against a confirmed purchase order."))
        config = self._pos_get_config(config_id, operation_type)
        if not lines:
            raise UserError(self.env._("Add at least one product."))
        picking_type = config.stock_ops_delivery_type_id
        if not picking_type:
            raise UserError(self.env._("Set the operation type for this point of sale first."))
        partner = self.env["res.partner"]
        if partner_id:
            # Under the cashier's own rights (no sudo): a partner of another company is refused.
            partner = self.env["res.partner"].browse(partner_id).exists()
            if not partner:
                raise UserError(self.env._("The partner does not exist."))
            partner.check_access("read")
        source = picking_type.default_location_src_id
        destination = (
            picking_type.default_location_dest_id
            or partner.sudo().property_stock_customer
            or self.env.ref("stock.stock_location_customers")
        )
        if not source or not destination:
            raise UserError(self.env._("The operation type has no locations set."))

        picking = (
            self.env["stock.picking"]
            .sudo()
            .with_company(config.company_id)
            .create(
                {
                    "picking_type_id": picking_type.id,
                    "partner_id": partner.id,
                    "location_id": source.id,
                    "location_dest_id": destination.id,
                    "origin": config.name,
                    "move_ids": [(0, 0, self._prepare_move_vals(line, source, destination)) for line in lines],
                }
            )
        )
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        return self._pos_finish_picking(config, operation_type, picking, partner)

    @api.model
    def _prepare_move_vals(self, line, source, destination):
        product = self.env["product.product"].sudo().browse(line.get("product_id")).exists()
        qty = float(line.get("qty") or 0)
        if not product or qty <= 0:
            raise UserError(self.env._("Each line needs a product and a positive quantity."))
        vals = {
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "location_id": source.id,
            "location_dest_id": destination.id,
        }
        uom_id = line.get("uom_id")
        if uom_id and uom_id != product.uom_id.id:
            # A pack is a unit of measure linked to the product (`product.uom`, with its own barcode).
            pack = (
                self.env["product.uom"]
                .sudo()
                .search([("product_id", "=", product.id), ("uom_id", "=", uom_id)], limit=1)
            )
            if not pack:
                raise UserError(self.env._("The unit does not belong to %s.", product.display_name))
            vals["product_uom"] = pack.uom_id.id
        vals["product_uom_qty"] = qty
        return vals
