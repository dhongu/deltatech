# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.tools import float_compare


class ProductProduct(models.Model):
    _inherit = "product.product"

    # ``_website_show_quick_add`` pe variantă deleagă în 20.0 la
    # ``product.template._website_show_quick_add(product)``: verificarea e acolo.

    def _is_add_to_cart_allowed(self):
        res = super()._is_add_to_cart_allowed()
        if res:
            website = self.env.website
            if website and website._is_cost_price_protection_enabled():
                price = self._get_contextual_price()
                cost_price = self.product_tmpl_id.sudo()._get_cost_price_for_comparison(self, website)
                if float_compare(price, cost_price, precision_rounding=website.currency_id.rounding) < 0:
                    return self.env.user.has_group("base.group_system")
        return res
