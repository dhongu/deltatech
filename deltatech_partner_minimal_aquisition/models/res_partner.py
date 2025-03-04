from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    minimal_purchase_value = fields.Float(
        string="Minimal Purchase", default=0.0, help="Minimal value of the purchase order to this partner."
    )
