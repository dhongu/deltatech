from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_display_price_ignore_combo(self):
        self.ensure_one()
        if self.order_id.pricelist_id and self.order_id.pricelist_id.discount_policy == "with_discount":
            return self._get_pricelist_price()

        if not self.pricelist_item_id or not self.pricelist_item_id._show_discount():
            return self._get_pricelist_price()

        base_price = self._get_pricelist_price_before_discount()
        pricelist_price = self._get_pricelist_price()
        return max(base_price, pricelist_price)

    @api.depends("product_id", "product_uom_id", "product_uom_qty")
    def _compute_discount(self):
        # Mirrors sale.order.line._compute_discount(): only the with_discount
        # policy is added, everything else (feature check, combo items) is kept.
        discount_enabled = self.env["product.pricelist.item"]._is_discount_feature_enabled()
        for line in self:
            if not line.product_id or line.display_type:
                line.discount = 0.0

            if not (line.order_id.pricelist_id and discount_enabled and line.product_uom_id):
                continue

            if line.combo_item_id:
                line.discount = line._get_linked_line().discount
                continue

            line.discount = 0.0

            if line.order_id.pricelist_id.discount_policy == "with_discount":
                continue

            if not line.pricelist_item_id._show_discount():
                continue

            line = line.with_company(line.company_id)
            pricelist_price = line._get_pricelist_price()
            base_price = line._get_pricelist_price_before_discount()

            if base_price != 0:
                discount = (base_price - pricelist_price) / base_price * 100
                if (discount > 0 and base_price > 0) or (discount < 0 and base_price < 0):
                    line.discount = discount
