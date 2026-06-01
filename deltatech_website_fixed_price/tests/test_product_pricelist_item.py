# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductPricelistItem(TransactionCase):
    def test_fixed_price_rule_shows_discount_when_parent_disables_it(self):
        item = self.env["product.pricelist.item"].new({"compute_price": "fixed"})

        with patch(
            "odoo.addons.website_sale.models.product_pricelist_item.ProductPricelistItem._show_discount_on_shop",
            return_value=False,
        ):
            self.assertTrue(item._show_discount_on_shop())

    def test_non_fixed_rule_keeps_parent_false_result(self):
        item = self.env["product.pricelist.item"].new({"compute_price": "formula"})

        with patch(
            "odoo.addons.website_sale.models.product_pricelist_item.ProductPricelistItem._show_discount_on_shop",
            return_value=False,
        ):
            self.assertFalse(item._show_discount_on_shop())

    def test_parent_true_result_is_preserved(self):
        item = self.env["product.pricelist.item"].new({"compute_price": "formula"})

        with patch(
            "odoo.addons.website_sale.models.product_pricelist_item.ProductPricelistItem._show_discount_on_shop",
            return_value=True,
        ):
            self.assertTrue(item._show_discount_on_shop())

    def test_empty_recordset_returns_false(self):
        with patch(
            "odoo.addons.website_sale.models.product_pricelist_item.ProductPricelistItem._show_discount_on_shop",
            return_value=False,
        ):
            self.assertFalse(self.env["product.pricelist.item"].browse()._show_discount_on_shop())
