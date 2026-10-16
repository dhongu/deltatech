from odoo import models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _show_discount(self):
        if not self:
            return False
        self.ensure_one()
        if self.pricelist_id.discount_policy == "without_discount":
            return self._is_discount_feature_enabled()
        return super()._show_discount()

    def _compute_price_before_discount(self, *args, **kwargs):
        if not self:
            return 0.0
        self.ensure_one()
        if self.pricelist_id.discount_policy == "without_discount":
            pricelist_item = self
            while (
                pricelist_item.base == "pricelist"
                and pricelist_item.base_pricelist_id.discount_policy == "without_discount"
            ):
                rule_id = pricelist_item.base_pricelist_id._get_product_rule(*args, **kwargs)
                pricelist_item = self.env["product.pricelist.item"].browse(rule_id)
            return pricelist_item._compute_base_price(*args, **kwargs)
        return super()._compute_price_before_discount(*args, **kwargs)
