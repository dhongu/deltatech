# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockInventoryAdjustmentName(models.TransientModel):
    _inherit = "stock.inventory.adjustment.name"

    def _default_inventory_adjustment_name(self):
        inventory_name = ""
        if self.env.context.get("default_quant_ids"):
            quant = self.env["stock.quant"].browse(self.env.context["default_quant_ids"][0])
            if quant.inventory_id:
                inventory_name = quant.inventory_id.name
        return inventory_name

    inventory_adjustment_name = fields.Char(default=_default_inventory_adjustment_name)
