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

    def _compute_base_price(self, product, quantity, uom, date, currency, **kwargs):
        if self.base != "standard_price_with_vat":
            return super()._compute_base_price(product, quantity, uom, date, currency, **kwargs)
        # like the native cost base: the value is in the cost currency of the current company
        currency.ensure_one()
        src_currency = product.cost_currency_id
        price = product._price_compute("standard_price_with_vat", uom=uom, date=date)[product.id]
        if src_currency != currency:
            price = src_currency._convert(price, currency, self.env.company, date, round=False)
        return price
