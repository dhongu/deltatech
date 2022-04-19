# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class StockMove(models.Model):
    _inherit = "stock.move"

    inventory_id = fields.Many2one("stock.inventory", "Inventory", check_company=True)
