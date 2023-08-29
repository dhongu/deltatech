# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"
    _order = "date, id"

    date = fields.Datetime(compute="_compute_date", string="Move/Valuation Date", store=True)

    def _compute_date(self):
        for valuation in self:
            if valuation.stock_move_id:
                valuation.date = valuation.stock_move_id.date
            else:
                valuation.date = valuation.create_date
