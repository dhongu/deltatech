# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"
    _order = "date, id"

    date = fields.Datetime(related="stock_move_id.date", store=True, string="Move Date")
