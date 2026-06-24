# ©  2008-2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    active = fields.Boolean(default=True)
