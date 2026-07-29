# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_negative_products(self):
        """Add moves that replenish the negative quants of the destination location.

        The needed quantities are taken from the source location of the transfer.
        """
        self.ensure_one()
        if self.state != "draft":
            return False
        quants = self.env["stock.quant"].search([("location_id", "=", self.location_dest_id.id), ("quantity", "<", 0)])
        moves_vals = []
        for quant in quants:
            # Odoo 19: `stock.move.name` was removed and `_onchange_product_id` no longer
            # exists; the picking description is filled in by the native computed field
            # `description_picking`, so the remaining values are set explicitly here.
            moves_vals.append(
                {
                    "picking_id": self.id,
                    "picking_type_id": self.picking_type_id.id,
                    "company_id": self.company_id.id,
                    "product_id": quant.product_id.id,
                    "product_uom": quant.product_id.uom_id.id,
                    "product_uom_qty": -1 * quant.quantity,
                    "date": self.scheduled_date,
                    "location_id": self.location_id.id,
                    "location_dest_id": self.location_dest_id.id,
                    "state": "draft",
                }
            )
        if moves_vals:
            # Odoo 19: `move_ids_without_package` was removed from `stock.picking`;
            # the moves are linked to the transfer through `move_ids` / `picking_id`.
            self.env["stock.move"].create(moves_vals)
        return True
