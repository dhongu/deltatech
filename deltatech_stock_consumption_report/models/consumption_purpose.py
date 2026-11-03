from odoo import fields, models


class StockConsumptionPurpose(models.Model):
    _name = "stock.consumption.purpose"
    _description = "Consumption purpose"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
