# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.fields import Command
from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon


@tagged("post_install", "-at_install")
class TestPriceWithoutTax(WebsiteSaleCommon):
    def _create_taxed_product(self, price_include, list_price):
        tax = (
            self.env["account.tax"]
            .sudo()
            .create(
                {
                    "name": "TVA 21% test",
                    "type_tax_use": "sale",
                    "amount": 21,
                    "price_include_override": "tax_included" if price_include else "tax_excluded",
                }
            )
        )
        return self._create_product(list_price=list_price, taxes_id=[Command.set(tax.ids)])

    def _get_price_without_tax(self, display, price_include, list_price, **request_kwargs):
        self.website.sudo().show_line_subtotals_tax_selection = display
        product = self._create_taxed_product(price_include, list_price)
        env = self.env(user=self.public_user)
        with MockRequest(env, website=self.website.with_env(env), **request_kwargs) as request:
            # Odoo 20: env.website comes from the context (website_id) set by the request
            info = product.product_tmpl_id.with_env(request.env)._get_combination_info(product_id=product.id)
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

    def test_pricelist_tax_display_overrides_website(self):
        """Odoo 20: the pricelist's price display wins over the website's one."""
        self._enable_pricelists()
        pricelist = self._create_pricelist(name="B2B", tax_display="tax_excluded", selectable=True)
        price = self._get_price_without_tax("tax_included", False, 100.0, website_sale_current_pl=pricelist.id)
        self.assertAlmostEqual(price, 100.0, places=2)


@tagged("post_install", "-at_install")
class TestPriceWithoutTaxPage(HttpCase, WebsiteSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website.sudo().show_line_subtotals_tax_selection = "tax_included"
        tax = (
            cls.env["account.tax"]
            .sudo()
            .create(
                {"name": "TVA 21% page", "type_tax_use": "sale", "amount": 21, "price_include_override": "tax_excluded"}
            )
        )
        cls.taxed_product = cls._create_product(
            name="Product price without tax", list_price=100.0, taxes_id=[Command.set(tax.ids)]
        )
        cls.portal_user = new_test_user(cls.env, login="dt_pwt_portal", groups="base.group_portal", name="Portal Price")

    def _assert_price_without_tax_shown(self):
        response = self.url_open(self.taxed_product.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("oe_price_without_tax", response.text)

    def test_product_page_public_visitor(self):
        self._assert_price_without_tax_shown()

    def test_product_page_portal_user(self):
        self.authenticate(self.portal_user.login, self.portal_user.login)
        self._assert_price_without_tax_shown()
