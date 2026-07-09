# ©  2015-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    restricted_stock = fields.Boolean(
        string="Restricted Stock",
        help="Quantities stored in this location (and its children) are shown as "
        "unavailable in the detailed kanban stock display and are excluded "
        "from the free stock.",
    )
