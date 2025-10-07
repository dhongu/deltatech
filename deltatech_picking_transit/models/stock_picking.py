# models/stock_picking.py

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_transit_transfer = fields.Boolean(default=False, compute="_compute_is_transit_transfer")
    sub_location_existent = fields.Boolean(default=False, compute="_compute_sub_location_existent")
    second_transfer_created = fields.Boolean(default=False)
    source_transfer_id = fields.Many2one("stock.picking")
    destionation_transfer_id = fields.Many2one("stock.picking")
    create_second_transfer_automatically = fields.Boolean(
        string="Create Second Transfer Automatically",
        related="picking_type_id.auto_second_transfer",
        store=True,
    )

    def open_transfer_wizard(self):
        if self.second_transfer_created:
            raise UserError(_("Second transfer already created."))
        return {
            "name": "Create Transfer",
            "type": "ir.actions.act_window",
            "res_model": "stock.picking.transfer.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_picking_id": self.id},
        }

    def create_second_transfer_wizard(self, final_dest_location_id, picking_type_id):
        for picking in self:
            new_picking_vals = {
                "picking_type_id": picking_type_id.id,
                "location_id": picking.location_dest_id.id,
                "location_dest_id": final_dest_location_id.id,
                "move_ids_without_package": [],
            }
            new_picking = self.env["stock.picking"].create(new_picking_vals)
            self.copy_move_lines(picking, new_picking)
            new_picking.action_confirm()
            # new_picking.action_assign()
            # new_picking.do_unreserve()
            self.second_transfer_created = True

            message = _("This transfer was generated from %s.") % picking.name
            new_picking.message_post(body=message)
            new_picking.source_transfer_id = picking.id
            picking.destionation_transfer_id = new_picking.id
            message = _("Transfer %s was generated.") % new_picking.name

            picking.message_post(body=message)
            picking.write({"partner_id": picking_type_id.warehouse_id.partner_id.id})
            new_picking.write({"partner_id": picking.picking_type_id.warehouse_id.partner_id.id})

    def copy_move_lines(self, source_picking, target_picking):
        for move in source_picking.move_ids_without_package:
            move.copy(
                {
                    "picking_id": target_picking.id,
                    "location_id": source_picking.location_dest_id.id,
                    "location_dest_id": target_picking.location_dest_id.id,
                    "state": "draft",
                }
            )

    # @api.model
    # def create(self, vals):
    #     res = super().create(vals)
    #     if res.picking_type_id.code == "internal" and res.picking_type_id.next_operation_id:
    #         res.action_toggle_is_locked()
    #        # res.immediate_transfer = False
    #     return res

    def _compute_sub_location_existent(self):
        for record in self:
            sub_location_usage = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param(key="deltatech_picking_transit.use_sub_locations", default=False)
            )
            if sub_location_usage and self.picking_type_id.code == "internal":
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
            if self.second_transfer_created:
                record.is_transit_transfer = False
                return
            if record.picking_type_id.two_step_transfer_use == "delivery":
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
                        _(
                            "You must set a partner before validating the picking when you are using 2 step picking with auto create on the second transfer."
                        )
                    )
                warehouse = self.env["stock.warehouse"].search([("partner_id", "=", picking.partner_id.id)], limit=1)
                if warehouse:
                    next_operation = self.env["stock.picking.type"].search(
                        [
                            ("warehouse_id", "=", warehouse.id),
                            ("code", "=", "internal"),
                            ("two_step_transfer_use", "=", "reception"),
                        ],
                        limit=1,
                    )
                    if next_operation:
                        picking.create_second_transfer_wizard(next_operation.default_location_dest_id, next_operation)
                    else:
                        raise UserError(_("No 2 step reception found for warehouse %s") % warehouse.name)
                else:
                    raise UserError(_("No warehouse found for partner %s") % picking.partner_id.name)
            if picking.source_transfer_id:
                for move in picking.move_ids_without_package:
                    other_moves = picking.source_transfer_id.move_ids_without_package.filtered(
                        lambda x: x.product_id == move.product_id
                    )
                    if not other_moves:
                        possible_picking = self.env["stock.picking"]
                        picking_now = picking.source_transfer_id
                        while picking_now.backorder_ids:
                            picking_now = picking_now.backorder_ids[0]
                            possible_picking |= picking_now
                        if possible_picking:
                            for backorder in possible_picking:
                                other_moves = backorder.move_ids_without_package.filtered(
                                    lambda x: x.product_id == move.product_id
                                )
                                if other_moves:
                                    break
                    if not other_moves:
                        raise UserError(
                            _("You cannot validate the picking because the product %s is not from the source picking")
                            % move.product_id.display_name
                        )
        return super().button_validate()
