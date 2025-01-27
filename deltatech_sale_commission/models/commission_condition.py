from odoo import fields, models


class SaleCommissionCondition(models.Model):
    _name = "sale.commission.condition"
    _description = "Commission condition"

    sequence = fields.Integer(string="Sequence", default=10)
    percentage = fields.Float(string="Percentage", required=True, default=0.0, digits=(12, 3))
    less_than_days = fields.Integer(string="Less Than Days", required=True, default=0)
    # maximum_days = fields.Integer(string="Maximum Days", required=True, default=0)
