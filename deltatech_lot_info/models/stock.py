# ©  2008-2021 Deltatech
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # TODO:
    # def button_validate(self):
    #     res = super(StockPicking, self).button_validate()
    #     for picking in self:
    #         for move_line in picking.move_line_ids_without_package:
    #             if move_line.lot_id:
    #                 values = {}
    #                 # update lot info for delivery
    #                 if move_line.location_dest_id.usage == "customer" and move_line.location_id.usage in ["internal", "supplier"]:
    #                     if move_line.picking_id.partner_id:
    #                         values["customer_id"] = move_line.picking_id.partner_id.id
    #                     values["output_date"] = move_line.picking_id.date_done
    #                     if move_line.move_id.sale_line_id:
    #                         # values["output_price"]
    #                         pass
