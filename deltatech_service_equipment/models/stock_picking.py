# ©  2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for picking in self:
            if picking.equipment_id:
                svls = picking.move_lines.stock_valuation_layer_ids
                value = 0.0
                for svl in svls:
                    value += svl.value
                cons_value = picking.equipment_id.total_costs + value
                picking.equipment_id.write({"total_costs": cons_value})
        return res
