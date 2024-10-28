# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, fields, models


class StockRequestCount(models.TransientModel):
    _inherit = "stock.request.count"

    def _default_inventory_name(self):
        inventory_name = _("Inventory Adjustment") + " - " + fields.Date.to_string(fields.Date.today())
        sequence = self.env.ref("deltatech_stock_inventory.sequence_inventory_doc")
        if sequence:
            inventory_name = sequence.next_by_id()
        return inventory_name

    inventory_name = fields.Char(default=_default_inventory_name)

    def action_request_count(self):
        res = super().action_request_count()
        for count_request in self.with_context(inventory_name=self.inventory_name):
            inventory = count_request.quant_ids.create_inventory_lines()
            inventory.write(
                {
                    "name": self.inventory_name,
                    "date": self.inventory_date,
                    "state": "confirm",
                }
            )
        return res
