# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_view_stock_valuation_layers(self):
        self = self.with_context(active_test=False)
        return super().action_view_stock_valuation_layers()
