# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockRequestCount(models.TransientModel):
    _inherit = "stock.request.count"

    set_count_zero = fields.Boolean(string="Set Count to Zero", default=False)

    def action_request_count(self):
        for count_request in self:
            if count_request.set_count_zero:
                # Set quantity to zero and call the super logic but manually to avoid interference
                quants_to_count = count_request._get_quants_to_count()
                values = count_request._get_values_to_write()
                values["inventory_quantity"] = 0.0
                quants_to_count.with_context(inventory_mode=True).write(values)
                quants_to_count.with_context(inventory_mode=True).action_apply_inventory()
            else:
                super(StockRequestCount, count_request).action_request_count()
        return {}
