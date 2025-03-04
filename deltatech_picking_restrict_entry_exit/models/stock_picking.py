from odoo import _, api, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model_create_multi
    def create(self, vals_list):
        # this should restrict users from creating delivery/receipts manually, they should only be created from sale/purchase orders
        for vals in vals_list:
            # there are users that can create picking without sale/purchase order if they have the group
            if not self.env.user.has_group("deltatech_picking_restrict_entry_exit.group_picking_restrict_entry_exit"):
                picking_type = self.env["stock.picking.type"].browse(vals.get("picking_type_id"))
                # returns and backorders are not restricted because they don't come with sale_id or purchase_id, don't know the back orders is not associated
                if not vals.get("return_id", False) and not vals.get("backorder_id", False):
                    if picking_type.code == "outgoing":
                        if not vals.get("sale_id"):
                            raise UserError(_("You cannot create an outgoing picking without a source sale order."))
                    elif picking_type.code == "incoming":
                        if not vals.get("purchase_id"):
                            raise UserError(_("You cannot create an incoming picking without a source purchase order."))

        return super().create(vals_list)

    # self.env.user.has_group("deltatech_picking_restrict_entry_exit.group_picking_restrict_entry_exit")
    def button_validate(self):
        for picking in self:  # this should restrict validation of delivery/receipts with unaccounted lines or with quantities greater than ordered
            if not self.return_id and not self.backorder_id:  # again returns and backorders are not restricted
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
                                if not move.sale_line_id:
                                    raise UserError(
                                        _(
                                            "You cannot validate the picking because the product %s is not linked to a sale order line."
                                        )
                                        % move.product_id.display_name
                                    )
                            elif picking_type.code == "incoming":
                                if not move.purchase_line_id:
                                    raise UserError(
                                        _(
                                            "You cannot validate the picking because the product %s is not linked to a purchase order line."
                                        )
                                        % move.product_id.display_name
                                    )
                            if move.quantity > move.product_uom_qty:
                                raise UserError(
                                    _(
                                        "You cannot validate the picking because the quantity done is greater than the quantity ordered for the product %s."
                                    )
                                    % move.product_id.display_name
                                )

        return super().button_validate()

    def write(self, vals):
        if "move_ids_without_package" in vals:  # client wanted the same check on validation to be done on saving too
            for move_data in vals["move_ids_without_package"]:  # we check if the lines were touched
                if len(move_data) > 2 and "quantity" in move_data[2]:
                    move_id = move_data[1]
                    if (
                        isinstance(move_id, str) and "virtual" in move_id
                    ):  # if the line contains virtual, it means it's a new line and we check it differently
                        picking_type = self.env["stock.picking.type"].search(
                            [("id", "=", move_data[2]["picking_type_id"])]
                        )
                        if picking_type.code == "internal":
                            location_id = self.env["stock.location"].search([("id", "=", move_data[2]["location_id"])])
                            location_dest_id = self.env["stock.location"].search(
                                [("id", "=", move_data[2]["location_dest_id"])]
                            )
                            warehouse_source = self.env["stock.warehouse"].search(
                                [("view_location_id", "parent_of", location_id.id)]
                            )
                            # apparently a location can have 2 warehouses (configuration for online shop warehouse
                            if warehouse_source:
                                warehouse_source = sorted(
                                    warehouse_source,
                                    key=lambda w: w.view_location_id.parent_path.count("/"),
                                    reverse=True,
                                )
                                warehouse_source = warehouse_source[0]
                            warehouse_destination = self.env["stock.warehouse"].search(
                                [("view_location_id", "parent_of", location_dest_id.id)]
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
                        if picking_type.code in ["incoming", "outgoing"] and not self.env.user.has_group(
                            "deltatech_picking_restrict_entry_exit.group_picking_restrict_entry_exit"
                        ):  # we check if the picking is incoming/outgoing, if yes we restrict creation
                            raise UserError(_("You can't manually add moves to an incoming/outgoing picking"))
                        else:  # if it is not incoming/outgoing, we check if the quantity is greater than the ordered quantity
                            if move_data[2]["quantity"] > move_data[2]["product_uom_qty"]:
                                raise UserError(
                                    _(
                                        "You can't add a line where the quantity done is greater than the quantity needed"
                                    )
                                )
                    else:  # this is for existing lines and we do the same check as in the validation
                        quantity = move_data[2]["quantity"]
                        move = self.env["stock.move"].browse(move_id)
                        picking = move.picking_id
                        if (
                            picking.picking_type_id and picking.picking_type_id.code == "internal"
                        ):  # if the picking is internal and the locations are in the same warehouse we don't need to check the lines
                            warehouse_source = self.env["stock.warehouse"].search(
                                [("view_location_id", "parent_of", picking.location_id.id)]
                            )
                            # apparently a location can have 2 warehouses (configuration for online shop warehouse
                            if warehouse_source:
                                warehouse_source = sorted(
                                    warehouse_source,
                                    key=lambda w: w.view_location_id.parent_path.count("/"),
                                    reverse=True,
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
                        if quantity > move.product_uom_qty:
                            raise UserError(
                                _(
                                    "You cannot save the picking because the quantity done is greater than the quantity ordered for the product %s."
                                )
                                % move.product_id.display_name
                            )
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
