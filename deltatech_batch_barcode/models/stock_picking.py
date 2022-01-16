# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_open_barcode_interface(self):
        action = self.env["ir.actions.act_window"]._for_xml_id("stock_barcode.stock_picking_action_kanban")
        action["domain"] = [("id", "in", self.ids)]
        return action
