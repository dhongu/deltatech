# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        for picking in self:
            picking_type = picking.picking_type_id
            if picking_type.use_create_lots or picking_type.use_existing_lots:
                if picking_type.code == "incoming":
                    for line in picking.move_line_ids:
                        if line.product_id.tracking == "lot" and not line.lot_name:
                            line.lot_name = self.env["ir.sequence"].next_by_code("stock.lot.serial")

        return super(StockPicking, self).button_validate()
