from odoo import fields, models


class StockRoute(models.Model):
    _inherit = "stock.route"

    use_this_for_auto_rules = fields.Boolean(
        string="Use This for Auto Rules", help="You should only have one route with this option"
    )
