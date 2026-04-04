from odoo import fields, models


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    kanban_display_stock = fields.Selection(
        [("all", "All"), ("main", "Main Location")], help="Display stock in kanban view", default="all"
    )
