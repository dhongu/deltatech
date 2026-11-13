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
    picking_id = fields.Many2one("stock.picking", required=True, index=True, ondelete="cascade")
    state = fields.Selection(
        [("done", "Done"), ("pending", "Needs confirmation")],
        required=True,
        default="done",
        help="Pending: the transfer was created but Odoo asked for a manual step "
        "(for example a backorder), so it must be finished in Inventory.",
    )
    note = fields.Char()

    @api.model
    def pos_create_operation(self, config_id, operation_type, partner_id, lines):
        """Create and validate a standard transfer on behalf of the POS cashier.

        This only drives the standard stock flow: any accounting (receipt or delivery notes,
        valuation entries) comes from the installed localization, not from here.

        :param lines: list of dicts ``{"product_id", "qty", "uom_id"?}``
        :return: dict with ``picking_id``, ``picking_name``, ``state`` and ``message``
        """
        config = self.env["pos.config"].browse(config_id).exists()
        if not config:
            raise UserError(self.env._("The point of sale does not exist."))
        if not self.env.user.has_group("deltatech_pos_stock_ops.group_pos_stock_ops"):
            raise AccessError(self.env._("You are not allowed to do stock operations from the POS."))
        if operation_type not in ("receipt", "delivery"):
            raise UserError(self.env._("Unknown operation type."))
        if not getattr(config, f"stock_ops_{operation_type}"):
            raise UserError(self.env._("This operation is not enabled on this point of sale."))
        if not lines:
            raise UserError(self.env._("Add at least one product."))

        config = config.sudo().with_company(config.company_id)
        picking_type = (
            config.stock_ops_receipt_type_id if operation_type == "receipt" else config.stock_ops_delivery_type_id
        )
        if not picking_type:
            raise UserError(self.env._("Set the operation type for this point of sale first."))
        partner = self.env["res.partner"].sudo().browse(partner_id) if partner_id else self.env["res.partner"]
        source = picking_type.default_location_src_id
        destination = picking_type.default_location_dest_id
        if operation_type == "receipt":
            source = source or partner.property_stock_supplier or self.env.ref("stock.stock_location_suppliers")
        else:
            destination = (
                destination or partner.property_stock_customer or self.env.ref("stock.stock_location_customers")
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
        result = picking.with_context(skip_sms=True).button_validate()
        pending = isinstance(result, dict)
        session = config.current_session_id
        operation = self.sudo().create(
            {
                "config_id": config.id,
                "session_id": session.id,
                "operation_type": operation_type,
                "partner_id": partner.id,
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
