# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.tools import float_compare


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _website_show_quick_add(self):
        res = super()._website_show_quick_add()
        if res:
            website = self.env["website"].get_current_website()
            if website.prevent_zero_price_sale:
                price = self._get_contextual_price()
                cost_price = self.product_tmpl_id.sudo()._get_cost_price_for_comparison(self, website)
                if float_compare(price, cost_price, precision_rounding=website.currency_id.rounding) < 0:
                    return False
        return res

    def _is_add_to_cart_allowed(self):
        res = super()._is_add_to_cart_allowed()
        if res:
            website = self.env["website"].get_current_website()
            if website.prevent_zero_price_sale:
                price = self._get_contextual_price()
                cost_price = self.product_tmpl_id.sudo()._get_cost_price_for_comparison(self, website)
                if float_compare(price, cost_price, precision_rounding=website.currency_id.rounding) < 0:
                    return self.env.user.has_group("base.group_system")
        return res
