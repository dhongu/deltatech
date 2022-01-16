# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    def button_open_barcode_interface(self):
        xml_id = "stock_barcode_picking_batch.stock_barcode_batch_picking_action_kanban"

        action = self.env["ir.actions.act_window"]._for_xml_id(xml_id)
        action["domain"] = [("id", "in", self.ids)]
        return action
