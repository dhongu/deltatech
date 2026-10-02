# models/stock_picking.py

from collections import defaultdict

from odoo import Command, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_transit_transfer = fields.Boolean(default=False, compute="_compute_is_transit_transfer")
    sub_location_existent = fields.Boolean(default=False, compute="_compute_sub_location_existent")
    second_transfer_created = fields.Boolean(default=False)
    source_transfer_id = fields.Many2one("stock.picking")
    linked_to_source_transfer = fields.Boolean(
        readonly=True,
        help="The moves of this transfer are chained to the moves of the source transfer.",
    )
    create_second_transfer_automatically = fields.Boolean(
        string="Create Second Transfer Automatically",
        related="picking_type_id.auto_second_transfer",
        store=True,
    )

    def open_transfer_wizard(self):
        if self.second_transfer_created:
            raise UserError(self.env._("Second transfer already created."))
        return {
            "name": "Create Transfer",
            "type": "ir.actions.act_window",
            "res_model": "stock.picking.transfer.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_picking_id": self.id},
        }

    def create_second_transfer_wizard(self, final_dest_location_id, picking_type_id):
        # the operator validating the first transfer may not have access rights
        # on the operation type / locations of the receiving warehouse
        picking_type_id = picking_type_id.sudo()
        final_dest_location_id = final_dest_location_id.sudo()
        for picking in self:
            if picking.picking_type_id.code == "internal":
                linked = picking.picking_type_id.link_second_transfer
                if linked and picking.state == "draft":
                    # kits are exploded at confirmation: chain the component moves, not the kit move
                    picking.action_confirm()
                new_picking_vals = {
                    "picking_type_id": picking_type_id.id,
                    "location_id": picking.location_dest_id.id,
                    "location_dest_id": final_dest_location_id.id,
                }
                new_picking = self.env["stock.picking"].sudo().create(new_picking_vals)
                self.copy_move_lines(picking, new_picking)
                new_picking.action_confirm()
                if linked and picking.state == "done":
                    # the first transfer is already done: reserve what it delivered
                    new_picking.action_assign()
                # new_picking.action_assign()
                # new_picking.do_unreserve()
                picking.second_transfer_created = True

                message = self.env._("This transfer was generated from %s.", picking.name)
                new_picking.message_post(body=message)
                new_picking.write({"source_transfer_id": picking.id, "linked_to_source_transfer": linked})
                message = self.env._("Transfer %s was generated.", new_picking.name)

                picking.message_post(body=message)
                picking.write({"partner_id": picking_type_id.warehouse_id.partner_id.id})
                new_picking.write({"partner_id": picking.picking_type_id.warehouse_id.partner_id.id})
                return new_picking

    def copy_move_lines(self, source_picking, target_picking):
        linked = source_picking.picking_type_id.link_second_transfer
        for move in source_picking.move_ids:
            vals = {
                "picking_id": target_picking.id,
                "location_id": source_picking.location_dest_id.id,
                "location_dest_id": target_picking.location_dest_id.id,
                "state": "draft",
            }
            if linked:
                if move.state == "cancel":
                    continue
                # the move waits for its origin and reserves exactly the delivered quantities and lots
                vals.update({"procure_method": "make_to_order", "move_orig_ids": [Command.link(move.id)]})
            move.sudo().copy(vals)

    # @api.model
    # def create(self, vals):
    #     res = super().create(vals)
    #     if res.picking_type_id.code == "internal" and res.picking_type_id.next_operation_id:
    #         res.action_toggle_is_locked()
    #        # res.immediate_transfer = False
    #     return res

    def _compute_sub_location_existent(self):
        sub_location_usage = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(key="deltatech_picking_transit.use_sub_locations", default=False)
        )
        for record in self:
            if sub_location_usage and record.picking_type_id.code == "internal":
                record.sub_location_existent = True
            else:
                record.sub_location_existent = False

    def reassign_location(self):
        for move_line in self.move_line_ids:
            quants = self.env["stock.quant"].search(
                [
                    ("product_id", "=", move_line.product_id.id),
                    ("location_id", "child_of", self.location_id.id),
                    ("quantity", ">", 0.0),
                ]
            )
            if quants:
                move_line.location_id = quants[0].location_id

    @api.onchange("picking_type_id")
    def _compute_is_transit_transfer(self):
        for record in self:
            if record.second_transfer_created:
                record.is_transit_transfer = False
                continue
            if record.picking_type_id.code == "internal" and record.picking_type_id.two_step_transfer_use == "delivery":
                record.is_transit_transfer = True
                record.action_toggle_is_locked()
            # record.immediate_transfer = False
            else:
                record.is_transit_transfer = False

    def button_validate(self):
        for picking in self:
            # to make the module work automatically without the wizard will have some conditions, if the document was an origin it will not create the second transfer automatically because it assumes that the picking comes from a different document so it has the counter part created (eg: replenishment, sale order with replenishment form a different warehouse, etc))
            if (
                picking.create_second_transfer_automatically
                and not picking.second_transfer_created
                and not picking.origin
            ):
                if (
                    not picking.partner_id
                ):  # we use the partner to find the warehouse where the products need to arrive to
                    raise UserError(
                        self.env._(
                            "You must set a partner before validating the picking when you are using 2 step picking with auto create on the second transfer."
                        )
                    )
                warehouse = (
                    self.env["stock.warehouse"].sudo().search([("partner_id", "=", picking.partner_id.id)], limit=1)
                )
                if warehouse:
                    next_operation = (
                        self.env["stock.picking.type"]
                        .sudo()
                        .search(
                            [
                                ("warehouse_id", "=", warehouse.id),
                                ("code", "=", "internal"),
                                ("two_step_transfer_use", "=", "reception"),
                            ],
                            limit=1,
                        )
                    )
                    if next_operation:
                        picking.create_second_transfer_wizard(next_operation.default_location_dest_id, next_operation)
                    else:
                        raise UserError(self.env._("No 2 step reception found for warehouse %s", warehouse.name))
                else:
                    raise UserError(self.env._("No warehouse found for partner %s", picking.partner_id.name))
            if picking.source_transfer_id:
                for move in picking.move_ids:
                    other_moves = picking.source_transfer_id.move_ids.filtered(
                        lambda x: x.product_id == move.product_id
                    )
                    if not other_moves:
                        raise UserError(
                            self.env._(
                                "You cannot validate the picking because the product %s is not from the source picking",
                                move.product_id.display_name,
                            )
                        )
        return super().button_validate()

    def _action_done(self):
        # guards on _action_done, not button_validate, to cover inventory, barcode and RPC validations too
        linked = self.filtered("linked_to_source_transfer")
        linked._check_linked_transfer_order()
        linked._check_linked_transfer_quantity()
        return super()._action_done()

    def _check_linked_transfer_order(self):
        for picking in self:
            source = picking.sudo().source_transfer_id
            if source.state != "done":
                raise UserError(
                    self.env._(
                        "You cannot validate %(picking)s before the source transfer %(source_transfer)s is done.",
                        picking=picking.name,
                        source_transfer=source.name,
                    )
                )

    def _get_transfer_backorders(self):
        """The picking and all its backorders, recursively."""
        family = todo = self
        while todo:
            todo = self.search([("backorder_id", "in", todo.ids)]) - family
            family |= todo
        return family

    @api.model
    def _get_done_quantities(self, move_lines):
        quantities = defaultdict(float)
        for line in move_lines:
            quantities[line.product_id, line.lot_id] += line.quantity_product_uom
        return quantities

    def _check_linked_transfer_quantity(self):
        """The second transfer cannot receive more than the source transfer (and its backorders) delivered,
        per product and lot, taking into account what the second transfer (and its backorders) already received."""
        for picking in self:
            source = picking.sudo().source_transfer_id
            delivered_lines = source._get_transfer_backorders().move_line_ids.filtered(lambda ml: ml.state == "done")
            delivered = self._get_done_quantities(delivered_lines)
            received_pickings = self.sudo().search([("source_transfer_id", "=", source.id), ("state", "=", "done")])
            received = self._get_done_quantities((received_pickings - picking).move_line_ids)
            moves = picking.move_ids.filtered(lambda m: m.state not in ("done", "cancel"))
            moves = moves.filtered("picked") or moves
            to_receive = self._get_done_quantities(moves.move_line_ids)
            problems = []
            for (product, lot), quantity in to_receive.items():
                available = delivered[product, lot] - received[product, lot]
                if product.uom_id.compare(quantity, available) > 0:
                    problems.append(
                        self.env._(
                            "%(product)s: %(quantity)s to receive, %(available)s delivered and not yet received",
                            product=f"{product.display_name} ({lot.name})" if lot else product.display_name,
                            quantity=f"{quantity:g} {product.uom_id.name}",
                            available=f"{max(available, 0.0):g}",
                        )
                    )
            if problems:
                raise UserError(
                    self.env._(
                        "You cannot receive in %(picking)s more than the source transfer %(source_transfer)s "
                        "and its backorders delivered:\n%(rows)s",
                        picking=picking.name,
                        source_transfer=source.name,
                        rows="\n".join(problems),
                    )
                )
