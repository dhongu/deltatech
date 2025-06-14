# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    account_modifier_id = fields.Many2one("account.modifier", string="Account Modifier")
