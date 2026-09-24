from odoo import fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(
        selection_add=[("standard_price_with_vat", "Cost with VAT")],
        ondelete={"standard_price_with_vat": "set default"},
    )
