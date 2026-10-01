from unittest.mock import patch

from odoo import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestDiscountPolicy(SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._enable_discounts()
        cls.pricelist.discount_policy = "without_discount"
        cls.discount = 20

    def _create_discount_rule(self, **values):
        return self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist.id,
                "compute_price": "percentage",
                "percent_price": self.discount,
                **values,
            }
        )

    def test_without_discount_shows_discount(self):
        self._create_discount_rule(product_tmpl_id=self.product.product_tmpl_id.id)
        line = self.env["sale.order.line"].create({"order_id": self.empty_order.id, "product_id": self.product.id})
        self.assertEqual(line.discount, self.discount)

    def test_with_discount_hides_discount(self):
        self.pricelist.discount_policy = "with_discount"
        self._create_discount_rule(product_tmpl_id=self.product.product_tmpl_id.id)
        line = self.env["sale.order.line"].create({"order_id": self.empty_order.id, "product_id": self.product.id})
        self.assertEqual(line.discount, 0.0)

    def test_combo_items_inherit_parent_discount(self):
        """DISCOUNTPOLICY-001: combo item lines keep the discount of the combo line."""
        product_a = self._create_product(name="Burger")
        product_b = self._create_product(name="Fries")
        combos = self.env["product.combo"].create(
            [
                {"name": "Main", "combo_item_ids": [Command.create({"product_id": product_a.id})]},
                {"name": "Side", "combo_item_ids": [Command.create({"product_id": product_b.id})]},
            ]
        )
        combo_product = self._create_product(
            name="Menu", list_price=10.0, type="combo", combo_ids=[Command.set(combos.ids)]
        )
        self._create_discount_rule(product_tmpl_id=combo_product.product_tmpl_id.id)
        order = self.empty_order
        combo_line = self.env["sale.order.line"].create({"order_id": order.id, "product_id": combo_product.id})
        item_lines = self.env["sale.order.line"].create(
            [
                {
                    "order_id": order.id,
                    "product_id": product.id,
                    "combo_item_id": combo.combo_item_ids.id,
                    "linked_line_id": combo_line.id,
                }
                for product, combo in zip(product_a + product_b, combos, strict=True)
            ]
        )
        self.assertEqual(combo_line.discount, self.discount)
        self.assertEqual(item_lines.mapped("discount"), [self.discount, self.discount])
        self.assertAlmostEqual(order.amount_untaxed, order.amount_undiscounted * (100 - self.discount) / 100)

    def test_manual_discount_kept_when_feature_disabled(self):
        """DISCOUNTPOLICY-001: with the discount feature off, a manual discount is not rewritten."""
        self._create_discount_rule(product_tmpl_id=self.product.product_tmpl_id.id)
        line = self.env["sale.order.line"].create({"order_id": self.empty_order.id, "product_id": self.product.id})
        line.discount = 5.0
        item_cls = type(self.env["product.pricelist.item"])
        with patch.object(item_cls, "_is_discount_feature_enabled", return_value=False):
            line.product_uom_qty = 3
            self.assertEqual(line.discount, 5.0)
