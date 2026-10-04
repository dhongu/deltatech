from odoo import Command, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # @api.model_create_multi
    # def create(self, vals_list):
    #     # this should restrict users from creating delivery/receipts manually, they should only be created from sale/purchase orders
    #     for vals in vals_list:
    #         # there are users that can create picking without sale/purchase order if they have the group
    #         if not self.env.user.has_group("deltatech_picking_restrict_entry_exit.group_picking_restrict_entry_exit"):
    #             picking_type = self.env["stock.picking.type"].browse(vals.get("picking_type_id"))
    #             # returns and backorders are not restricted because they don't come with sale_id or purchase_id, don't know the back orders is not associated
    #             if not vals.get("return_id", False) and not vals.get("backorder_id", False):
    #                 if picking_type.code == "outgoing":
    #                     if not vals.get("sale_id"):
    #                         raise UserError(_("You cannot create an outgoing picking without a source sale order."))
    #                 elif picking_type.code == "incoming":
    #                     if not vals.get("purchase_id"):
    #                         raise UserError(_("You cannot create an incoming picking without a source purchase order."))
    #
    #     return super().create(vals_list)

    # self.env.user.has_group("deltatech_picking_restrict_entry_exit.group_picking_restrict_entry_exit")
    def button_validate(self):
        # `sale_line_id` / `purchase_line_id` are added on stock.move by `sale_stock` / `purchase_stock`,
        # which are not dependencies of this module. Without them there is no sale/purchase order to link
        # a move to, so the corresponding check simply does not apply.
        move_fields = self.env["stock.move"]._fields
        has_sale_line = "sale_line_id" in move_fields
        has_purchase_line = "purchase_line_id" in move_fields
        for picking in self:  # this should restrict validation of delivery/receipts with unaccounted lines or with quantities greater than ordered
            if not picking.return_id and not picking.backorder_id:  # again returns and backorders are not restricted
                if not self.env.user.has_group(
                    "deltatech_picking_restrict_entry_exit.group_picking_restrict_entry_exit"
                ):
                    picking_type = picking.picking_type_id
                    if (
                        picking_type and picking_type.code == "internal"
                    ):  # if the picking is internal and the locations are in the same warehouse we don't need to check the lines
                        warehouse_source = self.env["stock.warehouse"].search(
                            [("view_location_id", "parent_of", picking.location_id.id)]
                        )
                        # apparently a location can have 2 warehouses (configuration for online shop warehouse
                        if warehouse_source:
                            warehouse_source = sorted(
                                warehouse_source, key=lambda w: w.view_location_id.parent_path.count("/"), reverse=True
                            )

                            warehouse_source = warehouse_source[0]
                        warehouse_destination = self.env["stock.warehouse"].search(
                            [("view_location_id", "parent_of", picking.location_dest_id.id)]
                        )
                        if warehouse_destination:
                            warehouse_destination = sorted(
                                warehouse_destination,
                                key=lambda w: w.view_location_id.parent_path.count("/"),
                                reverse=True,
                            )
                            warehouse_destination = warehouse_destination[0]
                        if warehouse_source and warehouse_destination and warehouse_source == warehouse_destination:
                            continue
                    for move in picking.move_ids:
                        if (
                            move.quantity or move.product_uom_qty
                        ):  # in barcode app if you add and delete a line it will have quantity 0 and product_uom_qty 0 on the picking
                            if picking_type.code == "outgoing":
                                if has_sale_line and not move.sale_line_id:
                                    raise UserError(
                                        self.env._(
                                            "You cannot validate the picking because the product %s is not linked to a sale order line."
                                        )
                                        % move.product_id.display_name
                                    )
                            elif picking_type.code == "incoming":
                                if has_purchase_line and not move.purchase_line_id:
                                    raise UserError(
                                        self.env._(
                                            "You cannot validate the picking because the product %s is not linked to a purchase order line."
                                        )
                                        % move.product_id.display_name
                                    )
                            if move.quantity > move.product_uom_qty:
                                raise UserError(
                                    self.env._(
                                        "You cannot validate the picking because the quantity done is greater than the quantity ordered for the product %s."
                                    )
                                    % move.product_id.display_name
                                )

        return super().button_validate()

    def write(self, vals):
        if "move_ids" in vals:  # client wanted the same check on validation to be done on saving too
            for picking in self:
                picking._check_restrict_move_commands(vals["move_ids"])
        return super().write(vals)
        # for picking in self:# additional check from previous version, not sure if it's needed but shouldn't cause any issues
        #     if not self.return_id and not self.backorder_id:
        #         picking_type = picking.picking_type_id
        #         for move in picking.move_ids:
        #             if picking_type.code == "outgoing":
        #                 if not move.sale_line_id:
        #                     raise UserError(
        #                         _(
        #                             "You cannot save the picking because the product %s is not linked to a sale order line."
        #                         )
        #                         % move.product_id.display_name
        #                     )
        #             elif picking_type.code == "incoming":
        #                 if not move.purchase_line_id:
        #                     raise UserError(
        #                         _(
        #                             "You cannot save the picking because the product %s is not linked to a purchase order line."
        #                         )
        #                         % move.product_id.display_name
        #                     )

    def _check_restrict_move_commands(self, commands):
        # the picking form sends the moves as x2many commands on `move_ids`; only CREATE / UPDATE carry values,
        # and only the lines whose done quantity was touched are checked
        self.ensure_one()
        for command in commands:
            if not isinstance(command, list | tuple) or len(command) < 3 or not isinstance(command[2], dict):
                continue
            values = command[2]
            if "quantity" not in values:
                continue
            if command[0] == Command.CREATE:  # new line, `command[1]` is a virtual id from the web client or 0
                self._check_restrict_new_move(values)
            elif command[0] == Command.UPDATE:  # existing line, we do the same check as in the validation
                self._check_restrict_existing_move(self.env["stock.move"].browse(command[1]), values)

    def _check_restrict_new_move(self, values):
        # the web client sends the picking type and locations of the line; fall back on the picking's
        picking_type = self.env["stock.picking.type"].browse(values.get("picking_type_id")) or self.picking_type_id
        if picking_type.code == "internal":
            location = self.env["stock.location"].browse(values.get("location_id")) or self.location_id
            location_dest = self.env["stock.location"].browse(values.get("location_dest_id")) or self.location_dest_id
            if self._is_same_warehouse(location, location_dest):
                return
        if picking_type.code in ["incoming", "outgoing"] and not self.env.user.has_group(
            "deltatech_picking_restrict_entry_exit.group_picking_restrict_entry_exit"
        ):  # we check if the picking is incoming/outgoing, if yes we restrict creation
            raise UserError(self.env._("You can't manually add moves to an incoming/outgoing picking"))
        # if it is not incoming/outgoing, we check if the quantity is greater than the ordered quantity
        if (values["quantity"] or 0.0) > (values.get("product_uom_qty") or 0.0):
            raise UserError(
                self.env._("You can't add a line where the quantity done is greater than the quantity needed")
            )

    def _check_restrict_existing_move(self, move, values):
        picking = move.picking_id
        if picking.picking_type_id.code == "internal" and self._is_same_warehouse(
            picking.location_id, picking.location_dest_id
        ):  # if the picking is internal and the locations are in the same warehouse we don't need to check the lines
            return
        # the demand may be changed in the same save
        demand = values.get("product_uom_qty", move.product_uom_qty) or 0.0
        if (values["quantity"] or 0.0) > demand:
            raise UserError(
                self.env._(
                    "You cannot save the picking because the quantity done is greater than the quantity ordered for the product %s.",
                    move.product_id.display_name,
                )
            )

    def _is_same_warehouse(self, location, location_dest):
        warehouses = []
        for loc in (location, location_dest):
            if not loc:
                return False
            warehouse = self.env["stock.warehouse"].search([("view_location_id", "parent_of", loc.id)])
            # apparently a location can have 2 warehouses (configuration for online shop warehouse
            if warehouse:
                warehouse = sorted(warehouse, key=lambda w: w.view_location_id.parent_path.count("/"), reverse=True)[0]
            warehouses.append(warehouse)
        return bool(warehouses[0] and warehouses[1] and warehouses[0] == warehouses[1])
