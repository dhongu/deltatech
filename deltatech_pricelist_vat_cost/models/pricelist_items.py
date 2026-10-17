from odoo import fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(
        selection_add=[("standard_price_with_vat", "Cost with VAT")],
        ondelete={"standard_price_with_vat": "set default"},
    )

    def _get_price_label_base_str(self):
        if self.base == "standard_price_with_vat":
            return self.env._("product cost with VAT")
        return super()._get_price_label_base_str()
