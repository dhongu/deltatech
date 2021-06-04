# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_negative_products(self):
        if self.state == "draft":
            # self.immediate_transfer = False
            self.update({"immediate_transfer": False})
            quants = self.env["stock.quant"].search(
                [("location_id", "=", self.location_dest_id.id), ("quantity", "<", 0)]
            )
            for quant in quants:
                vals = {
                    "product_id": quant.product_id.id,
                    "product_uom": quant.product_id.uom_id.id,
                    "product_uom_qty": -1 * quant.quantity,
                    "date": self.scheduled_date,
                    "location_id": self.location_id.id,
                    "location_dest_id": self.location_dest_id.id,
                    "state": "draft",
                }
                move = self.move_ids_without_package.new(vals)
                move.onchange_product_id()
                self.move_ids_without_package |= move
            return True
