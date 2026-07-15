from odoo.tests import tagged
from odoo.tools.translate import CodeTranslations

from odoo.addons.website_sale.tests.common import MockRequest
from odoo.addons.website_sale_stock.tests.common import WebsiteSaleStockCommon


@tagged("post_install", "-at_install")
class TestSaleMultipleWebsite(WebsiteSaleStockCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product.write({"qty_multiple": 5.0, "qty_minim": 10.0})
        cls.product.product_tmpl_id.check_min_website = True

    def test_initial_cart_add_is_normalized(self):
        cart = self.empty_cart.with_context(website_id=self.website.id)
        result = cart._cart_add(self.product.id, 7.0)
        line = cart.order_line.filtered(lambda item: item.product_id == self.product)

        self.assertEqual(line.product_uom_qty, 10.0)
        self.assertEqual(result["quantity"], 10.0)
        self.assertEqual(result["added_qty"], 10.0)

    def test_existing_cart_update_returns_saved_quantity(self):
        line = self.cart.order_line.filtered(lambda item: item.product_id == self.product)
        cart = self.cart.with_context(website_id=self.website.id)
        result = cart._cart_update_line_quantity(line.id, 7.0)

        self.assertEqual(line.product_uom_qty, 10.0)
        self.assertEqual(result["quantity"], 10.0)
        self.assertEqual(result["added_qty"], 5.0)

    def test_website_only_rule_is_not_applied_to_backend_order(self):
        backend_order = self.env["sale.order"].create({"partner_id": self.partner.id})
        line = self.env["sale.order.line"].create(
            {
                "order_id": backend_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 7.0,
            }
        )
        self.assertEqual(line.product_uom_qty, 7.0)

    def test_global_rule_is_applied_to_backend_order(self):
        self.product.product_tmpl_id.check_min_website = False
        backend_order = self.env["sale.order"].create({"partner_id": self.partner.id})
        line = self.env["sale.order.line"].create(
            {
                "order_id": backend_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 7.0,
            }
        )
        self.assertEqual(line.product_uom_qty, 10.0)

    def test_direct_create_on_website_order_applies_rule(self):
        line = self.env["sale.order.line"].create(
            {
                "order_id": self.empty_cart.id,
                "product_id": self.product.id,
                "product_uom_qty": 7.0,
            }
        )
        self.assertEqual(line.product_uom_qty, 10.0)

    def test_insufficient_stock_does_not_create_invalid_quantity(self):
        product = self._create_product(
            qty_multiple=5.0,
            qty_minim=10.0,
            check_min_website=True,
        )
        self._add_product_qty_to_wh(product.id, 7.0, self.warehouse.lot_stock_id.id)
        cart = self.empty_cart.with_context(website_id=self.website.id)

        result = cart._cart_add(product.id, 7.0)

        self.assertEqual(result["quantity"], 0.0)
        self.assertFalse(cart.order_line.filtered(lambda line: line.product_id == product))
        self.assertTrue(result["warning"])

    def test_stock_cap_falls_back_to_greatest_valid_quantity(self):
        product = self._create_product(
            qty_multiple=5.0,
            qty_minim=10.0,
            check_min_website=True,
        )
        self._add_product_qty_to_wh(product.id, 12.0, self.warehouse.lot_stock_id.id)
        cart = self.empty_cart.with_context(website_id=self.website.id)
        first_result = cart._cart_add(product.id, 10.0)
        line = cart.order_line.filtered(lambda item: item.product_id == product)

        update_result = cart._cart_update_line_quantity(line.id, 14.0)

        self.assertEqual(first_result["quantity"], 10.0)
        self.assertEqual(update_result["quantity"], 10.0)
        self.assertEqual(line.product_uom_qty, 10.0)
        self.assertTrue(update_result["warning"])

    def test_combination_info_contains_variant_quantity_rules(self):
        with MockRequest(self.env, website=self.website):
            combination_info = self.product.product_tmpl_id._get_combination_info(
                product_id=self.product.id,
                uom_id=self.product.uom_id.id,
            )

        self.assertEqual(combination_info["sale_qty_minimum"], 10.0)
        self.assertEqual(combination_info["sale_qty_multiple"], 5.0)
        self.assertIsInstance(combination_info["sale_qty_precision"], int)

    def test_product_page_qweb_compiles(self):
        self.env["ir.qweb"]._compile("website_sale.product")

    def test_romanian_frontend_translations_are_exported(self):
        messages = CodeTranslations().get_web_translations("deltatech_sale_multiple_website", "ro_RO")["messages"]
        translations = {message["id"]: message["string"] for message in messages}

        self.assertEqual(translations["Minimum quantity"], "Cantitate minimă")
        self.assertEqual(
            translations["The minimum order quantity is %s units."],
            "Cantitatea minimă pentru comandă este de %s unități.",
        )
        self.assertEqual(
            translations["Quantity multiple"],
            "Multiplu de cantitate",
        )
        self.assertEqual(
            translations["Quantity must be a multiple of %s (e.g. %s, %s, %s...)."],
            "Cantitatea trebuie să fie un multiplu de %s (de exemplu %s, %s, %s...).",
        )
