# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    inventory_id = fields.Many2one("stock.inventory", "Inventory Document", check_company=True)
    inventory_line_id = fields.Many2one(
        "stock.inventory.line",
        "Inventory Line",
        index="btree_not_null",
        help="Inventory line that generated this move; links the accounting value back to the line.",
    )
