# models/stock_picking.py

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_transit_transfer = fields.Boolean(default=False)

    def open_transfer_wizard(self):
        return {
            "name": "Create Transfer",
            "type": "ir.actions.act_window",
            "res_model": "stock.picking.transfer.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_picking_id": self.id},
        }

    def create_second_transfer_wizard(self, final_dest_location_id):
        for picking in self:
            if picking.picking_type_id.code == "internal" and picking.location_dest_id.usage == "transit":
                new_picking_vals = {
                    "picking_type_id": self.env.ref("stock.picking_type_internal").id,
                    "location_id": picking.location_dest_id.id,
                    "location_dest_id": final_dest_location_id.id,
                    "move_ids_without_package": [],
                }
                new_picking = self.env["stock.picking"].create(new_picking_vals)
                self.copy_move_lines(picking, new_picking)
                new_picking.action_confirm()
                new_picking.action_assign()
                return new_picking

    def copy_move_lines(self, source_picking, target_picking):
        for move in source_picking.move_ids_without_package:
            move.copy(
                {
                    "picking_id": target_picking.id,
                    "location_id": source_picking.location_dest_id.id,
                    "location_dest_id": target_picking.location_dest_id.id,
                }
            )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.picking_type_id.code == "internal" and res.location_dest_id.usage == "transit":
            res.is_transit_transfer = True
        return res
