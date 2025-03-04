from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    partner_minimal_purchase_value = fields.Float(
        related="partner_id.minimal_purchase_value", string="Partner Minimal Purchase Value"
    )
