from odoo import fields, models


class StockPutawayRule(models.Model):
    _inherit = "stock.putaway.rule"

    product_id = fields.Many2one(index=True)
    sequence = fields.Integer(index=True)
