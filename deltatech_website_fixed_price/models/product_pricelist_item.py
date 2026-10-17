# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _show_discount_on_shop(self):
        """Also strike through the base price for fixed price rules.

        Standard Odoo only does it for discount rules. The base must still be a
        price the customer could have seen (sales price or another pricelist),
        never the cost.

        Only for /shop, /product, and configurators, not on the cart or the checkout.
        """
        res = super()._show_discount_on_shop()
        if not self:
            return False

        self.ensure_one()

        return res or (self.compute_price == "fixed" and self.base in ("list_price", "pricelist"))
