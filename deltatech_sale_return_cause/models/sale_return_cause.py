from odoo import fields, models


class SaleReturnCause(models.Model):
    _name = "sale.return.cause"
    _description = "Sale Return Cause"
    _order = "sequence, id"

    name = fields.Char(string="Cause", required=True, translate=True)
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(default=True)
