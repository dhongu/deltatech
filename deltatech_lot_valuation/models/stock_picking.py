# ©  2008-2021 Deltatech
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        # update lot info for reception
        for picking in self:
            for move_line in picking.move_line_ids_without_package:
                if move_line.lot_id:
                    values = {}
                    if move_line.location_id.usage == "supplier" and move_line.location_dest_id.usage in ["internal"]:
                        values["inventory_value"] = move_line.move_id.price_unit * move_line.qty_done
                        values["input_price"] = move_line.move_id.price_unit
                        values["unit_price"] = move_line.move_id.price_unit
                        values["input_date"] = move_line.picking_id.scheduled_date
                        if move_line.product_id.tracking == "serial":
                            values["location_id"] = move_line.location_dest_id.id
                        move_line.lot_id.write(values)
        return res
