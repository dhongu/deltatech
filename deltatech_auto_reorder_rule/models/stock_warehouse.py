from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    generate_reorder_rules = fields.Boolean(string="Generate Reorder Rules", default=True)
