# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductTemplate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax_10_included = cls.env["account.tax"].create(
            {
                "name": "10% included",
                "amount_type": "percent",
                "amount": 10.0,
                "price_include": True,
                "type_tax_use": "sale",
            }
        )
        cls.tax_20_included = cls.env["account.tax"].create(
            {
                "name": "20% included",
                "amount_type": "percent",
                "amount": 20.0,
                "price_include": True,
                "type_tax_use": "sale",
            }
        )
        cls.product_with_tax = cls.env["product.template"].create(
            {
                "name": "Website taxed product",
                "list_price": 110.0,
                "taxes_id": [(6, 0, cls.tax_10_included.ids)],
            }
        )
        cls.product_without_tax = cls.env["product.template"].create(
            {
                "name": "Website untaxed product",
                "list_price": 99.0,
            }
        )

    def test_combination_info_prefers_taxes_from_base_result(self):
        with patch(
            "odoo.addons.website_sale.models.product_template.ProductTemplate._get_combination_info",
            return_value={"list_price": 120.0, "taxes": self.tax_20_included},
        ):
            combination_info = self.product_with_tax._get_combination_info()

        self.assertAlmostEqual(combination_info["list_price_without_tax"], 100.0)

    def test_combination_info_falls_back_to_product_taxes(self):
        with patch(
            "odoo.addons.website_sale.models.product_template.ProductTemplate._get_combination_info",
            return_value={"list_price": 110.0},
        ):
            combination_info = self.product_with_tax._get_combination_info()

        self.assertAlmostEqual(combination_info["list_price_without_tax"], 100.0)

    def test_combination_info_keeps_price_when_no_taxes_are_available(self):
        with patch(
            "odoo.addons.website_sale.models.product_template.ProductTemplate._get_combination_info",
            return_value={"list_price": 99.0},
        ):
            combination_info = self.product_without_tax._get_combination_info()

        self.assertAlmostEqual(combination_info["list_price_without_tax"], 99.0)
