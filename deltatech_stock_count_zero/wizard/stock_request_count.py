# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class StockRequestCount(models.TransientModel):
    _inherit = "stock.request.count"

    def action_request_count(self):
        for count_request in self:
            if count_request.set_count == "empty":
                count_request.quant_ids.write(
                    {
                        "inventory_quantity": 0.0,
                    }
                )
        return super().action_request_count()
