from odoo import Command
from odoo.tests import HttpCase, tagged

from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


@tagged("post_install", "-at_install")
class TestWebsiteFixedPrice(HttpCase, WebsiteSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._disable_taxes()
        cls._enable_pricelists()
        # The fixed price pricelist must be the one the website gives to visitors.
        cls.env["product.pricelist"].sudo().search([]).action_archive()
        cls.fixed_product = cls.env["product.product"].create(
            {
                "name": "Fixed Price Chair",
                "list_price": 200.0,
                "website_published": True,
            }
        )
        cls.fixed_pricelist = cls._create_pricelist(
            name="Fixed Price Pricelist",
            item_ids=[
                Command.create(
                    {
                        "applied_on": "0_product_variant",
                        "product_id": cls.fixed_product.id,
                        "compute_price": "fixed",
                        "fixed_price": 150.0,
                    }
                )
            ],
        )
        cls.fixed_item = cls.fixed_pricelist.item_ids

    def test_show_discount_on_shop(self):
        Item = self.env["product.pricelist.item"].sudo()
        self.assertFalse(Item._show_discount_on_shop())
        self.assertTrue(self.fixed_item._show_discount_on_shop())

        discount_item = Item.create(
            {
                "pricelist_id": self.fixed_pricelist.id,
                "compute_price": "discount",
                "price_discount": 10,
            }
        )
        self.assertTrue(discount_item._show_discount_on_shop())

        # The cost is never shown to the customer as the original price.
        self.fixed_item.sudo().base = "standard_price"
        self.assertFalse(self.fixed_item._show_discount_on_shop())

    def test_combination_info_fixed_price(self):
        template = self.fixed_product.product_tmpl_id.with_context(website_id=self.website.id)
        with self.mock_request():
            info = template._get_combination_info(product_id=self.fixed_product.id, pricelist=self.fixed_pricelist)
        self.assertTrue(info["has_discounted_price"])
        self.assertEqual(info["price"], 150.0)
        self.assertEqual(info["list_price"], 200.0)

    def test_shop_pages_show_original_price(self):
        # Product page: the list price is shown struck through next to the fixed price.
        res = self.url_open(self.fixed_product.website_url)
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertIn("oe_default_price", html)
        self.assertNotIn("oe_default_price mb-0 h6 d-none", html)
        self.assertIn("200.00", html)
        self.assertIn("150.00", html)

        # Shop grid: the product tile shows the original price.
        res = self.url_open("/shop?search=Fixed+Price+Chair")
        self.assertEqual(res.status_code, 200)
        self.assertIn('aria-label="Original price"', res.text)
        self.assertIn("200.00", res.text)
