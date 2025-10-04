# ©  2008-2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    alternative_code = fields.Char(string="Alternative Code", related="product_id.alternative_code", store=False)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    alternative_code = fields.Char(string="Alternative Code", related="product_id.alternative_code", store=False)
