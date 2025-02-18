# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_view_stock_valuation_layers(self):
        res = super().action_view_stock_valuation_layers()
        scraps = self.env["stock.scrap"].search([("picking_id", "=", self.id)])
        domain = [
            (
                "id",
                "in",
                (self.with_context(active_test=False).move_ids + scraps.move_id).stock_valuation_layer_ids.ids,
            )
        ]
        res["domain"] = domain
        return res
