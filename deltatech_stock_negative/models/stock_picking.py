# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def set_effective_qty(self):
        for move in self.move_ids_without_package:
            move.update({"quantity_done": move.product_qty})

    def button_validate(self):
        for picking in self:
            if not picking.company_id.no_negative_stock and picking.company_id.force_effective_qty:
                picking.set_effective_qty()

        return super().button_validate()
