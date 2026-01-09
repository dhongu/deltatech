# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _show_discount_on_shop(self):
        """On ecommerce, formula rules are also expected to show discounts.

        Only for /shop, /product, and configurators, not on the cart or the checkout.
        """
        res = super()._show_discount_on_shop()
        if not self:
            return False

        self.ensure_one()

        return res or self.compute_price == "fixed"
