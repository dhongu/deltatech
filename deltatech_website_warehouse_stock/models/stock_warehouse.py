# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    website_stock_display = fields.Boolean(string="Display on Website", default=True)
