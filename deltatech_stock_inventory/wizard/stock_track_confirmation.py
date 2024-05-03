# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockTrackConfirmation(models.TransientModel):
    _inherit = "stock.track.confirmation"

    inventory_id = fields.Many2one("stock.inventory", "Inventory")
