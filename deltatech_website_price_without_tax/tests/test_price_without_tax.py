# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon


@tagged("post_install", "-at_install")
class TestPriceWithoutTax(WebsiteSaleCommon):
    def _get_price_without_tax(self, display, price_include, list_price):
        self.website.show_line_subtotals_tax_selection = display
        tax = self.env["account.tax"].create(
            {
                "name": "TVA 21% test",
                "type_tax_use": "sale",
                "amount": 21,
                "price_include_override": "tax_included" if price_include else "tax_excluded",
            }
        )
        product = self._create_product(list_price=list_price, taxes_id=[Command.set(tax.ids)])
        env = self.env(user=self.public_user)
        with MockRequest(env, website=self.website.with_env(env)):
            info = product.product_tmpl_id.with_env(env)._get_combination_info(product_id=product.id)
        return info["list_price_without_tax"]

    def test_tax_included_display_tax_excluded_tax(self):
        price = self._get_price_without_tax("tax_included", False, 100.0)
        self.assertAlmostEqual(price, 100.0, places=2)

    def test_tax_excluded_display_tax_included_tax(self):
        price = self._get_price_without_tax("tax_excluded", True, 121.0)
        self.assertAlmostEqual(price, 100.0, places=2)

    def test_tax_included_display_tax_included_tax(self):
        price = self._get_price_without_tax("tax_included", True, 121.0)
        self.assertAlmostEqual(price, 100.0, places=2)

    def test_tax_excluded_display_tax_excluded_tax(self):
        price = self._get_price_without_tax("tax_excluded", False, 100.0)
        self.assertAlmostEqual(price, 100.0, places=2)
