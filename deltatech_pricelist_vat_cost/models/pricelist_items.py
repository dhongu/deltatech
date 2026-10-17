from odoo import api, fields, models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(
        selection_add=[("standard_price_with_vat", "Cost with VAT")],
        ondelete={"standard_price_with_vat": "set default"},
    )

    @api.onchange("compute_price")
    def _onchange_compute_price(self):
        res = super()._onchange_compute_price()
        # A discount offers no base selector (only the pricelist it is taken from),
        # so a "Cost with VAT" base carried over from a surcharge must be reset.
        if self.compute_price == "discount" and self.base == "standard_price_with_vat":
            self.base = "list_price"
        return res

    def _get_price_label_base_str(self):
        if self.base == "standard_price_with_vat":
            return self.env._("product cost with VAT")
        return super()._get_price_label_base_str()
