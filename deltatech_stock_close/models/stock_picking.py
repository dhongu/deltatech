# ©  2015-2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_view_stock_valuation_layers(self):
        return super(StockPicking, self.with_context(active_test=False)).action_view_stock_valuation_layers()
